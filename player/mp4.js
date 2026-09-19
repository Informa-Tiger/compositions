// Keep one MP4 track without moving any bytes: chunk offsets and edit lists
// remain intact. Other trak boxes become same-sized free boxes. The browser
// decoder therefore receives an ordinary, single-audio-track MP4.
export function splitTracks(input) {
 const bytes = new Uint8Array(input), view = new DataView(input);
 function boxes(start, end) {
  const result=[];
  for(let p=start;p<end;) {
   if(p+8>end)throw Error('Truncated MP4 box');
   let size=view.getUint32(p),header=8;
   if(size===1){if(p+16>end)throw Error('Truncated extended box');size=Number(view.getBigUint64(p+8));header=16;}
   if(size===0)size=end-p;
   if(!Number.isSafeInteger(size)||size<header||p+size>end)throw Error('Invalid MP4 box size');
   result.push({p,size,header,type:String.fromCharCode(...bytes.subarray(p+4,p+8))});p+=size;
  }
  return result;
 }
 const moov=boxes(0,bytes.length).find(b=>b.type==='moov');
 if(!moov)throw Error('Missing MP4 metadata');
 const tracks=boxes(moov.p+moov.header,moov.p+moov.size).filter(b=>b.type==='trak');
 if(tracks.length!==4)throw Error('Expected exactly four voice tracks');
 return tracks.map(keep=>{
  const copy=bytes.slice();
  for(const track of tracks)if(track!==keep)copy.set([102,114,101,101],track.p+4);
  return copy.buffer;
 });
}
