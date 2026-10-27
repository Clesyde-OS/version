"""Read-only validation of the isolated proposal and frozen live channels."""
import hashlib
import json
import pathlib
import re
import string
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = json.loads((HERE / 'candidate.json').read_text())
COMPONENTS = {'cli', 'dns', 'audio', 'multicast', 'observer'}


class Preparation(unittest.TestCase):
    def test_activation_is_blocked(self):
        self.assertEqual(DATA['status'], 'blocked_pending_explicit_core_supervisor_2026_10_4_acceptance')
        self.assertFalse(DATA['live_channel_changed'])
        self.assertEqual(set(DATA['scope']), COMPONENTS)
        self.assertEqual(set(DATA['targets']), COMPONENTS)

    def test_live_channels_are_unchanged(self):
        for channel, expected in DATA['frozen_channel_sha256'].items():
            with self.subTest(channel=channel):
                self.assertEqual(hashlib.sha256((ROOT / (channel + '.json')).read_bytes()).hexdigest(), expected)

    def test_core_supervisor_and_os_remain_current(self):
        dev = json.loads((ROOT / 'dev.json').read_text())
        self.assertEqual(dev['supervisor'], '2026.10.4')
        self.assertEqual(dev['homeassistant'], {'raspberrypi4-64': '2026.10.4', 'generic-x86-64': '2026.10.4'})
        self.assertEqual(dev['hassos'], {'rpi4-64': '18.1', 'generic-x86-64': '14.1'})
        for name, target in DATA['targets'].items():
            self.assertEqual(dev[name], target['current_dev'])

    def test_image_templates_and_platforms(self):
        for name, target in DATA['targets'].items():
            with self.subTest(component=name):
                template = target['image_template']
                fields = [f for _, f, _, _ in string.Formatter().parse(template) if f]
                self.assertEqual(fields, ['arch'])
                self.assertNotIn('@', template)
                self.assertEqual(set(target['official_reference_images']), {'aarch64', 'amd64'})
                for arch, platform in (('aarch64', 'linux/arm64'), ('amd64', 'linux/amd64')):
                    image = target['official_reference_images'][arch]
                    self.assertEqual(image['platform'], platform)
                    self.assertTrue(image['anonymous_pull'])
                    self.assertEqual(image['version'], target['candidate_version'])
                    self.assertEqual(image['image'], f'ghcr.io/home-assistant/{arch}-hassio-{name}')
                    for key in ('tag_digest', 'manifest_digest', 'config_digest'):
                        self.assertRegex(image[key], r'^sha256:[a-f0-9]{64}$')
                    self.assertTrue(template.format(arch=arch).endswith(f'{arch}-hassio-{name}'))

    def test_distribution_policy(self):
        for name, target in DATA['targets'].items():
            with self.subTest(component=name):
                expected = 'clesyde_rebrand' if name == 'cli' else 'upstream_unchanged'
                owner = 'clesyde-os' if name == 'cli' else 'home-assistant'
                self.assertEqual(target['distribution'], expected)
                self.assertEqual(target['image_template'], f'ghcr.io/{owner}/{{arch}}-hassio-{name}')
                current = tuple(map(int, target['current_dev'].split('.')))
                candidate = tuple(map(int, target['candidate_version'].split('.')))
                self.assertGreater(candidate, current)


if __name__ == '__main__':
    unittest.main(verbosity=2)
