"""Stage only public web assets and validated generated versions for Pages."""
from pathlib import Path
import json,shutil,html,hashlib
ROOT=Path(__file__).resolve().parents[1];site=ROOT/'_site';site.mkdir(exist_ok=True)
catalog=[]
for source in sorted(ROOT.glob('compositions/*/versions/*.json')):
 d=json.loads(source.read_text());gen=source.parent.parent/'generated'/d['version']
 for ext in ['json','pdf','musicxml','mid','mp3','mp4']:
  assert (gen/f'composition.{ext}').exists(),f'Missing export: {gen}/composition.{ext}'
 catalog.append({'composition':d['id'],'title':d['title'],'version':d['version'],'label':d['revision']['label'],'source':str((gen/'composition.json').relative_to(ROOT))})
(ROOT/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
for f in ['index.html','catalog.json']:shutil.copy2(ROOT/f,site/f)
shutil.copytree(ROOT/'player',site/'player',dirs_exist_ok=True)
player_page=site/'player/index.html'
revision=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'player').rglob('*')) if p.is_file())).hexdigest()[:12]
for script in (site/'player').glob('*.js'):
 text=script.read_text()
 for module in ['mixer.js','source.js','mp4.js']:text=text.replace(f"'./{module}'",f"'./{module}?v={revision}'")
 script.write_text(text)
player_page.write_text(player_page.read_text().replace('src="player.js"',f'src="player.js?v={revision}"').replace('href="player.css"',f'href="player.css?v={revision}"'))
for comp in (ROOT/'compositions').iterdir():
 if not comp.is_dir():continue
 shutil.copytree(comp/'generated',site/'compositions'/comp.name/'generated',dirs_exist_ok=True)
(site/'.nojekyll').write_text('')
print('Staged',len(catalog),'versions for GitHub Pages')
