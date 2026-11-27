#!/usr/bin/env python3
"""Read-only verification of image references advertised to Lyvo devices."""
import json
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


def inspect_refs(refs):
    failures = []
    for ref, architecture, kind, version in sorted(refs):
        print(f"Checking {ref} (linux/{architecture})", flush=True)
        try:
            command = [
                "skopeo", "--override-os", "linux", "--override-arch", architecture,
                "inspect", "--authfile", str(Path.home() / ".docker/config.json"),
                "--config", "docker://" + ref,
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=90)
            config = json.loads(result.stdout)
            if config.get("os") != "linux" or config.get("architecture") != architecture:
                raise ValueError("Unexpected image architecture or operating system")
            labels = config.get("config", {}).get("Labels") or {}
            if kind == "landingpage" and labels.get("io.hass.type") != "landingpage":
                raise ValueError("Recovery image has no landingpage type label")
            if kind in {"core", "supervisor"} and labels.get("io.hass.version") != version:
                raise ValueError("Version label does not match catalogue")
        except subprocess.CalledProcessError as err:
            reason = classify_error(err.stderr)
            try:
                alternative = subprocess.run(
                    ["docker", "manifest", "inspect", ref],
                    capture_output=True, text=True, timeout=45,
                )
                docker_reason = (
                    "manifest readable (config check still failed)"
                    if alternative.returncode == 0
                    else classify_error(alternative.stderr)
                )
            except (subprocess.SubprocessError, OSError):
                docker_reason = "secondary inspection unavailable"
            print(f"::error::{ref}: skopeo={reason}; docker={docker_reason}", file=sys.stderr)
            failures.append(ref)
        except (subprocess.SubprocessError, ValueError, OSError) as err:
            print(f"::error::{ref}: {type(err).__name__}", file=sys.stderr)
            failures.append(ref)
        else:
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
    if len(sys.argv) != 2 or sys.argv[1] not in CHANNELS:
        raise SystemExit("Unknown channel")
    channel = sys.argv[1]
    catalogue = json.loads((Path(__file__).resolve().parents[1] / f"{channel}.json").read_text())
    if catalogue["channel"] != channel:
        raise SystemExit("Channel mismatch")
    print(f"=== {channel.upper()} ===", flush=True)
    return inspect_refs(expected_refs(catalogue))


if __name__ == "__main__":
    raise SystemExit(main())
