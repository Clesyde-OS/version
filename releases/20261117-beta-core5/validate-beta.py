"""Promote only the exact accepted DEV Core pair to BETA; freeze DEV/STABLE/history."""

import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEV_PROOFS = ROOT / 'releases/20261117-dev5'
BASE = 'a33c4231cc45e7009349d21301c935d35ee9c3d2'
SOURCE = '391e027fb62f296d83dd0c55c5c6b08e1fb9f1e4'
IDENTITY = 'https://github.com/Clesyde-OS/core/.github/workflows/clesyde-upstream-dev.yaml@refs/heads/clesyde/restore-upstream-stores-20261117'
EXPECTED = {
    'aarch64': ('raspberrypi4-64', 'sha256:eff076101ad9fc52484ad92d709608548c652fdcad660aa42d29cf98dc57278d', 'sha256:4b0a42e76329ca592dc711c697f9155a9714b98f9ed421b32d6877b72e4bebd1'),
    'amd64': ('generic-x86-64', 'sha256:ad2521a8fc51ec997a7a81c3a129668d22957a9eb8c2524419fcba8fce9f9efc', 'sha256:37b7f6415964dd0e5a013fdd013837c0b1f303c3cb8f23d00a3dc0a28dfe3f1f'),
}


def load(path):
    return json.loads(path.read_text())


def original(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)


def signed(bundle, payload):
    subprocess.run(['cosign', 'verify-blob', '--certificate-identity', IDENTITY, '--certificate-oidc-issuer', 'https://token.actions.githubusercontent.com', '--bundle', str(bundle), str(payload)], check=True)


def main():
    manifest = load(HERE / 'manifest.json')
    assert manifest['stage'] == 'beta-promotion-exact-accepted-dev'
    assert manifest['base_commit'] == BASE and manifest['source_commit'] == SOURCE
    assert manifest['core_package'] == '2026.11.1.5' and manifest['frontend_build'] == '4clesyde4'
    assert manifest['native_run'] == 44059783487 and manifest['dev_catalog_pr'] == 12
    assert manifest['rebuilds'] == 0 and manifest['registry_mutation'] is False
    assert manifest['stable_changed'] is False
    approval = load(HERE / 'dev-acceptance.json')
    assert approval['user_accepted_dev'] and approval['explicit_beta_promotion_requested']
    assert approval['dev_installed_core'] == '2026.11.1.5'
    assert approval['signed_frontend_files_match_served'] and approval['store_order'][0] == 'Clesyde Apps'
    assert approval['applications_unchanged'] == 16
    for channel in ('dev', 'stable'):
        assert (ROOT / (channel + '.json')).read_bytes() == original(channel + '.json')
    beta = json.loads(original('beta.json'))
    assert beta['homeassistant'] == {'raspberrypi4-64': '2026.11.1.4', 'generic-x86-64': '2026.11.1.4'}
    beta['homeassistant'] = {'raspberrypi4-64': '2026.11.1.5', 'generic-x86-64': '2026.11.1.5'}
    assert load(ROOT / 'beta.json') == beta
    assert beta['supervisor'] == '2026.11.0.6'
    assert hashlib.sha256((ROOT / 'stable.json').read_bytes()).hexdigest() == '240f3d1bfad16585865157a3680240590ae24efff0f5781c96a5f4ba81cd32b1'
    changes = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    assert all(p in ('beta.json', '.github/workflows/validate-release-20261113.yaml') or p.startswith('releases/20261117-beta-core5/') for p in changes)
    registry = load(HERE / 'same-signed-images.json')
    assert registry['result'] == 'PASS' and registry['source_commit'] == SOURCE
    assert registry['same_images_as_accepted_dev'] and registry['rollback_preserved']
    assert registry['rebuilds'] == 0 and registry['registry_mutation'] is False
    for arch, (machine, digest, rollback) in EXPECTED.items():
        folder = DEV_PROOFS / 'proofs' / arch
        payload = load(folder / 'image-payload.json')
        assert payload['critical']['image']['docker-manifest-digest'] == digest
        assert payload['critical']['identity']['docker-reference'] == 'ghcr.io/clesyde-os/' + machine + '-homeassistant'
        signed(folder / 'image.bundle.json', folder / 'image-payload.json')
        for tag, expected in [('2026.11.1.5', digest), ('2026.11.1.4', rollback)]:
            reference = 'ghcr.io/clesyde-os/' + machine + '-homeassistant:' + tag
            assert next(row['digest'] for row in registry['registry_readback'] if row['reference'] == reference) == expected
    signed(DEV_PROOFS / 'frontend/frontend-checksums.bundle.json', DEV_PROOFS / 'frontend/SHA256SUMS')
    print(json.dumps({'result': 'PASS', 'promoted_channel': 'beta', 'same_signed_images_as_dev': True, 'image_signatures_verified': 2, 'shared_frontend_signature_verified': True, 'dev_unchanged': True, 'stable_byte_identical': True, 'rollback_preserved': True, 'rebuilds': 0}))


if __name__ == '__main__':
    main()
