import {splitTracks} from './mp4.js';

// One AudioContext is both the transport and the clock for all four voices.
export class VoiceMixer extends EventTarget {
 constructor(master,changed,failed){
  super();this.master=master;this.changed=changed;this.failed=failed;
  this.buffers=[];this.nodes=[];this.gains=[];this.enabled=[];
  this.position=0;this.running=false;this.rate=1;this.epoch=0;
  for(const event of ['loadedmetadata','error','play','pause'])master.addEventListener(event,()=>{if(!this.ready)this.dispatchEvent(new Event(event))});
 }
 get ready(){return this.buffers.length===4}
 get src(){return this.master.src}
 set src(v){this.master.src=v}
 get duration(){return this.ready?this.buffers[0].duration:this.master.duration}
 get paused(){return this.ready?!this.running:this.master.paused}
 get currentTime(){return this.ready?Math.min(this.duration,this.position+(this.running?Math.max(0,this.context.currentTime-this.started)*this.rate:0)):this.master.currentTime}
 set currentTime(v){if(!this.ready){this.master.currentTime=v;return}const resume=this.running;this.stop();this.position=Math.max(0,Math.min(this.duration,v));if(resume)this.start()}
 get playbackRate(){return this.ready?this.rate:this.master.playbackRate}
 set playbackRate(v){const t=this.currentTime,resume=this.running;this.stop();this.rate=v;this.master.playbackRate=v;this.position=t;if(resume)this.start()}
 removeAttribute(v){this.master.removeAttribute(v)}
 load(){this.master.load()}
 clear(){this.epoch++;this.stop();this.buffers=[];this.enabled=[];this.position=0;this.master.pause();this.master.muted=false;this.changed();this.dispatchEvent(new Event('pause'))}
 async loadMP4(data){
  const epoch=this.epoch;
  this.context??=new AudioContext({sampleRate:48000});
  this.workletReady??=this.context.audioWorklet.addModule(new URL('./vendor/soundtouch-processor-2.1.1.js',import.meta.url));
  await this.workletReady;
  const buffers=await Promise.all(splitTracks(data).map(b=>this.context.decodeAudioData(b)));
  if(epoch!==this.epoch)return false;
  if(buffers.some(b=>b.length!==buffers[0].length||b.numberOfChannels!==2))throw Error('Voice tracks have unequal lengths or channel layouts');
  const resume=!this.paused,time=this.currentTime;this.stop();
  this.master.pause();this.master.muted=true;this.buffers=buffers;this.enabled=[true,true,true,true];this.position=time;this.rate=this.master.playbackRate;
  this.changed();this.dispatchEvent(new Event('loadedmetadata'));if(resume)await this.play();return true;
 }
 toggle(i){if(!this.ready)return;this.enabled[i]=!this.enabled[i];const gain=this.gains[i]?.gain;if(gain){gain.cancelScheduledValues(this.context.currentTime);gain.setTargetAtTime(this.enabled[i]?1:0,this.context.currentTime,.008)}this.changed()}
 stop(){
  if(this.running)this.position=this.currentTime;
  this.running=false;
  for(const node of this.nodes){node.onended=null;try{node.stop()}catch{}node.disconnect()}
  if(this.processor){this.processor.disconnect();this.processor.port.close();this.processor=null;}
  for(const gain of this.gains)gain.disconnect();this.nodes=[];this.gains=[];
 }
 start(){
  if(!this.ready||this.running)return;
  if(this.position>=this.duration)this.position=0;
  this.started=this.context.currentTime+.025;this.running=true;
  // Sum the selected voices before a single pitch-compensating processor.
  // At normal speed bypass DSP entirely, preserving the decoded audio.
  let destination=this.context.destination;
  if(this.rate!==1){
   this.processor=new AudioWorkletNode(this.context,'soundtouch-processor',{
    numberOfInputs:1,numberOfOutputs:1,outputChannelCount:[2],
    parameterData:{pitch:1,pitchSemitones:0,playbackRate:this.rate}
   });
   this.processor.connect(destination);destination=this.processor;
  }
  this.nodes=this.buffers.map((buffer,i)=>{
   const node=this.context.createBufferSource(),gain=this.context.createGain();node.buffer=buffer;node.playbackRate.value=this.rate;
   gain.gain.setValueAtTime(0,this.started);gain.gain.linearRampToValueAtTime(this.enabled[i]?1:0,this.started+.008);
   node.connect(gain).connect(destination);this.gains.push(gain);node.start(this.started,this.position);return node;
  });
  this.nodes[0].onended=()=>{this.stop();this.position=this.duration;this.dispatchEvent(new Event('pause'))};
 }
 async play(){if(!this.ready)return this.master.play();const epoch=this.epoch;await this.context.resume();if(epoch!==this.epoch||!this.ready)return;this.start();this.dispatchEvent(new Event('play'))}
 pause(){if(!this.ready){this.master.pause();return}this.stop();this.dispatchEvent(new Event('pause'))}
}
