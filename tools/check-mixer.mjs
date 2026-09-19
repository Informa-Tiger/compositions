import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import os from 'node:os';
import path from 'node:path';
import {splitTracks} from '../player/mp4.js';
import {VoiceMixer} from '../player/mixer.js';
const file=fs.readFileSync('compositions/wenn-der-abend-leise-wird/generated/v001/composition.voices.mp4');
const tracks=splitTracks(file.buffer.slice(file.byteOffset,file.byteOffset+file.byteLength));
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'voice-mp4-'));
try {
 tracks.forEach((data,i)=>{
  const p=path.join(temp,`${i}.mp4`);fs.writeFileSync(p,new Uint8Array(data));
  const info=JSON.parse(execFileSync('ffprobe',['-v','error','-show_streams','-of','json',p]));
  assert.equal(info.streams.length,1);assert.equal(info.streams[0].codec_name,'aac');
  const pcm=execFileSync('ffmpeg',['-v','error','-i',p,'-f','f32le','-'],{maxBuffer:100*1024*1024});
  const original=execFileSync('ffmpeg',['-v','error','-i','compositions/wenn-der-abend-leise-wird/generated/v001/composition.voices.mp4','-map',`0:a:${i}`,'-f','f32le','-'],{maxBuffer:100*1024*1024});
  assert.deepEqual(pcm,original,'Extraction must preserve decoded samples and encoder-delay edit list');
 });
}finally{fs.rmSync(temp,{recursive:true,force:true})}
assert.throws(()=>splitTracks(new ArrayBuffer(7)));
class Master extends EventTarget {currentTime=0;paused=true;playbackRate=1;pause(){this.paused=true}}
const processors=[];
globalThis.AudioWorkletNode=class {
 constructor(context,name,options){this.options=options;this.port={close(){}};processors.push(this)}
 connect(target){this.target=target;return target}disconnect(){this.disconnected=true}
};
const created=[];
const ctx={currentTime:10,destination:{},resume:async()=>{},createBufferSource(){const n={playbackRate:{},connect(target){this.target=target;return target},disconnect(){},stop(){},start(...args){this.args=args}};created.push(n);return n},createGain(){return{gain:{setValueAtTime(){},linearRampToValueAtTime(){},cancelScheduledValues(){},setTargetAtTime(){}},connect(target){this.target=target;return target},disconnect(){}}}};
const mixer=new VoiceMixer(new Master(),()=>{},()=>{});mixer.context=ctx;mixer.buffers=Array(4).fill({duration:100});mixer.enabled=[true,true,true,true];
await mixer.play();assert.equal(new Set(created.map(n=>n.args[0])).size,1);assert.equal(new Set(created.map(n=>n.args[1])).size,1);
ctx.currentTime=20;assert.equal(mixer.currentTime,9.975);
mixer.toggle(2);assert.equal(created.length,4,'Muting must not restart or seek');
mixer.currentTime=50;assert.equal(created.length,8);assert(created.slice(4).every(n=>n.args[1]===50));
mixer.playbackRate=.75;assert(created.slice(-4).every(n=>n.playbackRate.value===.75));
assert.equal(processors.length,1);
assert.equal(processors[0].options.parameterData.pitch,1);
assert.equal(processors[0].options.parameterData.playbackRate,.75);
assert(created.slice(-4).every(n=>n.target.target===processors[0]),'All voices must mix through the same processor');
mixer.playbackRate=1.25;
assert.equal(processors.at(-1).options.parameterData.pitch,1);
assert.equal(processors.at(-1).options.parameterData.playbackRate,1.25);
mixer.playbackRate=1;
assert(created.slice(-4).every(n=>n.target.target===ctx.destination),'Normal speed must bypass processing');
assert(processors.every(p=>p.disconnected));
mixer.pause();const paused=mixer.currentTime;ctx.currentTime+=10;assert.equal(mixer.currentTime,paused);
mixer.clear();assert(!mixer.ready);assert(!mixer.running);
console.log('MP4 track extraction is sample-identical; shared clock, mute, seek, rate and pause checks passed.');
