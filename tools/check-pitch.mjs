// Exercise the shipped worklet DSP with known stereo tones, without a browser.
import assert from 'node:assert/strict';
let Processor;
globalThis.sampleRate=48000;
globalThis.AudioWorkletProcessor=class{port={postMessage(){}}};
globalThis.registerProcessor=(name,implementation)=>{Processor=implementation};
await import('../player/vendor/soundtouch-processor-2.1.1.js');
for(const rate of [.75,1.25]){
 const p=new Processor();const result=[[],[]];
 const parameters={pitch:[1],pitchSemitones:[0],playbackRate:[rate]};
 for(let frame=0;frame<48000*4;frame+=128){
  const input=[440,660].map(f=>Float32Array.from({length:128},(_,i)=>.25*Math.sin(2*Math.PI*f*rate*(frame+i)/48000)));
  const output=[new Float32Array(128),new Float32Array(128)];p.process([input],[output],parameters);
  output.forEach((samples,c)=>result[c].push(...samples));
 }
 for(const [channel,expected] of [440,660].entries()){
  const samples=result[channel].slice(48000);let crossings=[];
  for(let i=1;i<samples.length;i++)if(samples[i-1]<0&&samples[i]>=0)crossings.push(i-1-samples[i-1]/(samples[i]-samples[i-1]));
  const hz=(crossings.length-1)*48000/(crossings.at(-1)-crossings[0]);
  assert(Math.abs(hz-expected)<2,`${rate}: expected ${expected}Hz, got ${hz}`);
  assert(samples.every(Number.isFinite));
  let longestSilence=0,run=0;
  for(const x of samples){run=Math.abs(x)<1e-6?run+1:0;longestSilence=Math.max(longestSilence,run)}
  assert(longestSilence<128,'No silent/dropout blocks after startup');
  console.log(`${rate*100}% channel ${channel+1}: ${hz.toFixed(2)} Hz (expected ${expected}), no dropout blocks`);
 }
}
