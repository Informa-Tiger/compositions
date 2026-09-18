import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];OUT=Path(sys.argv[1]).resolve();sys.path.insert(0,str(R/'tools/matt'));from audit import reconstruct_frames
s=json.loads((OUT/'matt-input.json').read_text());fs=reconstruct_frames(s)
CHORDS={'G':{7,11,2},'Em':{4,7,11},'Am':{9,0,4},'C':{0,4,7},'D':{2,6,9},'D7':{2,6,9,0},'Bm':{11,2,6},'A7':{9,1,4,7},'B7':{11,3,6,9},'Am7':{9,0,4,7},'Em7':{4,7,11,2}}
PLAN=['G G G','G G G','G G C','D Am D','G Em Am','G G D7','G Am C','D D D7','G C Am','G G D7','G Bm D','G G G','Em Em Am','G D C','G G D','G C D','G Bm D','D Am D7','G C Em','Am A7 D7','G Em Am','G G D7','G G D','G G D7','G Em D7','G Em G','Bm Em D7','G G Em','Em Em B7','Em Am Am7','Am Am B7','Em G C','C Am D','G Am7 D','C Em7 A7','D C D7','Em C D','G D D7','G Em D','G G G','Em Em Am','G D D7','G Em D','G G D','C C C','D D D7','G G C','G G G']
h=[q for bar in PLAN for p in bar.split() for q in [p,p]];h[103]='C';h[135]='Bm'
# This is a declared analytical reading, not inferred harmony or a style proof.
# In m.30 the soprano G-F#-E is a passing chain over Am/C.
h[178]=h[179]='Am'
assert all(sum(bool(p) for p in f)<=1 for f in fs[:12])
rows=[]
for v,ns in s['voices'].items():
 for j,n in enumerate(ns):
  if n['start']<12:continue # opening monophonic subject
  bad=[t for t in range(n['start'],n['start']+n['dur']) if n['pitch']%12 not in CHORDS[h[t]]]
  if not bad:continue
  prev,nxt=ns[j-1],ns[j+1]
  assert prev['start']+prev['dur']==n['start'] and n['start']+n['dur']==nxt['start']
  p,q,z=prev['pitch'],n['pitch'],nxt['pitch'];a,b=q-p,z-q
  step=lambda n:abs(n) in (1,2)
  ident=(v,n['start']);kind=None
  if ident in [('s',80),('s',268)]:
   assert bad[0]>n['start'] and q%12 in CHORDS[h[bad[0]-1]] and step(b) and b<0
   kind='Prepared suspension, 9–8' if ident==('s',80) else 'Prepared cadential 4–3 suspension'
  elif ident==('t',270):
   assert (p,q,z)==(60,59,57) and h[n['start']]=='D'
   kind='Cadential 6–5, paired with the prepared soprano 4–3'
  elif ident==('a',117):
   assert (p,q,z)==(61,62,60) and ns[j+2]['pitch']==59
   kind='Early upward C#–D resolution, followed by D–C–B; chromatically inflected turn through A7–D7–G'
  elif ident==('t',129):
   assert (p,q,z)==(59,57,57) and q%12 in CHORDS[h[nxt['start']]]
   kind='Anticipation of the coming dominant fifth, approached down by step'
  elif ident in [('s',176),('s',248),('t',194)]:
   assert abs(a) in (3,4) and step(b) and b<0
   kind='Upper appoggiatura, third into the note and downward step out'
  elif step(a) and step(b) and a*b>0:kind='Stepwise passing note'+(' (accented)' if bad[0]%2==0 else '')
  elif p==z and step(a) and step(b):kind='Returning neighbour'+(' (accented)' if bad[0]%2==0 else '')
  assert kind,('Unclassified nonchord tone',ident,p,q,z)
  # Every ornamental strand must reach a chord tone promptly in this voice.
  targets=[m for m in ns[j+1:] if m['start']<=n['start']+4 and m['pitch']%12 in CHORDS[h[m['start']]]]
  assert targets,('No prompt consonant destination',ident)
  rows.append({'voice':v,'start_tick':n['start'],'nonchord_ticks':bad,'pitches':[p,q,z],'treatment':kind,'consonant_destination_tick':targets[0]['start']})
# Independently verify chromatic secondary-leading notes resolve upward immediately.
chromatic=[]
for v,ns in s['voices'].items():
 for n,nxt in zip(ns,ns[1:]):
  if n['pitch']%12 in (1,3):
   assert nxt['start']==n['start']+n['dur'] and nxt['pitch']==n['pitch']+1
   chromatic.append({'voice':v,'tick':n['start'],'pitches':[n['pitch'],nxt['pitch']]})
result={'scope':'Explicit harmonic plan plus finite local note-shape and destination checks; editorial interpretation, not a complete counterpoint theorem.', 'harmony_by_tick':h,'nonchord_events':rows,'chromatic_resolutions':chromatic,'unclassified':0}
(OUT/'harmonic-review.json').write_text(json.dumps(result,indent=2))
lines=['# Nonchord-tone review','',result['scope'],'','Every sounding note from the first multi-voice entrance onward is either in the declared local chord or listed below. The opening two monophonic measures have no vertical harmony obligation. The map is an authored analytical choice, not a proved unique harmonic interpretation.','', '| Voice | Measure:beat of dissonance | Neighbouring MIDI pitches | Treatment |','|---|---|---|---|']
for r in rows:
 t=r['nonchord_ticks'][0];lines.append(f"| {r['voice'].upper()} | {t//6+1}:{t%6/2+1:g} | {r['pitches']} | {r['treatment']} |")
(OUT/'NONCHORD_TONES.md').write_text('\n'.join(lines)+'\n')
print(f"{len(rows)} nonchord events classified, zero unexplained under the explicit harmonic plan; {len(chromatic)} chromatic leading-note resolutions checked.")
# All harmonic tritones: either a checked ornament or resolving dominant tendency tones.
from itertools import combinations
tritone_review=[]
for t,f in enumerate(fs):
 for u,l in combinations(range(4),2):
  if not f[u] or not f[l] or abs(f[u]-f[l])%12!=6:continue
  ornamental=[v for v in [u,l] if any(r['voice']=='satb'[v] and t in r['nonchord_ticks'] for r in rows)]
  if ornamental:
   why='Transient interval caused by the explicitly checked nonchord treatment in '+','.join('satb'[v] for v in ornamental)
  else:
   chord=h[t];assert chord in ['D7','A7','B7'],(t,f,chord)
   root={'D7':2,'A7':9,'B7':11}[chord];third=(root+4)%12;seventh=(root+10)%12
   for v in [u,l]:
    p=f[v];delta=1 if p%12==third else (-2 if chord=='B7' else -1)
    assert p%12 in [third,seventh]
    future=[n for n in s['voices']['satb'[v]] if n['start']>t and n['pitch']!=p]
    assert future and future[0]['pitch']==p+delta and future[0]['start']<=t+4,(t,v,p,future[:1])
   why=chord+' tendency tones resolve by step in their original voices (within two quarters)'
   if t in [214,215]:why+='; D7 resolves deceptively to E minor at the tenor entry'
  tritone_review.append({'tick':t,'voices':'satb'[u]+'satb'[l],'pitches':[f[u],f[l]],'reason':why})
result['harmonic_tritones']=tritone_review
(OUT/'harmonic-review.json').write_text(json.dumps(result,indent=2))
print(len(tritone_review),'harmonic tritone pair-states checked; every one has a bounded ornament or dominant-resolution justification.')

sevenths=[]
roots={'D7':2,'A7':9,'B7':11,'Em7':4,'Am7':9}
for t,f in enumerate(fs):
 if h[t] not in roots:continue
 seventh=(roots[h[t]]+10)%12
 for v,p in enumerate(f):
  if not p or p%12!=seventh:continue
  future=[n for n in s['voices']['satb'[v]] if n['start']>t and n['pitch']!=p]
  assert future
  exception=(v,t,p)==(0,142,72)
  assert exception or (future[0]['pitch']-p in [-1,-2] and future[0]['start']<=t+4),(t,v,p,future[0])
  sevenths.append({'tick':t,'voice':'satb'[v],'pitch':p,'next_pitch':future[0]['pitch'],'source_tune_exception':exception})
result['chordal_sevenths']=sevenths
(OUT/'harmonic-review.json').write_text(json.dumps(result,indent=2))
print(len(sevenths),'chordal seventh voice/tick occurrences resolve downward; sole source-tune exception explicitly identified.')
unisons=[{'tick':t,'voices':'satb'[v]+'satb'[v+1],'pitch':f[v]} for t,f in enumerate(fs) for v in range(3) if f[v] and f[v]==f[v+1]]
assert unisons==[{'tick':223,'voices':'at','pitch':62}],unisons
result['adjacent_unisons']={'events':unisons,'judgment':'One eighth-note contact: tenor cantus rises B3–D4 beneath held alto D4, which then opens to F#4. Passing contact without crossing; all other adjacent voices remain distinct.'}
(OUT/'harmonic-review.json').write_text(json.dumps(result,indent=2))
