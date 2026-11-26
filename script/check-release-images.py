#!/usr/bin/env python3
"""Read-only verification of image references advertised to Lyvo devices."""
import json
from pathlib import Path
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


def main():
    channel = sys.argv[1]
    if channel not in CHANNELS:
        raise SystemExit("Unknown channel")
    catalogue = json.loads((Path(__file__).resolve().parents[1] / f"{channel}.json").read_text())
    if catalogue["channel"] != channel:
        raise SystemExit("Channel mismatch")
    failures = []
    for ref, architecture, kind, version in sorted(expected_refs(catalogue)):
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
        except (subprocess.SubprocessError, ValueError, OSError) as err:
            print(f"::error::{ref}: {type(err).__name__}", file=sys.stderr)
            failures.append(ref)
    if failures:
        print("Missing, inaccessible or invalid images:", *failures, sep="\n", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
