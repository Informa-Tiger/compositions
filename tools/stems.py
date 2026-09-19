"""Render isolated voices with identical timing and a shared mastering gain."""
from pathlib import Path
import argparse,hashlib,json,math,re,subprocess,tempfile
import mido
ROOT=Path(__file__).resolve().parents[1]
def call(args):return subprocess.run([str(a) for a in args],check=True,capture_output=True,text=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def render(source):
 source=Path(source).resolve();out=source.parent;piece=out.parent.parent;doc=json.loads(source.read_text());cfg=doc['render'];sf=piece/cfg['soundfont'];assert sha(sf)==cfg['soundfontSha256']
 midi=mido.MidiFile(out/'composition-performance.mid');assert len(midi.tracks)==5
 duration=float(call(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',out/'composition.mp3']).stdout)
 with tempfile.TemporaryDirectory() as td:
  tmp=Path(td);waves=[];peaks=[]
  for i,voice in enumerate(doc['voices']):
   one=mido.MidiFile(ticks_per_beat=midi.ticks_per_beat);one.tracks.extend([midi.tracks[0].copy(),midi.tracks[i+1].copy()]);mp=tmp/f'{i}.mid';one.save(mp);wav=tmp/f'{i}.wav';waves.append(wav)
   args=['fluidsynth','-ni','-g',cfg['gain'],'-r',cfg['sampleRate'],'-o','synth.reverb.active=1']
   for k,v in cfg['reverb'].items():args+=['-o',f'synth.reverb.{k}={v}']
   args+=['-o',f'synth.chorus.active={int(cfg["chorus"])}','-F',wav,sf,mp];call(args)
   stats=call(['ffmpeg','-hide_banner','-i',wav,'-af','volumedetect','-f','null','-']).stderr
   peaks.append(float(re.search(r'max_volume: ([\d.-]+) dB',stats)[1]))
  # One gain for all voices preserves their authored balance. Bound the sum of
  # individual peaks, so every subset has headroom, including all voices on.
  max_sum_db=20*math.log10(sum(10**(p/20) for p in peaks));gain=-3-max_sum_db
  files=[]
  for i,wav in enumerate(waves):
   name=f'composition.voice-{i+1}.mp3';target=out/name
   af=f'volume={gain}dB,afade=t=out:st={doc["playback"]["duration"]+cfg["fadeDelaySeconds"]}:d={cfg["fadeSeconds"]},apad,atrim=duration={duration}'
   call(['ffmpeg','-v','error','-y','-i',wav,'-af',af,'-ar',cfg['sampleRate'],'-codec:a','libmp3lame','-b:a',cfg['mp3Bitrate'],target]);files.append({'voice':i,'name':doc['voices'][i]['name'],'file':name,'sha256':sha(target)})
  # Encode directly from PCM, never transcode the downloadable MP3 stems.
  container=out/'composition.voices.mp4'
  args=['ffmpeg','-v','error','-y']
  for wav in waves:args+=['-i',wav]
  for i in range(4):args+=['-map',f'{i}:a:0',f'-filter:a:{i}',af,f'-metadata:s:a:{i}',f'title={doc["voices"][i]["name"]}']
  args+=['-c:a','aac','-b:a','320k','-ar',str(cfg['sampleRate']),'-movflags','+faststart',container];call(args)
  canonical={k:v for k,v in doc.items() if k!='playback'}
  info={'sourceDataSha256':hashlib.sha256(json.dumps(canonical,sort_keys=True).encode()).hexdigest(),'duration':duration,'gainDB':gain,'mastering':'Common gain across all voices; summed peak bounds leave 3 dB headroom. No independent normalization.','voices':files,'container':{'file':container.name,'sha256':sha(container),'codec':'AAC-LC','bitratePerVoice':320000,'trackOrder':[v['name'] for v in doc['voices']]}}
  (out/'composition.stems.json').write_text(json.dumps(info,indent=2)+'\n')
 if (out/'manifest.json').exists():
  p=out/'manifest.json';m=json.loads(p.read_text())
  for f in [container,out/'composition.stems.json',*[out/v['file'] for v in files]]:m['artifacts'][f.name]=sha(f)
  p.write_text(json.dumps(m,indent=2)+'\n')
 print('Rendered four synchronized stems:',doc['version'],flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('source',nargs='?');ap.add_argument('--all',action='store_true');a=ap.parse_args()
 for source in sorted(ROOT.glob('compositions/*/generated/*/composition.json')) if a.all else [a.source]:render(source)
