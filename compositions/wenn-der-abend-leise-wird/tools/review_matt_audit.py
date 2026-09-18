"""Explicit final editorial disposition of every unchanged Matt-policy finding.
These are checked musical explanations, not a proof of aesthetic merit.
"""
from pathlib import Path
import json,hashlib,collections,sys
R=Path(__file__).resolve().parents[1];OUT=Path(sys.argv[1]).resolve()
a=json.loads((OUT/'matt-audit.json').read_text())
h=json.loads((OUT/'harmonic-review.json').read_text())
for k in ['schema_valid','events_well_formed','instantaneous_parallel','pulse_parallel','stagger_parallel','no_crossing','ranges','rhythmic_independence','adjacent_voice_overlap']:
 assert a['checks'][k],k
assert h['unclassified']==0
stagger={
 ('sa',(30,31,32)):'Soprano B–D arpeggiation precedes alto D–G within G major. Independent entrances converge on a chordal fifth; no perfect-to-perfect succession.',
 ('sa',(70,72,73)):'Arrival contains the alto B–C–B neighbour over E minor, not a structural fifth progression; the ornament is separately checked.',
 ('sa',(126,127,128)):'The repeated tune arpeggiates B–D before alto D–G in G major. Retained motivic repetition with staggered chord-tone arrivals.',
 ('sb',(54,55,58)):'Cantus D arrives three eighths before the bass D; a held melody note is reharmonized from G to D. Genuine oblique harmonic change, not consecutive parallel octaves.',
 ('sb',(126,127,130)):'Same cantus-held D and later dominant-bass arrival as m.10; retained phrase identity.',
 ('sb',(152,154,155)):'Bass B arrives before the soprano G–B chordal arpeggiation in G/B; the prior interval is a third, not an octave.',
 ('ab',(68,70,72)):'Alto reaches B while bass still supports G/B, then holds B into E minor. Common-tone connection across I6–vi.',
 ('tb',(70,72,74)):'Bass E arrives before tenor leaves G for E: tenor arpeggiation inside the established E-minor chord, not paired parallel octave movement.',
 ('tb',(194,195,196)):'Tenor B appoggiatura resolves to A over C, then the bass changes to D while A is held. The two endpoints omit the checked resolution.',
 ('tb',(222,223,224)):'Tenor cantus B–D precedes the dominant bass. Held cantus note is reharmonized; upper voices remain independent.',
 ('tb',(246,247,248)):'Repeated tenor-cantus B–D and delayed dominant bass, as m.38.',
 ('st',(83,84,85)):'Cantus C–B resolves while tenor subsequently arpeggiates G–B in the tonic. Stepwise soprano arrival, no parallel progression.',
 ('sb',(80,82,83)):'The endpoints omit the prepared D–C 9–8 suspension over the already-arrived C bass. Resolution is independently checked.',
 ('ab',(67,68,70)):'Passing bass A reaches B first; alto then moves D–B within G/B. The bass ornament and common harmony explain the delayed octave.',
}
def pos(t):return f'{t//6+1}:{t%6/2+1:g}'
def names(ps):return '/'.join(['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][p%12]+str(p//12-1) if p else 'rest' for p in ps)
def disposition(e):
 k=e['check']
 if k.startswith('stagger_'):return stagger[(e['voices'],tuple(e['ticks']))]
 if k=='licensed_harmonic_tritones':
  hits=[r for r in h['harmonic_tritones'] if r['tick']==e['tick']];assert hits
  return '; '.join(dict.fromkeys(r['reason'] for r in hits))
 if k=='allowed_pitch_classes':return 'Secondary leading tone C# or D#; the next note in this same voice rises by semitone, independently checked. It establishes the local dominant rather than accidental chromaticism.'
 if k=='no_melodic_tritone':
  assert (e['voice'],e['tick'],e['semitones'])==('s',143,-6)
  return 'Literal source-tune C5–F#4–G4. Preserving its identity warrants this explicit melodic exception; F# rises immediately to G.'
 if k=='max_leaps':
  assert (e['voice'],e['tick'],e['semitones'])==('s',192,9)
  return 'G4–E5 creates the sole high E, immediately reversing through D5–C5. A bounded expressive sixth, not an uncontrolled line.'
 if k.endswith('_direct'):
  du=e['to_pitches'][0]-e['from_pitches'][0]
  if e['voices']=='sb':
   if abs(du)<=2:return 'Outer soprano approaches by step. I retain this conventional tonal arrival while rejecting outer similar-motion leaps and all consecutive parallel perfects.'
   assert k=='pulse_direct' and e['ticks'] in [[142,144],[262,264]]
   return 'Quarter reduction deletes the soprano’s intermediate eighth: the actual arrival is stepwise (C–F#–G in the fixed tune, or A–B–C). Actual-event outer-leap check passes.'
  return 'Nonparallel arrival involving an inner voice. Retained for the chord-tone destination and independent line; no crossing/overlap, bounded leaps, and a checked harmonic or ornamental context. The blanket all-pair direct-perfect ban is not adopted for this tonal four-part texture.'
 if k.endswith('_battuta'):
  before,after=e['from_pitches'],e['to_pitches'];assert after[0]!=after[1]
  du=after[0]-before[0]
  if abs(du)<=2:return 'Stepwise upper voice and contrary lower motion arrive at an octave, not a unison. Retained contrary-motion articulation; no parallel movement or crossing.'
  tick=e['ticks'][-1]
  if k=='pulse_battuta' and e['voices']=='ab' and tick in [232,256]:return 'Quarter reduction omits E in the alto F#–E–D descent. The actual octave arrival is stepwise; the accented 9–8 figure and subsequent dominant chord are separately checked.'
  if (e['voices'],tick)==('sb',98):return 'm.17: fixed D–B–D cantus over G–B–D bass. Contrary thirds reach the B-minor chord on beat 2; the bass arpeggio and returning soprano shape justify the local octave.'
  if (e['voices'],tick)==('sb',118):return 'm.20: fixed cantus A–D closes the phrase over A7–D7. Opposite bass motion supports the dominant preparation while inner tendency tones resolve; retained phrase-ending octave, not parallel octaves.'
  if (e['voices'],tick)==('ab',238):return 'm.40: inner alto D–B settles into G/B while bass G–B rises. A tonic inversion and inward third, under a sustained soprano; retained inner-voice cadence.'
  raise AssertionError(('Unreviewed inward leap',e))
 raise AssertionError(('Unreviewed finding',e))
rows=[]
for i,e in enumerate(a['errors'],1):rows.append({'id':i,'finding':e,'assessment':disposition(e)})
(OUT/'exception-ledger.json').write_text(json.dumps(rows,indent=2))
lines=['# Final exception ledger','', 'All findings below are genuine failures under Matt’s unchanged strict policy. Their retention is an explicit musical judgment for this tonal fantasia, not a claim that his predicate passes. The additional harmonic checks establish finite note shapes/resolutions under an authored chord analysis; they do not prove that analysis uniquely correct or certify Bach style.','', '| ID | Finding | Measure:beat | Voices / notes | Musical assessment |','|---|---|---|---|---|']
for r in rows:
 e=r['finding'];ticks=e.get('ticks',[e.get('tick',0)]);detail=e.get('voices',e.get('voice','SATB'))
 if 'from_pitches' in e:detail+=' '+names(e['from_pitches'])+' → '+names(e['to_pitches'])
 elif 'pitches' in e:detail+=' '+names(e['pitches'])
 elif 'pitch' in e:detail+=' '+names([e['pitch']])
 lines.append(f"| {r['id']} | {e['check']} | {' → '.join(pos(t) for t in ticks)} | {detail} | {r['assessment']} |")
(OUT/'FINDINGS.md').write_text('\n'.join(lines)+'\n')
files=[OUT/'composition.json',OUT/'matt-input.json',R/'tools/matt/Counterpoint.lean',R/'tools/matt/audit.py']
(OUT/'SHA256.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
print(len(rows),'strict-policy diagnostics accounted for; no unreviewed category or staggered pattern.')
