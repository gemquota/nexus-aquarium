'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {URL}=require('node:url');
const source=fs.readFileSync('assets/sprites/sprite-runtime.js','utf8');
const sandbox={
 window:{dispatchEvent(){}},
 document:{currentScript:{src:'https://example.test/assets/sprites/sprite-runtime.js'}},
 fetch:async()=>({ok:true,json:async()=>({assets:[
  {kind:'plant',species:'seaweed',filename:'seaweed_green_a.png',src:'/assets/sprites/seaweed_green_a.png',frames:1},
  {kind:'plant',species:'seaweed',filename:'seaweed_grass_a.png',src:'/assets/sprites/seaweed_grass_a.png',frames:1},
  {kind:'plant',species:'seaweed',filename:'background_seaweed_a.png',src:'/assets/sprites/background_seaweed_a.png',frames:1}
 ]})}),
 Image:class FakeImage{constructor(){this.naturalWidth=64;this.naturalHeight=64;this.decoding='';}set src(value){this._src=value;this.onload?.();}get src(){return this._src;}},
 CustomEvent:class CustomEvent{},
 URL,
 console:{info(){}}
};
vm.runInNewContext(source,sandbox,{filename:'assets/sprites/sprite-runtime.js'});
const choose=sandbox.window.NexusSprites.chooseView;
assert.equal(choose(1,0),'side');
assert.equal(choose(-1,0),'side');
assert.equal(choose(0,-1),'side');
assert.equal(choose(0,1),'side');
assert.equal(choose(1,-1),'side');
assert.equal(choose(1,1),'side');
assert.equal(sandbox.window.NexusSprites.resolveView({vy:-1}),'side');
assert.equal(sandbox.window.NexusSprites.resolveView({view:'front_three_quarter'}),'front_three_quarter');
assert.equal(sandbox.window.NexusSprites.resolveView({animation_state:'turning',view:'side',animation_elapsed:.05,turn_target_view:'rear'}),'side');
assert.equal(sandbox.window.NexusSprites.resolveView({animation_state:'turning',view:'side',animation_elapsed:.85,turn_target_view:'rear'}),'rear','turning clip must override stale side orientation');
assert.equal(sandbox.window.NexusSprites.resolveView({animation_state:'turning',animation_elapsed:.45,turn_target_view:'rear'}),'rear_three_quarter');
assert.equal(sandbox.window.NexusSprites.resolveView({animation_state:'turning',animation_elapsed:.85,turn_target_view:'rear'}),'rear');
async function verifyPlantSprites(){
 await new Promise(resolve=>{const original=sandbox.window.dispatchEvent;sandbox.window.dispatchEvent=event=>{original(event);resolve();};});
 const calls=[];
 const ctx={save(){},restore(){},translate(){},rotate(){},scale(){},drawImage(){calls.push('drawImage');}};
 assert.equal(sandbox.window.NexusSprites.drawPlant(ctx,10,100,36,90,1,7,'kelp'),true,'kelp resolves to imported green seaweed sprite');
 assert.equal(sandbox.window.NexusSprites.drawPlant(ctx,20,100,30,60,1,7,'seagrass'),true,'seagrass resolves to imported grass sprite');
 assert.equal(sandbox.window.NexusSprites.drawPlant(ctx,30,100,30,70,1,7,'mangrove'),true,'mangrove resolves to imported background seaweed sprite');
 assert.equal(sandbox.window.NexusSprites.drawPlant(ctx,40,100,30,70,1,7,'coral'),false,'missing coral artwork must not be misrepresented as a coral sprite');
 assert.equal(calls.length,3,'each available flora category draws a real image');
 console.log('Sprite view and flora asset checks passed.');
}
verifyPlantSprites().catch(error=>{console.error(error);process.exitCode=1;});
