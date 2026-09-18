"""Build score, sound and visualizations from one composition JSON."""
from pathlib import Path
from fractions import Fraction
import argparse, hashlib, json, subprocess, sys, html
import mido
from music21 import stream, note, meter, key, clef, metadata, tempo, expressions, instrument, bar, tie

ROOT=Path(__file__).resolve().parents[1]
def run(args): subprocess.run([str(x) for x in args],check=True)
def read(path): return json.loads(Path(path).read_text())
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def validate(d):
    import jsonschema
    jsonschema.validate(d,read(ROOT/'schema/composition.schema.json'))
    beats=Fraction(d['meter'].split('/')[0])*4/int(d['meter'].split('/')[1])
    assert len(d['voices'])==4
    for row in d['measures']:
        assert len(row)==4
        for cell in row:
            assert sum(Fraction(n['duration']) for n in cell)==beats,'Incomplete measure'
            for n in cell:
                assert Fraction(n['duration'])>0
                if n['pitch']!='R': assert 0<=note.Note(n['pitch']).pitch.midi<=127
    count=len(d['measures'])
    assert d['tempos'][0]['bar']==1
    assert [x['bar'] for x in d['tempos']]==sorted(set(x['bar'] for x in d['tempos']))
    assert all(1<=x['bar']<=count for x in d['tempos']+d['sections'])
    assert all(0<=c['start']<c['end']<=count*beats for c in d['cantus'])
    return float(beats)

def derive(d):
    beats=validate(d); count=len(d['measures']); tempi={x['bar']:x['bpm'] for x in d['tempos']}
    def seconds(beat):
        t=0.;bpm=tempi[1]
        for i in range(count):
            bpm=tempi.get(i+1,bpm);t+=max(0,min(beats,beat-i*beats))*60/bpm
        return t
    ties={(x['voice'],float(Fraction(x['beat']))) for x in d['ties']}; events=[]; used=set()
    for v in range(4):
        for bi,row in enumerate(d['measures']):
            pos=bi*beats
            for n in row[v]:
                dur=float(Fraction(n['duration']));p=n['pitch']
                if p!='R':
                    e=dict(voice=v,bar=bi+1,start=pos,duration=dur,pitch=note.Note(p).pitch.midi,name=p,cf=any(c['voice']==v and c['start']<=pos<c['end'] for c in d['cantus']))
                    if (v,pos) in ties:
                        a=events[-1]; assert a['voice']==v and a['pitch']==e['pitch'] and abs(a['start']+a['duration']-pos)<1e-8,'Invalid tie'
                        a['duration']+=dur;used.add((v,pos))
                    else: events.append(e)
                pos+=dur
    assert used==ties,'Tie does not point to a note'
    for e in events:e.update(time=seconds(e['start']),seconds=seconds(e['start']+e['duration'])-seconds(e['start']))
    return dict(title=d['title'],subtitle=d['subtitle'],voices=[v['name'] for v in d['voices']],colors=[v['color'] for v in d['voices']],bars=count,meter=d['meter'],key=d['key'],duration=seconds(count*beats),events=events,cantus=d['cantus'],sections=[dict(s,time=seconds((s['bar']-1)*beats)) for s in d['sections']],barTimes=[seconds(i*beats) for i in range(count+1)],tempo={str(k):v for k,v in tempi.items()})

def export(d,p,out):
    beats=float(Fraction(d['meter'].split('/')[0])*4/int(d['meter'].split('/')[1]));count=len(d['measures']);tempi={x['bar']:x['bpm'] for x in d['tempos']};sections={x['bar']:x['name'] for x in d['sections']};ties={(x['voice'],float(Fraction(x['beat']))) for x in d['ties']};cfg=d['render']
    score=stream.Score();score.metadata=metadata.Metadata(title=d['title'],composer=d['composer'],movementName=d['subtitle'])
    for vi,v in enumerate(d['voices']):
        part=stream.Part(id=v['name']);part.partName=v['name'];part.partAbbreviation=v['shortName'];part.insert(0,instrument.PipeOrgan())
        for bi,row in enumerate(d['measures']):
            m=stream.Measure(number=bi+1)
            if bi==0:
                m.insert(0,meter.TimeSignature(d['meter']));m.insert(0,key.Key(d['key']));m.insert(0,clef.TrebleClef() if v['clef']=='treble' else clef.BassClef())
            if vi==0 and bi+1 in tempi:m.insert(0,tempo.MetronomeMark(number=tempi[bi+1]))
            if vi==0 and bi+1 in sections:m.insert(0,expressions.TextExpression(sections[bi+1]))
            pos=bi*beats
            for n in row[vi]:
                dur=Fraction(n['duration']); obj=note.Rest(quarterLength=dur) if n['pitch']=='R' else note.Note(n['pitch'],quarterLength=dur)
                if n['pitch']!='R':
                    incoming=(vi,pos) in ties;outgoing=(vi,pos+float(dur)) in ties
                    if incoming or outgoing:obj.tie=tie.Tie('continue' if incoming and outgoing else 'stop' if incoming else 'start')
                m.append(obj);pos+=float(dur)
            if bi==count-1:
                m.rightBarline=bar.Barline('final')
                if d['engraving']['fermataFinal']:m.notes[-1].expressions.append(expressions.Fermata())
            part.append(m)
        score.insert(0,part)
    score.write('musicxml',fp=out/'composition.musicxml')
    for perf in [False,True]:
        mid=mido.MidiFile(ticks_per_beat=960);con=mido.MidiTrack();mid.tracks.append(con)
        num,den=map(int,d['meter'].split('/'));con.extend([mido.MetaMessage('track_name',name=d['title']),mido.MetaMessage('time_signature',numerator=num,denominator=den),mido.MetaMessage('key_signature',key=d['key'])]);last=0
        for b,bpm in tempi.items():
            tick=round((b-1)*beats*960);con.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(bpm),time=tick-last));last=tick
        for vi,v in enumerate(d['voices']):
            tr=mido.MidiTrack();mid.tracks.append(tr);tr.extend([mido.MetaMessage('track_name',name=v['name']),mido.Message('program_change',program=v['program'],channel=vi),mido.Message('control_change',channel=vi,control=10,value=v['pan']),mido.Message('control_change',channel=vi,control=7,value=v['volume'])]);seq=[]
            for e in (e for e in p['events'] if e['voice']==vi):
                end=e['start']+e['duration']
                if perf and e['bar']!=count:end-=min(cfg['articulationMaxBeats'],e['duration']*cfg['articulationFraction'])
                vel=v['velocity']+(cfg['cantusVelocityBoost'] if e['cf'] else 0)
                seq.extend([(round(e['start']*960),mido.Message('note_on',channel=vi,note=e['pitch'],velocity=vel)),(round(end*960),mido.Message('note_off',channel=vi,note=e['pitch'],velocity=0))])
            last=0
            for tick,msg in sorted(seq,key=lambda x:(x[0],x[1].type=='note_on')):msg.time=tick-last;tr.append(msg);last=tick
        mid.save(out/('composition-performance.mid' if perf else 'composition.mid'))
    def quote(s): return json.dumps(s,ensure_ascii=False)
    def lp(s):
        if s=='R':return 'r'
        p=note.Note(s).pitch
        return p.step.lower()+{'#':'is','-':'es','':'','##':'isis','--':'eses'}[p.accidental.modifier if p.accidental else '']+("'"*(p.octave-3) if p.octave>=3 else ','*(3-p.octave))
    durations={Fraction('0.25'):'16',Fraction('0.5'):'8',Fraction(1):'4',Fraction('1.5'):'4.',Fraction(2):'2',Fraction(3):'2.'}
    eg=d['engraving'];k=key.Key(d['key']); lines=['\\version "2.26.0"','\\pointAndClickOff','\\header {',f'title = {quote(d["title"])}',f'subtitle = {quote(d["subtitle"])}',f'composer = {quote(d["composer"])}',f'poet = {quote(d["tuneCredit"])}',f'tagline = {quote(eg["tagline"])}','}',f'#(set-global-staff-size {eg["staffSize"]})',r'\paper { #(set-paper-size "a4") top-margin = 12\mm bottom-margin = 12\mm left-margin = 14\mm right-margin = 12\mm system-system-spacing.basic-distance = #17 score-system-spacing.basic-distance = #16 print-page-number = ##t }',f'global = {{ \\key {lp(k.tonic.name+"3")} \\{k.mode} \\time {d["meter"]} }}']
    for vi,v in enumerate(d['voices']):
        lines.append(f'voice{["A","B","C","D"][vi]} = {{ \\global \\clef {v["clef"]}')
        for bi,row in enumerate(d['measures']):
            if vi==0:
                if bi+1 in tempi:lines.append(f'\\tempo {quote(eg["tempoText"]) if bi==0 else ""} 4 = {tempi[bi+1]}')
                if bi+1 in sections:lines.append('\\mark \\markup { \\small '+quote(sections[bi+1])+' }')
            pos=bi*beats;cells=[]
            for n in row[vi]:
                dur=Fraction(n['duration']);txt=lp(n['pitch'])+durations[dur];pos+=float(dur)
                if (vi,pos) in ties:txt+=' ~'
                cells.append(txt)
            if bi==count-1 and eg['fermataFinal']:cells[-1]+='\\fermata'
            lines.append(' '.join(cells)+' |')
            if vi==0:
                if bi+1 in eg['pageBreakAfter']:lines.append('\\pageBreak')
                elif (bi+1)%eg['systemEvery']==0:lines.append('\\break')
        lines.append('\\bar "|." }')
    lines.append('\\score { \\new StaffGroup <<')
    for vi,v in enumerate(d['voices']):lines.append('\\new Staff \\with { instrumentName = '+quote(v['name'])+' shortInstrumentName = '+quote(v['shortName'])+' } \\voice'+['A','B','C','D'][vi])
    lines.append(r'>> \layout { indent = 14\mm short-indent = 7\mm \context { \Score \override RehearsalMark.self-alignment-X = #LEFT } } }')
    (out/'composition.ly').write_text('\n'.join(lines)+'\n')

def build(source,media=True,video=True):
    source=Path(source).resolve();d=read(source);d.pop('playback',None);piece=source.parent.parent.parent if source.parent.parent.name=='generated' else source.parent.parent;out=piece/'generated'/d['version'];out.mkdir(parents=True,exist_ok=True)
    previous=read(out/'manifest.json') if (out/'manifest.json').exists() else {}
    source_hash=hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
    if previous.get('sourceDataSha256')!=source_hash:(out/'lean-verification.txt').unlink(missing_ok=True)
    p=derive(d);snapshot=dict(d,playback=p)
    (out/'composition.json').write_text(json.dumps(snapshot,indent=2)+'\n');export(d,p,out)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>'+html.escape(d['title'])+'</title><script>location.replace("../../../../player/?composition='+d['id']+'&version='+d['version']+'")</script><a href="composition.mp3">Listen</a>')
    if media:
        run(['lilypond','-o',out/'composition',out/'composition.ly'])
        cfg=d['render'];sf=piece/cfg['soundfont'];assert digest(sf)==cfg['soundfontSha256'],'Soundfont hash mismatch';tmp=ROOT/'build'/d['id']/d['version'];tmp.mkdir(parents=True,exist_ok=True);raw=tmp/'organ.wav'
        args=['fluidsynth','-ni','-g',cfg['gain'],'-r',cfg['sampleRate'],'-o','synth.reverb.active=1']
        for k,v in cfg['reverb'].items():args+=['-o',f'synth.reverb.{k}={v}']
        args+=['-o',f'synth.chorus.active={int(cfg["chorus"])}','-F',raw,sf,out/'composition-performance.mid'];run(args)
        af=f'loudnorm=I={cfg["loudnessLUFS"]}:TP={cfg["truePeakDB"]}:LRA={cfg["loudnessRange"]},afade=t=out:st={p["duration"]+cfg["fadeDelaySeconds"]}:d={cfg["fadeSeconds"]}'
        run(['ffmpeg','-v','error','-y','-i',raw,'-af',af,'-ar',cfg['sampleRate'],'-codec:a','libmp3lame','-b:a',cfg['mp3Bitrate'],out/'composition.mp3'])
        raw.unlink()
        run([sys.executable,ROOT/'tools/video.py',out/'composition.json',*(['--video'] if video else [])])
    run([sys.executable,ROOT/'tools/verify.py',out/'composition.json'])
    versions={}
    for cmd in [['lilypond','--version'],['fluidsynth','--version'],['ffmpeg','-version']]:
        try:versions[cmd[0]]=subprocess.check_output(cmd,stderr=subprocess.STDOUT,text=True).splitlines()[0]
        except Exception:versions[cmd[0]]='unavailable'
    manifest={'source':str(source.relative_to(ROOT)),'sourceDataSha256':source_hash,'mediaSourceDataSha256':source_hash if media else previous.get('mediaSourceDataSha256'),'videoSourceDataSha256':source_hash if media and video else previous.get('videoSourceDataSha256'),'schemaVersion':1,'buildTools':versions,'artifacts':{f.name:digest(f) for f in sorted(out.iterdir()) if f.is_file() and f.name!='manifest.json'}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Built',out,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',nargs='?');ap.add_argument('--all',action='store_true');ap.add_argument('--no-media',action='store_true');ap.add_argument('--no-video',action='store_true');a=ap.parse_args()
    paths=sorted(ROOT.glob('compositions/*/versions/*.json')) if a.all else [Path(a.source)]
    for path in paths:build(path,not a.no_media,not a.no_video)
