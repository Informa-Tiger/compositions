"""Stage only public web assets and validated generated versions for Pages."""
from pathlib import Path
import json,shutil,html
ROOT=Path(__file__).resolve().parents[1];site=ROOT/'_site';site.mkdir(exist_ok=True)
catalog=[]
for source in sorted(ROOT.glob('compositions/*/versions/*.json')):
 d=json.loads(source.read_text());gen=source.parent.parent/'generated'/d['version']
 for ext in ['json','pdf','musicxml','mid','mp3','mp4']:
  assert (gen/f'composition.{ext}').exists(),f'Missing export: {gen}/composition.{ext}'
 catalog.append({'title':d['title'],'version':d['version'],'label':d['revision']['label'],'source':str((gen/'composition.json').relative_to(ROOT))})
(ROOT/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
for f in ['index.html','catalog.json']:shutil.copy2(ROOT/f,site/f)
shutil.copytree(ROOT/'player',site/'player',dirs_exist_ok=True)
for comp in (ROOT/'compositions').iterdir():
 if not comp.is_dir():continue
 shutil.copytree(comp/'generated',site/'compositions'/comp.name/'generated',dirs_exist_ok=True)
(site/'.nojekyll').write_text('')
print('Staged',len(catalog),'versions for GitHub Pages')
