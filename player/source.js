// Beat-based source is authoritative. Ignore the optional cached playback data.
export function derive(d){
 if(d.format!=='composition'||d.schemaVersion!==1||d.meter!=='3/4'||!Array.isArray(d.voices)||d.voices.length!==4)throw Error('Unsupported composition format');
 const duration=s=>{const a=String(s).split('/').map(Number),v=a.length===2?a[0]/a[1]:a[0];if(!Number.isFinite(v)||v<=0)throw Error('Invalid duration');return v};
 const pitch=s=>{const m=s.match(/^([A-G])([#-]{0,2})([0-9])$/);if(!m)throw Error('Invalid pitch');return (Number(m[3])+1)*12+{C:0,D:2,E:4,F:5,G:7,A:9,B:11}[m[1]]+[...m[2]].reduce((a,c)=>a+(c==='#'?1:-1),0)};
 const tempi=new Map(d.tempos.map(t=>[t.bar,t.bpm]));if(!tempi.has(1)||d.tempos.some(t=>!(t.bpm>0)))throw Error('Missing or invalid tempo');
 function seconds(beat){let total=0,bpm=tempi.get(1);for(let i=0;i<d.measures.length;i++){bpm=tempi.get(i+1)||bpm;total+=Math.max(0,Math.min(3,beat-i*3))*60/bpm}return total}
 const ties=new Set(d.ties.map(t=>t.voice+':'+Number(t.beat))),used=new Set(),events=[];
 for(let v=0;v<4;v++)d.measures.forEach((row,bi)=>{if(row.length!==4)throw Error('Expected four voices');let pos=bi*3;for(const n of row[v]){let dur=duration(n.duration);if(n.pitch!=='R'){const e={voice:v,bar:bi+1,start:pos,duration:dur,pitch:pitch(n.pitch),name:n.pitch,cf:d.cantus.some(c=>c.voice===v&&c.start<=pos&&pos<c.end)};if(ties.has(v+':'+pos)){const prev=events.at(-1);if(!prev||prev.voice!==v||prev.pitch!==e.pitch||Math.abs(prev.start+prev.duration-pos)>1e-7)throw Error('Invalid tie');prev.duration+=dur;used.add(v+':'+pos)}else events.push(e)}pos+=dur}if(Math.abs(pos-(bi+1)*3)>1e-7)throw Error('Incomplete measure')});
 if(used.size!==ties.size)throw Error('Unused tie');
 for(const e of events){e.time=seconds(e.start);e.seconds=seconds(e.start+e.duration)-e.time}
 return {title:d.title,subtitle:d.subtitle,voices:d.voices.map(v=>v.name),colors:d.voices.map(v=>v.color),bars:d.measures.length,meter:d.meter,key:d.key,duration:seconds(d.measures.length*3),events,cantus:d.cantus,sections:d.sections.map(s=>({...s,time:seconds((s.bar-1)*3)})),barTimes:Array.from({length:d.measures.length+1},(_,i)=>seconds(i*3)),tempo:Object.fromEntries(tempi)};
}
