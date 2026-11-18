# Phase 2 preparation, 27 October 2026

This directory preserves the historical preparation from 27 October 2026.
No served channel manifest changes are included. Core/Supervisor releases
accepted later are not required to match this historical baseline. Plugin
activation still requires a separate explicit decision and current field review.
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
`candidate.json` and `snapshots/*.json` are immutable historical evidence.
Their versions and SHA256 values are checked against the original channel
bytes, not against today's catalog. The historical blocked status in
`candidate.json` remains a record, not a claim about current Core/Supervisor
acceptance or permission to activate plugins.

The read-only validation command requires the exact current PR base commit:

```sh
python3 preparation/phase2-20261027/validate.py --base-ref <40-character-base-SHA>
```

CI fetches full history and uses the first parent of the checked-out test
merge as the actual base, after verifying that its second parent is the
expected PR head. The event's cached base SHA can be older than that merge.
It verifies that the PR and worktree change none of dev.json, beta.json or
stable.json. It reads current plugin selections from that base with git show;
new accepted Core/Supervisor versions are allowed. Image templates, native
platforms, original distribution policy and frozen digests remain checked.

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
