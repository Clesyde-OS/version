"""Validate the exact DEV ARM64-only store fix; preserve BETA/STABLE and immutable history."""

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
MANIFEST = json.loads((FOLDER / "manifest.json").read_text())
RECEIPT = json.loads((FOLDER / "publication-receipt-aarch64.json").read_text())
SOURCE = "391e027fb62f296d83dd0c55c5c6b08e1fb9f1e4"
PATCH = "08b0ebb1b4c4227324cff0ae1217d29d8c0ad21e13a8d0ba15d68cc68640098a"
ARM_DIGEST = "sha256:eff076101ad9fc52484ad92d709608548c652fdcad660aa42d29cf98dc57278d"
ROLLBACK_DIGEST = "sha256:4b0a42e76329ca592dc711c697f9155a9714b98f9ed421b32d6877b72e4bebd1"
BASE = "8a2b080724dc4522096ab399896c219146be7fc3"


def at_base(file: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE}:{file}"], cwd=ROOT)


def verify() -> None:
    assert MANIFEST["stage"] == "dev-only-physical-box-test"
    assert MANIFEST["catalog_base_commit"] == BASE
    assert MANIFEST["channel"] == "dev" and MANIFEST["machine"] == "raspberrypi4-64"
    assert MANIFEST["dev_box_acceptance"] == "PENDING"
    assert MANIFEST["backup_before_device_update"] == "REQUIRED"
    assert MANIFEST["core_package_release"] == "2026.11.1.5"
    assert MANIFEST["frontend_build"] == "4clesyde4"
    assert MANIFEST["frontend_patch_sha256"] == PATCH
    assert MANIFEST["source_commit"] == SOURCE
    assert MANIFEST["native_ci_run"] == 44059783487
    assert MANIFEST["native_ci_status"] == "success"
    assert MANIFEST["publish_run"] == 44067426477
    assert MANIFEST["publish_run_status"] == "success"
    assert MANIFEST["published_tag"] == "2026.11.1.5"
    assert MANIFEST["published_reference"] == (
        "ghcr.io/clesyde-os/raspberrypi4-64-homeassistant@" + ARM_DIGEST
    )
    assert MANIFEST["rollback_digest"] == ROLLBACK_DIGEST
    assert MANIFEST["beta_unchanged"] and MANIFEST["stable_unchanged"]
    assert MANIFEST["amd64_published"] is False
    assert MANIFEST["amd64_catalog_remains"] == "2026.11.1.4"
    assert MANIFEST["supervisor_remains"] == "2026.11.0.6"
    assert MANIFEST["image_rebuild_for_promotion"] is False

    # No change is permitted in either client-facing channel or the historical
    # release evidence. The only catalog change is the DEV ARM64 Core tag.
    for channel in ("beta", "stable"):
        assert (ROOT / f"{channel}.json").read_bytes() == at_base(f"{channel}.json")
    previous = json.loads(at_base("dev.json"))
    current = json.loads((ROOT / "dev.json").read_bytes())
    assert previous["homeassistant"]["raspberrypi4-64"] == "2026.11.1.4"
    assert previous["homeassistant"]["generic-x86-64"] == "2026.11.1.4"
    assert previous["supervisor"] == "2026.11.0.6"
    previous["homeassistant"]["raspberrypi4-64"] = "2026.11.1.5"
    assert current == previous
    assert current["homeassistant"]["generic-x86-64"] == "2026.11.1.4"
    assert current["supervisor"] == "2026.11.0.6"

    original = json.loads(
        (ROOT / "releases/20261113/proofs/core-aarch64-archive-binding.json").read_text()
    )
    assert original["reference"].endswith("@" + ROLLBACK_DIGEST)
    assert original["tag"] == "2026.11.1.4"
    assert hashlib.sha256((ROOT / "stable.json").read_bytes()).hexdigest() == (
        "240f3d1bfad16585865157a3680240590ae24efff0f5781c96a5f4ba81cd32b1"
    )

    # These exact observations were recorded by the successful publisher run
    # and remain linked to its downloadable GitHub Actions receipt.
    assert RECEIPT["result"] == "published-from-digest-verified-staging"
    assert RECEIPT["candidate"] == (
        "ghcr.io/clesyde-os/raspberrypi4-64-homeassistant:2026.11.1.5"
    )
    assert RECEIPT["digest"] == ARM_DIGEST
    assert RECEIPT["source_commit"] == SOURCE
    assert RECEIPT["native_ci_run"] == 44059783487
    assert RECEIPT["frontend_patch_sha256"] == PATCH
    assert RECEIPT["signature_verified_before_publication"] is True
    assert RECEIPT["registry_manifest_readback"] is True
    assert RECEIPT["previous_tag_unchanged"] is True
    assert RECEIPT["rebuild"] is False
    assert RECEIPT["catalog_changed"] is False
    assert RECEIPT["beta_or_stable_changed"] is False
    assert RECEIPT["dev_box_tested"] is False

    print(
        json.dumps(
            {
                "result": "PASS",
                "channel": "dev",
                "changed_machine": "raspberrypi4-64",
                "published_manifest": ARM_DIGEST,
                "native_run": 44059783487,
                "publish_run": 44067426477,
                "amd64_unchanged": True,
                "beta_unchanged": True,
                "stable_unchanged": True,
                "historical_signatures": "validated separately",
                "dev_box_tested": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    verify()
