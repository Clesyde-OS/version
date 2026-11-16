"""Validate the six approved catalog changes and exact release proof files."""
from pathlib import Path
import hashlib,json,subprocess
root=Path(__file__).resolve().parents[2]
folder=Path(__file__).resolve().parent
manifest=json.loads((folder/'manifest.json').read_text())
dev_only=manifest['stage']=='dev-validation'
assert manifest['channels']==(['dev'] if dev_only else ['dev','beta']) and manifest['stable_publication'] is False
base=manifest['catalog_base_commit']
def original(channel):return subprocess.check_output(['git','show',base+':'+channel+'.json'],cwd=root)
assert hashlib.sha256((root/'stable.json').read_bytes()).hexdigest()==manifest['stable_sha256']
assert (root/'stable.json').read_bytes()==original('stable')
for channel in ['dev','beta']:
 before=json.loads(original(channel));expected=json.loads(original(channel))
 if dev_only and channel=='beta':
  assert (root/'beta.json').read_bytes()==original('beta')
  continue
 expected['supervisor']='2026.11.0.6'
 for machine in ['raspberrypi4-64','generic-x86-64']:expected['homeassistant'][machine]='2026.11.1.4'
 assert json.loads((root/(channel+'.json')).read_bytes())==expected
 assert expected['image']==before['image'] and expected['images']==before['images']
images=manifest['images']
assert {(i['component'],i['architecture']) for i in images}=={(c,a) for c in ['core','supervisor'] for a in ['aarch64','amd64']}
for image in images:
 assert image['package_release']=={'core':'2026.11.1.4','supervisor':'2026.11.0.6'}[image['component']]
 assert image['native_runtime']==image['source_binding']==image['image_signature']=='PASS'
 assert image['reference'].endswith('@'+image['published_digest'])
 assert image['preserve_digests'] is True
 assert image['source_commit']==manifest['source_commits'][image['component']]
 assert image['config_digest'].startswith('sha256:') and len(image['config_digest'])==71
frontend=manifest['frontend']
assert frontend['build']=='3clesyde3' and frontend['wheel_sha256']=='578b94541a29aa49eb3c6c7b4226279962fb3d034309113aa26d007f6edc810a'
assert frontend['original_build']['wheel_sha256']==frontend['wheel_sha256'] and frontend['browser_scenarios']==19
assert all(i['frontend_sha256']==frontend['wheel_sha256'] for i in images if i['component']=='core')
assert manifest['fresh_backup']['isolated_restore_byte_check']=='PASS' and manifest['fresh_backup']['sqlite_integrity']=='ok'
if dev_only:
 assert manifest['dev_acceptance']['result']=='PENDING'
else:
 assert manifest['dev_acceptance']['result']=='PASS' and manifest['dev_acceptance']['exact_images']=='PASS'
 assert manifest['dev_acceptance']['cloud_entry_loaded'] and manifest['dev_acceptance']['external_url_and_tunnel']=='PASS'
 assert manifest['dev_acceptance']['mqtt_roundtrip']=='PASS' and manifest['dev_acceptance']['physical_isolated_cloud_cases']==12
 assert manifest['dev_acceptance']['telemetry_confirmed_batches']>=1
 assert manifest['dev_acceptance']['logger_restored'] is True
 assert manifest['dev_acceptance']['credentials_unchanged']==6
assert manifest['builds_on_promotion']==0 and manifest['historical_tag_overwrites']==0
assert manifest['amd64_physical_acceptance'] is False
for relative,expected in manifest['proof_files_sha256'].items():
 path=folder/relative
 assert path.resolve().is_relative_to(folder.resolve()) and path.is_file()
 assert hashlib.file_digest(path.open('rb'),'sha256').hexdigest()==expected
print(json.dumps({'catalog_changes':'PASS','changed_values':3 if dev_only else 6,'beta_unchanged':dev_only,'stable_unchanged':True,'exact_signed_images':4,'same_frontend_for_both_architectures':True,'dev_acceptance':'PENDING' if dev_only else 'PASS','builds_on_promotion':0}))
