import fs from 'node:fs';
import assert from 'node:assert/strict';
import {derive} from '../player/source.js';
const root=new URL('../',import.meta.url);
for(const piece of fs.readdirSync(new URL('compositions/',root))){
 const dir=new URL(`compositions/${piece}/versions/`,root);
 for(const name of fs.readdirSync(dir)){
  const source=JSON.parse(fs.readFileSync(new URL(name,dir)));
  const generated=JSON.parse(fs.readFileSync(new URL(`compositions/${piece}/generated/${source.version}/composition.json`,root)));
  assert.deepEqual(derive(source),generated.playback);
  const broken=structuredClone(source);broken.measures[0][0][0].duration='1.0';
  assert.throws(()=>derive(broken));
  console.log('Browser and Python beat/timing derivation agree:',source.version);
 }
}
