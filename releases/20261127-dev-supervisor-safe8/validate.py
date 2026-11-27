"""Validate the exact supervisor-only DEV promotion; preserve earlier releases."""
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "1f0768ea032f1e4f61b9f1c93b55851c443e08be"
MANIFEST = json.loads((HERE / "manifest.json").read_text())
EXPECTED = {
    "aarch64": "sha256:b53393d310fb437ca669e6d2c8b265d64d3128e22e1fbe3285aac4a977c59cdd",
    "amd64": "sha256:2b7cf1501853c59d403cf9bed87e5dba51595cd8b29ddc85d657deeee56f4e9e",
}


def original(path):
    return subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)


assert MANIFEST["stage"] == "dev-supervisor-only"
assert MANIFEST["base_commit"] == BASE
assert MANIFEST["previous_release_commit"] == "c226ffbc4b5652ac81c8278dc84b6d5bb3f835f4"
assert MANIFEST["previous_supervisor"] == "2026.11.0.6"
assert MANIFEST["supervisor"] == "2026.11.0.8"
assert MANIFEST["source_commit"] == "d28a86d1455b8b97359d434085d4618b40d3f79b"
assert MANIFEST["native_build_run"] == 45975834977
assert MANIFEST["publication_run"] == 45980061215
assert MANIFEST["device_readback_run"] == 45980458812
assert MANIFEST["images"] == EXPECTED
assert MANIFEST["physical_dev_acceptance"] == "pending"
assert MANIFEST["beta_promotion_authorized"] is False
assert MANIFEST["stable_changed"] is False

before = original("dev.json")
assert before.count(b'"supervisor": "2026.11.0.6"') == 1
expected = before.replace(b'"supervisor": "2026.11.0.6"', b'"supervisor": "2026.11.0.8"')
assert (ROOT / "dev.json").read_bytes() == expected
for channel in ("beta", "stable"):
    assert (ROOT / f"{channel}.json").read_bytes() == original(f"{channel}.json")
changes = set(subprocess.check_output(["git", "diff", "--name-only", BASE, "HEAD"], cwd=ROOT, text=True).splitlines())
assert changes == {
    "dev.json",
    ".github/workflows/validate-release-20261113.yaml",
    "releases/20261127-dev-supervisor-safe8/manifest.json",
    "releases/20261127-dev-supervisor-safe8/validate.py",
}, changes
print("PASS: DEV Supervisor only; BETA/STABLE and historical proofs unchanged; device acceptance pending")
