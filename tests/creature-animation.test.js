'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('assets/sprites/creature-animation.js','utf8');
const sandbox={window:{}};
vm.runInNewContext(source,sandbox,{filename:'assets/sprites/creature-animation.js'});
const api=sandbox.window.NexusCreatureAnimation;
assert.equal(api.species.length,16,'all generated species need a rig');
const calls=['save','restore','translate','scale','rotate','beginPath','moveTo','lineTo','closePath','fill','stroke','bezierCurveTo'];
const ctx={};
for(const method of calls)ctx[method]=()=>{};
for(const name of api.species){
  assert.ok(api.profile(name),`missing profile for ${name}`);
  const a=api.draw(ctx,{id:17,species:name,vx:.2,vy:.03},0,0,40,20,3.25,{view:'side',flip:false});
  const b=api.draw(ctx,{id:17,species:name,vx:.2,vy:.03},0,0,40,20,3.25,{view:'side',flip:false});
  assert.ok(Number.isFinite(a.phase),`invalid phase for ${name}`);
  assert.equal(a.phase,b.phase,`animation must be deterministic for ${name}`);
  assert.ok(Number.isFinite(a.bodyFlex));
}
assert.equal(api.profile('shark').type,'shark');
assert.equal(api.profile('jellyfish').type,'jelly');
assert.equal(api.profile('sea_turtle').type,'turtle');
console.log(`Species rig checks passed for ${api.species.length} species.`);
