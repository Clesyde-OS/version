#!/usr/bin/env python3
"""Read-only verification of image references advertised to Lyvo devices."""
import json
from pathlib import Path
import subprocess
import sys

CHANNELS = {"dev", "beta", "stable"}
MACHINES = {"raspberrypi4-64": "aarch64", "generic-x86-64": "amd64"}
PLUGINS = ("supervisor", "cli", "audio", "dns", "observer", "multicast")


def main():
    channel = sys.argv[1]
    if channel not in CHANNELS:
        raise SystemExit("Unknown channel")
    catalogue = json.loads((Path(__file__).resolve().parents[1] / f"{channel}.json").read_text())
    if catalogue["channel"] != channel:
        raise SystemExit("Channel mismatch")
    refs = set()
    for machine, arch in MACHINES.items():
        core = catalogue["images"]["core"].format(machine=machine, arch=arch)
        refs.add(f"{core}:{catalogue['homeassistant'][machine]}")
        refs.add(f"{core}:landingpage")
        for plugin in PLUGINS:
            image = catalogue["images"][plugin].format(machine=machine, arch=arch)
            refs.add(f"{image}:{catalogue[plugin]}")
    failures = []
    for ref in sorted(refs):
        print(f"Checking {ref}", flush=True)
        if subprocess.run(["docker", "manifest", "inspect", ref], stdout=subprocess.DEVNULL).returncode:
            failures.append(ref)
    if failures:
        print("Missing or inaccessible images:", *failures, sep="\n", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
