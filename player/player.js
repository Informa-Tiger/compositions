import {derive} from './source.js';
import {VoiceMixer} from './mixer.js';
let D=null,span=16,scrubbing=false,objectURL=null,loadGeneration=0;
const $=s=>document.querySelector(s),media=$('#audio'),C=$('#roll'),O=$('#overview'),seek=$('#seek');
const status=t=>$('#loadStatus').textContent=t;
const mixer=new VoiceMixer(media,()=>{
 document.querySelectorAll('#legend .voice').forEach((button,i)=>{const on=!mixer.ready||mixer.enabled[i];button.disabled=!mixer.ready;button.setAttribute('aria-pressed',String(on));button.classList.toggle('muted',!on);const state=button.querySelector('.voice-state');if(state)state.textContent=mixer.ready?(on?'On · click to mute':'Muted · click to hear'):'Voice tracks unavailable';});
},()=>status('Voice tracks unavailable; playing the full mix.'));
const A=mixer;
async function loadStems(url,generation){
 const response=await fetch(url.href.replace(/\.json(?:\?.*)?$/,'.stems.json'));
 if(!response.ok)throw Error('Missing voice manifest');
 const info=await response.json();
 const r=await fetch(new URL(info.container.file,url));
 if(!r.ok)throw Error('Missing multitrack MP4');
 const data=await r.arrayBuffer();
 if(generation!==loadGeneration)return;
 if(!await mixer.loadMP4(data))return;
 const a=document.createElement('a');a.href=new URL(info.container.file,url).href;a.textContent='Multitrack MP4';$('#downloads').append(a);
 status('Ready. Click a voice in the legend to mute or restore it.');
}

function jump(t){if(D&&Number.isFinite(t)&&(mixer.ready||A.src))A.currentTime=Math.max(0,Math.min(Number.isFinite(A.duration)?A.duration:D.duration,t))}
A.addEventListener('loadedmetadata',()=>seek.max=A.duration);
A.addEventListener('error',()=>status('Audio could not be loaded. For local playback, select the matching MP3 too.'));
A.addEventListener('play',()=>$('#play').textContent='Pause');A.addEventListener('pause',()=>$('#play').textContent='Play');
async function play(){if(!D||(!mixer.ready&&!A.src))return;try{await A.play()}catch(e){status('Playback unavailable: '+e.message)}}
$('#play').onclick=()=>A.paused?play():A.pause();$('#restart').onclick=()=>{jump(0);play()};
$('#rate').onchange=e=>A.playbackRate=+e.target.value;$('#zoom').onchange=e=>span=+e.target.value;
seek.onpointerdown=()=>scrubbing=true;window.addEventListener('pointerup',()=>scrubbing=false);seek.onblur=()=>scrubbing=false;seek.oninput=()=>jump(+seek.value);
$('#back').onclick=()=>jump(A.currentTime-5);$('#forward').onclick=()=>jump(A.currentTime+5);
$('#jumpMeasure').onsubmit=e=>{e.preventDefault();if(D)jump(D.barTimes[+$('#measure').value-1])};
$('#jumpTime').onsubmit=e=>{e.preventDefault();const m=$('#timestamp').value.trim().match(/^(?:(\d+):)?(\d+(?:\.\d+)?)$/);if(!m||(m[1]&&+m[2]>=60)){$('#jumpError').textContent='Enter seconds or m:ss.';return}$('#jumpError').textContent='';jump(+(m[1]||0)*60 + +m[2])};
function clearAudio(){mixer.clear();A.pause();A.removeAttribute('src');A.load();if(objectURL){URL.revokeObjectURL(objectURL);objectURL=null}}
function display(source){D=derive(source);document.title=D.title+' · '+source.version;$('#title').textContent=D.title;$('#subtitle').textContent=D.subtitle+' · '+source.version+' · '+source.revision.label;$('#measure').max=D.bars;$('#measure').value=1;seek.max=D.duration;seek.value=0;$('#legend').replaceChildren();$('#chapters').replaceChildren();$('#downloads').replaceChildren();
 D.voices.forEach((name,i)=>{const div=document.createElement('button');div.type='button';div.className='voice';div.disabled=true;div.setAttribute('aria-pressed','true');div.onclick=()=>mixer.toggle(i);div.style.setProperty('--c',D.colors[i]);const strong=document.createElement('strong');strong.textContent=name;const label=document.createElement('span');const spans=D.cantus.filter(c=>c.voice===i);label.textContent=spans.length?spans.map(c=>{const beats=Number(D.meter.split('/')[0])*4/Number(D.meter.split('/')[1]);const position=b=>`${Math.floor(b/beats)+1}.${b%beats+1}`;return `${c.label} · mm. ${position(c.start)}–${position(Math.ceil(c.end)-1)}`}).join('; '):(name==='Bass'?'Foundation':'Countervoice');const state=document.createElement('span');state.className='voice-state';state.textContent='Loading voice tracks…';div.append(strong,label,state);$('#legend').append(div)});
 D.sections.forEach(s=>{const b=document.createElement('button');b.textContent=s.name;b.onclick=()=>jump(s.time);$('#chapters').append(b)});
}
async function loadURL(path){const generation=++loadGeneration;clearAudio();D=null;status('Loading…');try{const url=new URL(path,new URL('../',location.href));const resp=await fetch(url);if(!resp.ok)throw Error('HTTP '+resp.status);const source=await resp.json();if(generation!==loadGeneration)return;display(source);status('Loading multitrack audio…');for(const [ext,label] of [['pdf','Score PDF'],['musicxml','MusicXML'],['mid','MIDI'],['mp3','MP3'],['mp4','Video'],['json','Source JSON']]){const a=document.createElement('a');a.href=url.href.replace(/\.json(?:\?.*)?$/,'.'+ext);a.textContent=label;$('#downloads').append(a)}try{await loadStems(url,generation)}catch(error){
 if(generation!==loadGeneration)return;
 const response=await fetch(url.href.replace(/\.json(?:\?.*)?$/,'.mp3'));
 if(!response.ok)throw Error('Full mix unavailable');
 const blob=await response.blob();if(generation!==loadGeneration)return;
 objectURL=URL.createObjectURL(blob);A.src=objectURL;A.load();status('Multitrack audio unavailable; full mix ready.');
 }}catch(e){if(generation===loadGeneration)status('Cannot load composition: '+e.message)}}
$('#files').onchange=async e=>{
 const generation=++loadGeneration,files=[...e.target.files],json=files.find(f=>f.name.endsWith('.json')&&!f.name.endsWith('.stems.json')),mp3=files.find(f=>f.name.endsWith('.mp3')&&!/\.voice-\d+\.mp3$/.test(f.name));
 try{
  if(json){clearAudio();D=null;display(JSON.parse(await json.text()));$('#catalog').value='';const u=new URL(location.href);for(const key of ['score','composition','version'])u.searchParams.delete(key);history.replaceState({},'',u);status('Score loaded. Select its matching .voices.mp4 (or full-mix MP3).');}
  if(mp3){if(!D)throw Error('Select a composition JSON first.');clearAudio();objectURL=URL.createObjectURL(mp3);A.src=objectURL;A.load();status('Full mix ready. Select the multitrack MP4 to enable voice controls.');}
  const multitrack=files.find(f=>f.name.endsWith('.voices.mp4'));
  if(multitrack){if(!D)throw Error('Select the composition JSON too.');await mixer.loadMP4(await multitrack.arrayBuffer());status('Local multitrack audio ready. Click a voice to mute or restore it.');}
 }catch(err){status(err.message)}
};
try{
 const catalog=await (await fetch('../catalog.json')).json();$('#catalog').replaceChildren();
 const ids=[...new Set(catalog.map(i=>i.composition))];
 for(const id of ids){const versions=catalog.filter(i=>i.composition===id).sort((a,b)=>a.version.localeCompare(b.version,undefined,{numeric:true}));const latest=versions.at(-1);const group=document.createElement('optgroup');group.label=latest.title;const option=document.createElement('option');option.value=id+'|latest';option.textContent='Latest ('+latest.version+')';group.append(option);for(const item of versions){const o=document.createElement('option');o.value=id+'|'+item.version;o.textContent=item.version+' — '+item.label;group.append(o)}$('#catalog').append(group)}
 function select(composition,version='latest',updateURL=false){const versions=catalog.filter(i=>i.composition===composition).sort((a,b)=>a.version.localeCompare(b.version,undefined,{numeric:true}));const selected=version==='latest'?versions.at(-1):versions.find(i=>i.version===version);if(!selected){status('Unknown composition or version. Choose one from the catalog.');return}$('#catalog').value=composition+'|'+version;if(updateURL){const url=new URL(location.href);url.searchParams.delete('score');url.searchParams.set('composition',composition);url.searchParams.set('version',version);history.replaceState({},'',url)}loadURL(selected.source)}
 $('#catalog').onchange=e=>{const [composition,version]=e.target.value.split('|');select(composition,version,true)};
 const params=new URL(location.href).searchParams;
 if(params.has('composition'))select(params.get('composition'),params.get('version')||'latest');
 else if(params.has('score')){$('#catalog').value='';loadURL(params.get('score'))}
 else if(ids.length)select(ids[0],params.get('version')||'latest');
}catch(e){status('Catalog unavailable. You can still open local JSON and MP3 files.')}
function fit(c){let r=c.getBoundingClientRect(),k=Math.min(2,devicePixelRatio||1),w=Math.round(r.width*k),h=Math.round(r.height*k);if(c.width!==w||c.height!==h){c.width=w;c.height=h}let g=c.getContext('2d');g.setTransform(k,0,0,k,0,0);return[g,r.width,r.height]}
let lastFrame=-100;function draw(stamp=0){if(stamp-lastFrame<40){requestAnimationFrame(draw);return}lastFrame=stamp;if(!D){requestAnimationFrame(draw);return}let t=A.currentTime,[g,w,h]=fit(C),left=45,right=w-12,top=27,bottom=h-15,low=Math.min(...D.events.map(e=>e.pitch))-2,high=Math.max(...D.events.map(e=>e.pitch))+2,row=(bottom-top)/(high-low+1),start=t-span*.23,scale=(right-left)/span;g.fillStyle='#10171f';g.fillRect(0,0,w,h);
for(let p=low;p<=high;p++){let y=bottom-(p-low+1)*row;if([1,3,6,8,10].includes(p%12)){g.fillStyle='#17232d';g.fillRect(left,y,right-left,row)}if(p%12===0){g.strokeStyle='#33414c';g.beginPath();g.moveTo(left,y+row/2);g.lineTo(right,y+row/2);g.stroke();g.fillStyle='#97a9b7';g.font='12px system-ui';g.fillText('C'+(Math.floor(p/12)-1),8,y+row)}}
D.barTimes.forEach((b,i)=>{let x=left+(b-start)*scale;if(x>=left&&x<=right){g.strokeStyle='#26333d';g.beginPath();g.moveTo(x,top);g.lineTo(x,bottom);g.stroke();g.fillStyle='#97a9b7';g.fillText(i+1,x+4,17)}});
D.events.forEach(e=>{let x=left+(e.time-start)*scale,xe=x+e.seconds*scale;if(xe<left||x>right)return;let y=bottom-(e.pitch-low+1)*row+1,xx=Math.max(left,x),ww=Math.min(right,xe)-xx-1;g.fillStyle=D.colors[e.voice];g.globalAlpha=mixer.ready&&!mixer.enabled[e.voice]?.12:(e.time+e.seconds<t?.5:1);g.fillRect(xx,y,Math.max(1,ww),row-2);g.globalAlpha=1;if((!mixer.ready||mixer.enabled[e.voice])&&(e.cf||e.time<=t&&t<e.time+e.seconds)){g.strokeStyle=e.cf?'#f9f7eb':D.colors[e.voice];g.lineWidth=e.time<=t&&t<e.time+e.seconds?2:1;g.strokeRect(xx+.5,y+.5,Math.max(1,ww-1),row-3)}});
let px=left+span*.23*scale;g.strokeStyle='#faf5e1';g.lineWidth=1.5;g.beginPath();g.moveTo(px,top-5);g.lineTo(px,bottom+5);g.stroke();
if(!scrubbing)seek.value=t;
let b=Math.min(D.bars,D.barTimes.filter(v=>v<=t+0.02).length),sec=D.sections.filter(s=>s.time<=t+0.02).at(-1);document.querySelector('#section').textContent=sec?.name||'';document.querySelector('#time').textContent='Measure '+b+' / '+D.bars+' · '+Math.floor(t/60)+':'+String(Math.floor(t%60)).padStart(2,'0');
let [q,ow,oh]=fit(O);q.fillStyle='#15212c';q.fillRect(0,0,ow,oh);D.events.forEach(e=>{q.globalAlpha=mixer.ready&&!mixer.enabled[e.voice]?.15:1;q.fillStyle=D.colors[e.voice];q.fillRect(e.time/D.duration*ow,8+(high-e.pitch)*(oh-16)/(high-low+1),Math.max(2,e.seconds/D.duration*ow),2)});q.globalAlpha=1;q.strokeStyle='#fff';q.beginPath();q.moveTo(t/D.duration*ow,0);q.lineTo(t/D.duration*ow,oh);q.stroke();requestAnimationFrame(draw)}
O.onclick=e=>{if(D)jump((e.clientX-O.getBoundingClientRect().left)/O.clientWidth*D.duration)};draw();