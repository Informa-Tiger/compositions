"""Check committed artifacts are current and match their authored version."""
from pathlib import Path
import json,subprocess,sys,hashlib
from build import ROOT,read,derive,digest
for source in sorted(ROOT.glob('compositions/*/versions/*.json')):
 d=read(source);out=source.parent.parent/'generated'/d['version'];snap=read(out/'composition.json');manifest=read(out/'manifest.json')
 assert {k:v for k,v in snap.items() if k!='playback'}==d
 assert derive(d)==snap['playback']
 expected_hash=hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
 assert manifest['sourceDataSha256']==expected_hash
 assert manifest['mediaSourceDataSha256']==expected_hash,'Rebuild audio/PDF for changed source'
 assert manifest['videoSourceDataSha256']==expected_hash,'Rebuild video for changed source'
 for name,sha in manifest['artifacts'].items():assert digest(out/name)==sha,(out,name)
 subprocess.run([sys.executable,str(ROOT/'tools/verify.py'),str(out/'composition.json')],check=True)
 print('Verified source, artifacts, and note roundtrips:',d['version'])
