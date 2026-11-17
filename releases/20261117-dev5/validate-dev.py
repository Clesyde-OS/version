"""Validate the signed DEV image pair and preserve both client channels and history."""

import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = '03ebf75fac41086285526f592fb0a01cc21dd5eb'
SOURCE = '391e027fb62f296d83dd0c55c5c6b08e1fb9f1e4'
IDENTITY = 'https://github.com/Clesyde-OS/core/.github/workflows/clesyde-upstream-dev.yaml@refs/heads/clesyde/restore-upstream-stores-20261117'
PATCH = '08b0ebb1b4c4227324cff0ae1217d29d8c0ad21e13a8d0ba15d68cc68640098a'
WHEEL = '5e5332b887efb4599ee39f87391eb73fd74c905ddb0ead2427d2ac0e88f28e78'
EXPECTED = {
    'aarch64': ('raspberrypi4-64', 'sha256:eff076101ad9fc52484ad92d709608548c652fdcad660aa42d29cf98dc57278d', 'sha256:4b0a42e76329ca592dc711c697f9155a9714b98f9ed421b32d6877b72e4bebd1'),
    'amd64': ('generic-x86-64', 'sha256:ad2521a8fc51ec997a7a81c3a129668d22957a9eb8c2524419fcba8fce9f9efc', 'sha256:37b7f6415964dd0e5a013fdd013837c0b1f303c3cb8f23d00a3dc0a28dfe3f1f'),
}


def load(path):
    return json.loads((HERE / path).read_text())


def at_base(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)


def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def signed(bundle, payload):
    subprocess.run(['cosign', 'verify-blob', '--certificate-identity', IDENTITY, '--certificate-oidc-issuer', 'https://token.actions.githubusercontent.com', '--bundle', str(HERE / bundle), str(HERE / payload)], check=True)


def main():
    manifest = load('manifest.json')
    assert manifest['channel'] == 'dev'
    assert manifest['catalog_base_commit'] == BASE and manifest['source_commit'] == SOURCE
    assert manifest['core_package'] == '2026.11.1.5'
    assert manifest['frontend_build'] == '4clesyde4' and manifest['frontend_patch_sha256'] == PATCH
    assert manifest['native_run'] == 44059783487 and manifest['native_result'] == 'success'
    assert manifest['beta_stable_changed'] is False and manifest['rebuilds'] == 0
    assert manifest['upstream_general_ci'] == 'failure: disabled Nabu Casa, Clesyde branding expectations, unavailable dependency review and Codecov'
    previous = json.loads(at_base('dev.json'))
    assert previous['homeassistant'] == {'raspberrypi4-64': '2026.11.1.5', 'generic-x86-64': '2026.11.1.4'}
    previous['homeassistant']['generic-x86-64'] = '2026.11.1.5'
    assert json.loads((ROOT / 'dev.json').read_text()) == previous
    for channel in ('beta', 'stable'):
        assert (ROOT / f'{channel}.json').read_bytes() == at_base(f'{channel}.json')
    assert hashlib.sha256((ROOT / 'beta.json').read_bytes()).hexdigest() == '91bd3a9cd1b2a9fbb9caf6d255be004908edba530a32fb9136e40b7200893d6b'
    assert hashlib.sha256((ROOT / 'stable.json').read_bytes()).hexdigest() == '240f3d1bfad16585865157a3680240590ae24efff0f5781c96a5f4ba81cd32b1'
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    allowed = {'dev.json', '.github/workflows/validate-release-20261113.yaml'}
    assert all(name in allowed or name.startswith('releases/20261117-dev5/') for name in changed)

    for arch, (machine, expected_digest, rollback) in EXPECTED.items():
        prefix = 'proofs/' + arch + '/'
        binding = load(prefix + 'archive-binding.json')
        payload = load(prefix + 'image-payload.json')
        image_manifest_bytes = (HERE / (prefix + 'image-manifest.json')).read_bytes()
        # Docker's retained raw JSON may end with one newline; the signed OCI digest does not.
        if digest(image_manifest_bytes) != expected_digest:
            image_manifest_bytes = image_manifest_bytes.rstrip(b'\n')
        assert digest(image_manifest_bytes) == expected_digest
        image_manifest = json.loads(image_manifest_bytes)
        config_bytes = (HERE / (prefix + 'image-config.json')).read_bytes()
        if digest(config_bytes) != image_manifest['config']['digest']:
            config_bytes = config_bytes.rstrip(b'\n')
        assert digest(config_bytes) == image_manifest['config']['digest']
        config = json.loads(config_bytes)
        labels = config['config']['Labels']
        assert labels['io.hass.version'] == '2026.11.1.5' and labels['io.hass.machine'] == machine
        assert labels['io.hass.arch'] == arch and labels['org.opencontainers.image.revision'] == SOURCE
        assert labels['io.clesyde.frontend.sha256'] == WHEEL
        assert binding['reference'] == 'ghcr.io/clesyde-os/' + machine + '-homeassistant@' + expected_digest
        assert binding['source_commit'] == SOURCE and binding['exact_native_tested_archive'] is True
        assert binding['config_digest'] == image_manifest['config']['digest']
        assert payload['critical']['image']['docker-manifest-digest'] == expected_digest
        assert payload['critical']['identity']['docker-reference'] == 'ghcr.io/clesyde-os/' + machine + '-homeassistant'
        signed(prefix + 'image.bundle.json', prefix + 'image-payload.json')
        check = load(prefix + 'independent-verification.json')
        assert check['image_digest'] == expected_digest and check['cosign_signature'] == 'PASS'
        assert check['archive_checksum'] == 'PASS' and check['all_oci_blobs'] == 30
        receipt = load(prefix + 'publication-receipt.json')
        assert receipt['digest'] == expected_digest and receipt['source_commit'] == SOURCE
        assert receipt['signature_verified_before_publication'] and receipt['registry_manifest_readback']
        assert receipt['previous_tag_unchanged'] and receipt['rebuild'] is False
        registry = load('registry-readback.json')
        assert next(row['digest'] for row in registry if row['architecture'] == arch and row['reference'].endswith(':2026.11.1.5')) == expected_digest
        assert next(row['digest'] for row in registry if row['architecture'] == arch and row['reference'].endswith(':2026.11.1.4')) == rollback
        runtime = load(prefix + 'native-runtime.json')
        assert runtime['architecture'] == ('aarch64' if arch == 'aarch64' else 'x86_64')
        assert runtime['protocol_imports'] == 'PASS'
        assert runtime['versions']['homeassistant'] == '2026.11.1'
        assert runtime['versions']['home-assistant-frontend'] == '20261028.5'
        assert runtime['http_default'] == 8123
        assert 'start: frontend served' in (HERE / (prefix + 'startup-summary.txt')).read_text()
        assert 'restart: frontend served' in (HERE / (prefix + 'startup-summary.txt')).read_text()

    provenance = load('frontend/REUSE_PROVENANCE.json')
    assert provenance['wheel_sha256'] == WHEEL and provenance['compiler_inputs']['patch_sha256'] == PATCH
    assert WHEEL in (HERE / 'frontend/SHA256SUMS').read_text()
    signed('frontend/frontend-checksums.bundle.json', 'frontend/SHA256SUMS')
    print(json.dumps({'result': 'PASS', 'channel': 'dev', 'core_package': '2026.11.1.5', 'native_architectures': list(EXPECTED), 'new_image_signatures_verified': 2, 'shared_frontend_signature_verified': True, 'beta_stable_byte_identical': True, 'rollback_preserved': True, 'rebuilds': 0}))


if __name__ == '__main__':
    main()
