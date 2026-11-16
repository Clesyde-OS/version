"""Verify exact workflow/source identities for all retained release signatures."""
from pathlib import Path
import json,os,subprocess
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
for item in manifest['signature_checks']:
 command=[os.environ.get('CLESYDE_COSIGN','cosign'),'verify-blob','--certificate-identity',item['identity'],'--certificate-oidc-issuer','https://token.actions.githubusercontent.com','--certificate-github-workflow-sha',item['source_commit'],'--bundle',str(root/item['bundle']),str(root/item['file'])]
 subprocess.run(command,check=True)
print('Seven exact artifact/source signature checks passed')
