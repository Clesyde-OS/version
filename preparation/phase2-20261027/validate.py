"""Validate the historical proposal and the current PR without channel activation."""

import argparse
import hashlib
import json
import pathlib
import re
import string
import subprocess
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = json.loads((HERE / "candidate.json").read_text())
COMPONENTS = {"cli", "dns", "audio", "multicast", "observer"}
CHANNELS = ("dev", "beta", "stable")

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--base-ref", required=True)
options, unittest_args = parser.parse_known_args()
if not re.fullmatch(r"[a-f0-9]{40}", options.base_ref):
    parser.error("--base-ref must be the full pull-request base commit SHA")
BASE_REF = options.base_ref


def git(*args):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        check=True,
    ).stdout


class Preparation(unittest.TestCase):
    def test_activation_is_blocked(self):
        self.assertEqual(
            DATA["status"],
            "blocked_pending_explicit_core_supervisor_2026_10_4_acceptance",
        )
        self.assertFalse(DATA["live_channel_changed"])
        self.assertEqual(set(DATA["scope"]), COMPONENTS)
        self.assertEqual(set(DATA["targets"]), COMPONENTS)

    def test_historical_channels_are_unchanged(self):
        self.assertEqual(set(DATA["frozen_channel_sha256"]), set(CHANNELS))
        for channel, expected in DATA["frozen_channel_sha256"].items():
            with self.subTest(channel=channel):
                snapshot = HERE / "snapshots" / (channel + ".json")
                self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), expected)

    def test_historical_core_supervisor_and_os_baseline(self):
        dev = json.loads((HERE / "snapshots" / "dev.json").read_text())
        self.assertEqual(dev["supervisor"], "2026.10.4")
        self.assertEqual(
            dev["homeassistant"],
            {"raspberrypi4-64": "2026.10.4", "generic-x86-64": "2026.10.4"},
        )
        self.assertEqual(dev["hassos"], {"rpi4-64": "18.1", "generic-x86-64": "14.1"})
        for name, target in DATA["targets"].items():
            self.assertEqual(dev[name], target["current_dev"])

    def test_served_channels_are_not_modified_by_this_pr(self):
        files = [channel + ".json" for channel in CHANNELS]
        self.assertEqual(
            git("diff", "--name-only", BASE_REF + "...HEAD", "--", *files),
            b"",
            "The PR changes a served channel manifest",
        )
        self.assertEqual(
            git("diff", "--name-only", "HEAD", "--", *files),
            b"",
            "The worktree changes a served channel manifest",
        )
        for channel in CHANNELS:
            with self.subTest(channel=channel):
                current = json.loads(git("show", f"{BASE_REF}:{channel}.json"))
                self.assertEqual(current["channel"], channel)
                self.assertIn("homeassistant", current)
                self.assertIn("supervisor", current)
                self.assertIn("hassos", current)
                if channel == "dev":
                    for name, target in DATA["targets"].items():
                        self.assertEqual(current[name], target["current_dev"])

    def test_image_templates_and_platforms(self):
        for name, target in DATA["targets"].items():
            with self.subTest(component=name):
                template = target["image_template"]
                fields = [field for _, field, _, _ in string.Formatter().parse(template) if field]
                self.assertEqual(fields, ["arch"])
                self.assertNotIn("@", template)
                self.assertEqual(set(target["official_reference_images"]), {"aarch64", "amd64"})
                for arch, platform in (("aarch64", "linux/arm64"), ("amd64", "linux/amd64")):
                    image = target["official_reference_images"][arch]
                    self.assertEqual(image["platform"], platform)
                    self.assertTrue(image["anonymous_pull"])
                    self.assertEqual(image["version"], target["candidate_version"])
                    self.assertEqual(image["image"], f"ghcr.io/home-assistant/{arch}-hassio-{name}")
                    for key in ("tag_digest", "manifest_digest", "config_digest"):
                        self.assertRegex(image[key], r"^sha256:[a-f0-9]{64}$")
                    self.assertTrue(template.format(arch=arch).endswith(f"{arch}-hassio-{name}"))

    def test_distribution_policy(self):
        for name, target in DATA["targets"].items():
            with self.subTest(component=name):
                expected = "clesyde_rebrand" if name == "cli" else "upstream_unchanged"
                owner = "clesyde-os" if name == "cli" else "home-assistant"
                self.assertEqual(target["distribution"], expected)
                self.assertEqual(target["image_template"], f"ghcr.io/{owner}/{{arch}}-hassio-{name}")
                current = tuple(map(int, target["current_dev"].split(".")))
                candidate = tuple(map(int, target["candidate_version"].split(".")))
                self.assertGreater(candidate, current)


if __name__ == "__main__":
    unittest.main(argv=[__file__, *unittest_args], verbosity=2)
