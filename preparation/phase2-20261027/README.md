# Phase 2 preparation, 27 October 2026

This directory is preparation only. No served channel manifest changes.
The user must explicitly accept the ongoing Core/Supervisor 2026.10.4 DEV
field validation before any of these components is announced on DEV.
No BETA/STABLE, installed app, field device, AWS or OS image changes are included.

| Component | Existing DEV | Official STABLE candidate | Distribution |
| --- | --- | --- | --- |
| CLI | 2024.05.0 | 2026.10.1, binary 5.6.0 | Clesyde CLI, separate native candidate |
| DNS | 2024.04.0 | 2026.10.0 | Official image, unchanged |
| Audio | 2023.12.0 | 2026.10.0 | Official image, unchanged |
| Multicast | 2024.03.0 | 2026.10.0 | Official image, unchanged |
| Observer | 2023.06.0 | 2026.08.0 | Official image, unchanged |

References supplied at handoff were superseded by official releases on
26 October. candidate.json records both OCI index and platform manifest digests.
The four unchanged plugins are neither rebuilt nor copied into Clesyde GHCR.
The CLI official image digest is a base reference, not the Clesyde candidate
digest. Its final native candidate receipts live in the private CLI repository.

Supervisor consumes `images` (plural); legacy `image` is not its current input.
Templates require `{arch}` and yield `aarch64` or `amd64`, not ARM machine names.
Core still uses `{machine}`. Supervisor separately supplies the version tag:
inserting `@sha256` into its image template is not a supported digest lock.
Recheck official tags against the frozen digests immediately before future
activation and verify the downloaded platform image on each target.

Candidate JSON is not a channel manifest and must never be served as one.
`python3 preparation/phase2-20261027/validate.py` is read-only. CI checks
templates, architectures, provenance, and unchanged DEV/BETA/STABLE snapshots.

Future activation, only after explicit user acceptance:

1. Recheck current DEV and Core/Supervisor image digests against the recorded
   phase-1 baseline. Review CI receipts and verify CLI package read access on
   each DEV target. Never rebuild a tested candidate to promote it.
2. Publish/copy the already-tested CLI OCI manifests to unused private candidate
   tags, preserving their exact digests, and recheck both native platforms.
   Existing CLI packages are currently linked to ghcr-migration; a CLI workflow
   token's write access is not established by owner read access.
3. Prepare a NEW DEV-only activation PR for one component at a time, including
   its version and matching `images` entry together. Keep all Core/Supervisor,
   OS, legacy `image`, BETA and STABLE values intact. Use a unique Clesyde CLI
   package path/tag if needed to prevent a same-version upstream collision.
4. Suggested order: CLI, Observer, DNS, Multicast, Audio, with acceptance between
   steps. Changing the DEV feed can trigger automatic plugin updates on every
   subscribing DEV machine; a UI notification is not an installation gate.
5. On each real target, validate cold pull, actual version/image/platform,
   restart, logs, API, retained options and component-specific functionality.
   Check DNS local/forwarding/IPv6, audio devices/sockets, Observer HTTP 4357,
   multicast discovery and CLI host console. A container test proves no radio,
   LAN/mDNS, sound device, CM4 eMMC/NVMe or generic x86-64 field behavior.
6. Before each step, preserve configuration, previous image/digest and a tested
   recovery route. Supervisor cleans up old images and does not automatically
   roll back a failed plugin update. Reverting a feed alone does not downgrade
   an installed newer version. Image-source changes also matter during boot:
   load/check_image may request the OLD installed version at the NEW registry.
   Revalidate old tag availability, credentials and the recovery procedure.
7. OS rpi4-64 remains 18.1; generic-x86-64 remains 14.1 in DEV. OS 18.3 stays
   blocked by the missing approved RAUC signing pair and trust/migration checks.
   No OS rebuild is required to prepare these container updates. Field
   compatibility with each installed OS/Docker/kernel combination is pending.

The live beta.json and stable.json remain byte-for-byte unchanged. Later channel
promotion requires separate explicit approval and reuses the exact artifacts.
