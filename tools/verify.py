"""Validate exports and run the unchanged supplied strict checker."""
from pathlib import Path
import json,sys,subprocess,hashlib
import mido
from music21 import converter
from build import derive,read

source=Path(sys.argv[1]).resolve();out=source.parent;piece=out.parent.parent;d=read(source);p=derive(d)
assert p==d['playback'],'Stale playback cache'
expected=sorted((e['voice'],e['pitch'],e['start'],e['duration']) for e in p['events'])
mid=mido.MidiFile(out/'composition.mid');actual=[]
for v,tr in enumerate(mid.tracks[1:]):
 t=0;on={}
 for m in tr:
  t+=m.time
  if m.type=='note_on' and m.velocity:on[m.note]=t
  elif m.type=='note_off' or (m.type=='note_on' and not m.velocity):
   a=on.pop(m.note);actual.append((v,m.note,a/960,(t-a)/960))
 assert not on
assert sorted(actual)==expected,'MIDI roundtrip differs'
s=converter.parse(out/'composition.musicxml');xml=[]
for v,part in enumerate(s.parts):
 for n in part.stripTies().flatten().notes:xml.append((v,n.pitch.midi,float(n.offset),float(n.quarterLength)))
assert sorted(xml)==expected,'MusicXML roundtrip differs'
mel=read(piece/'sources/melody.json')['events'];tune=[(e['midi'],e['onset_eighths']/2,e['duration_eighths']/2) for e in mel]
actual=[(e['pitch'],e['start']-23,e['duration']) for e in p['events'] if e['voice']==0 and 23<=e['start']<83]
assert actual==tune,'Cantus changed'
tool=piece/'tools/matt';sys.path.insert(0,str(tool));from audit import audit_score
config={'total_ticks':len(d['measures'])*6,'ticks_per_quarter':2,'tonic_pc':7,'tonic_third':4,'allowed_pcs':[0,2,4,6,7,9,11],'ranges':[[60,84],[55,77],[48,69],[36,64]],'max_leaps':[7,7,7,12],'pulse_stride':2,'pulse_offset':0,'tritone_max_wait':2,'require_independence':True,'min_independent_changes':1}
x={'title':d['title'],'config':config,'voices':{v:[] for v in 'satb'}}
for e in p['events']:
 assert e['start']*2==int(e['start']*2) and e['duration']*2==int(e['duration']*2)
 x['voices']['satb'[e['voice']]].append({'start':int(e['start']*2),'dur':int(e['duration']*2),'pitch':e['pitch']})
(out/'matt-input.json').write_text(json.dumps(x,indent=2)+'\n');a=audit_score(x);(out/'matt-audit.json').write_text(json.dumps(a,indent=2)+'\n')
result={'schema_and_timing_valid':True,'playback_cache_exact':True,'midi_roundtrip_exact':True,'musicxml_roundtrip_exact':True,'complete_cantus_exact':True,'notes':len(p['events']),'strict_checks':a['checks'],'strict_findings':len(a['errors']),'scope':'Strict checker results are reported without waiving failures; export integrity is checked separately.'}
if d['version']=='v003':
 for name in ['harmonic_review.py','review_matt_audit.py','create_matt_diagnostic.py']:subprocess.run([sys.executable,str(piece/'tools'/name),str(out)],check=True)
 result['editorial_review']='All strict findings covered by the explicit final-version assessment; not an aesthetic proof.'
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
