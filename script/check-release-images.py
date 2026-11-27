#!/usr/bin/env python3
"""Read-only verification of image references advertised to Lyvo devices."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

CHANNELS = {"dev", "beta", "stable"}
MACHINES = {"raspberrypi4-64": ("aarch64", "arm64"), "generic-x86-64": ("amd64", "amd64")}
PLUGINS = ("supervisor", "cli", "audio", "dns", "observer", "multicast")


def expected_refs(catalogue):
    refs = set()
    for machine, (arch, platform_arch) in MACHINES.items():
        core = catalogue["images"]["core"].format(machine=machine, arch=arch)
        refs.add((f"{core}:{catalogue['homeassistant'][machine]}", platform_arch, "core", catalogue["homeassistant"][machine]))
        refs.add((f"{core}:landingpage", platform_arch, "landingpage", None))
        for plugin in PLUGINS:
            image = catalogue["images"][plugin].format(machine=machine, arch=arch)
            refs.add((f"{image}:{catalogue[plugin]}", platform_arch, plugin, catalogue[plugin]))
    return refs


def classify_error(stderr):
    """Report only fixed categories; never print raw registry error output."""
    msg = (stderr or "").lower()
    for patterns, reason in (
        (("unauthorized", "authentication required", "401 unauthorized", "invalid username/password"), "authentication rejected"),
        (("denied", "forbidden", "insufficient_scope", "403 forbidden"), "registry access denied"),
        (("manifest unknown", "manifest_unknown", "no such manifest", "name unknown"), "manifest or repository not found"),
        (("blob unknown", "blob_unknown"), "image blob not found"),
        (("no image found", "no matching manifest", "no image for"), "platform not available"),
        (("unsupported media type", "unsupported manifest", "unrecognized manifest"), "unsupported manifest format"),
        (("too many requests", "rate limit"), "registry rate limit"),
        (("certificate", "tls"), "TLS/certificate error"),
        (("timeout", "timed out", "no such host", "could not resolve", "connection refused", "network is unreachable"), "network or DNS failure"),
        (("404 not found",), "HTTP 404"),
    ):
        if any(pattern in msg for pattern in patterns):
            return reason
    return "unclassified registry/client failure"


def pull_config(ref, architecture):
    """Fallback to an actual device-style pull on the disposable CI runner."""
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("LYVO_PREFLIGHT_DOCKER_PULL") != "1":
        raise ValueError("Docker pull fallback is enabled only on the CI runner")
    existing = subprocess.run(
        ["docker", "image", "inspect", ref], capture_output=True, timeout=30
    ).returncode == 0
    try:
        subprocess.run(
            ["docker", "pull", "--quiet", "--platform", f"linux/{architecture}", ref],
            capture_output=True, text=True, check=True, timeout=420,
        )
        result = subprocess.run(
            ["docker", "image", "inspect", ref],
            capture_output=True, text=True, check=True, timeout=30,
        )
        image = json.loads(result.stdout)[0]
        return {
            "os": image.get("Os"),
            "architecture": image.get("Architecture"),
            "config": image.get("Config") or {},
        }
    finally:
        if not existing:
            try:
                subprocess.run(
                    ["docker", "image", "rm", ref],
                    capture_output=True, timeout=60,
                )
            except (subprocess.SubprocessError, OSError):
                pass


def check_config(config, architecture, kind, version):
    if config.get("os") != "linux" or config.get("architecture") != architecture:
        raise ValueError("Unexpected image architecture or operating system")
    labels = config.get("config", {}).get("Labels") or {}
    if kind == "landingpage" and labels.get("io.hass.type") != "landingpage":
        raise ValueError("Recovery image has no landingpage type label")
    if kind in {"core", "supervisor"} and labels.get("io.hass.version") != version:
        raise ValueError("Version label does not match catalogue")


def inspect_refs(refs, cache=None):
    if cache is None:
        cache = {}
    failures = []
    for item in sorted(refs):
        ref, architecture, kind, version = item
        print(f"Checking {ref} (linux/{architecture})", flush=True)
        if item in cache:
            if cache[item]:
                print(f"PASS {ref} (already verified)", flush=True)
            else:
                print(f"::error::{ref}: previously failed in this run", file=sys.stderr)
                failures.append(ref)
            continue
        try:
            command = [
                "skopeo", "--override-os", "linux", "--override-arch", architecture,
                "inspect", "--authfile", str(Path.home() / ".docker/config.json"),
                "--config", "docker://" + ref,
            ]
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=90)
                config = json.loads(result.stdout)
            except subprocess.CalledProcessError as err:
                reason = classify_error(err.stderr)
                alternative = subprocess.run(
                    ["docker", "manifest", "inspect", ref],
                    capture_output=True, text=True, timeout=45,
                )
                if alternative.returncode:
                    print(f"::error::{ref}: skopeo={reason}; docker={classify_error(alternative.stderr)}", file=sys.stderr)
                    failures.append(ref)
                    cache[item] = False
                    continue
                print(f"Manifest readable; verifying complete image with Docker: {ref}", flush=True)
                config = pull_config(ref, architecture)
            check_config(config, architecture, kind, version)
        except subprocess.CalledProcessError as err:
            print(f"::error::{ref}: Docker verification failed: {classify_error(err.stderr)}", file=sys.stderr)
            failures.append(ref)
            cache[item] = False
        except (subprocess.SubprocessError, ValueError, OSError) as err:
            detail = str(err) if type(err) is ValueError else type(err).__name__
            print(f"::error::{ref}: {detail}", file=sys.stderr)
            failures.append(ref)
            cache[item] = False
        else:
            cache[item] = True
            print(f"PASS {ref}", flush=True)
    if failures:
        print("Missing, inaccessible or invalid images:", *failures, sep="\n", file=sys.stderr)
        return 1
    return 0


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--candidate":
        machine, digest = sys.argv[2:]
        if machine not in MACHINES or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
            raise SystemExit("Invalid recovery candidate")
        return inspect_refs({
            (f"ghcr.io/clesyde-os/{machine}-homeassistant@{digest}",
             MACHINES[machine][1], "landingpage", None)
        })
    channels = sys.argv[1:]
    if not channels or any(channel not in CHANNELS for channel in channels):
        raise SystemExit("Unknown channel")
    cache = {}
    failed = 0
    for channel in channels:
        catalogue = json.loads((Path(__file__).resolve().parents[1] / f"{channel}.json").read_text())
        if catalogue["channel"] != channel:
            raise SystemExit("Channel mismatch")
        print(f"=== {channel.upper()} ===", flush=True)
        failed |= inspect_refs(expected_refs(catalogue), cache)
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
