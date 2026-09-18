from pathlib import Path
import json,sys
r=Path(__file__).resolve().parents[1];OUT=Path(sys.argv[1]).resolve();s=json.loads((OUT/'matt-input.json').read_text());c=s['config']
names={'totalTicks':'total_ticks','ticksPerQuarter':'ticks_per_quarter','tonicPc':'tonic_pc','tonicThird':'tonic_third','pulseStride':'pulse_stride','pulseOffset':'pulse_offset','tritoneMaxWait':'tritone_max_wait','minIndependentChanges':'min_independent_changes'}
f=[f'  {k} := {c[v]}' for k,v in names.items()]+[f"  allowedPcs := {c['allowed_pcs']}", '  ranges := ['+', '.join(f'({a}, {b})' for a,b in c['ranges'])+']',f"  maxLeaps := {c['max_leaps']}",'  requireIndependence := true']
p=['  '+v+' := ['+', '.join('⟨{start}, {dur}, {pitch}⟩'.format(**n) for n in s['voices'][v])+']' for v in 'satb']
core=(r/'tools/matt/Counterpoint.lean').read_text()
out=core+'\n-- Diagnostic proof: unchanged Matt predicates; failures are proved false, not waived.\nset_option maxRecDepth 100000\nset_option maxHeartbeats 0\nnamespace Review\nopen Counterpoint\ndef config : Config := {\n'+'\n'.join(f)+'\n}\ndef voices : Voices := {\n'+'\n'.join(p)+'\n}\ndef fs := timeline voices config.totalTicks\n'
checks={'configuration':('validConfig config',True),'events':('wellFormed voices config.totalTicks',True),'direct':('checkNoDirect fs',False),'parallel':('checkNoParallel fs',True),'battuta':('checkNoBattuta fs',False),'pulse':('checkStructural voices config.totalTicks config.pulseStride config.pulseOffset',False),'stagger':('checkNoStaggeredPerfects fs',False),'crossing':('fs.all noCrossing',True),'ranges':('fs.all (voiceRanges config)',True),'scale':('fs.all (inScale config)',False),'melody':('checkMelody voices',False),'tritones':('checkTritones config fs',False),'independence':('hasRhythmicIndependence config voices',True),'rejected':('certified config voices',False)}
for name,(expr,b) in checks.items():out+=f'theorem {name}_result : ({expr}) = {str(b).lower()} := by decide\n#print axioms {name}_result\n'
out+='end Review\n';(OUT/'MattDiagnostic.lean').write_text(out)

prefix=out.split('theorem configuration_result')[0]
(OUT/'Rejected.lean').write_text(prefix+'theorem rejected : certified config voices = false := by decide\n#print axioms rejected\nend Review\n')
