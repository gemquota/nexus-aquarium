'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {URL}=require('node:url');
const source=fs.readFileSync('assets/sprites/sprite-runtime.js','utf8');
const manifest=JSON.parse(fs.readFileSync('assets/sprites/runtime-manifest.json','utf8'));
assert.ok(!manifest.assets.some(a=>a.kind==='creature'&&a.species==='generic'),'legacy generic fish are not runtime assets');
assert.ok(!manifest.assets.some(a=>a.source_pack==='kenney-fish'||a.source_pack==='inmenus-bird-cc0'),'legacy visual packs are retired from runtime');
const sandbox={
 window:{dispatchEvent(){}},
 document:{currentScript:{src:'https://example.test/assets/sprites/sprite-runtime.js'}},
 fetch:async()=>({ok:true,json:async()=>({assets:[
  {kind:'plant',species:'kelp',filename:'kelp_giant.svg',src:'/assets/sprites/flora/kelp_giant.svg',frames:1},
  {kind:'plant',species:'seagrass',filename:'seagrass_tuft.svg',src:'/assets/sprites/flora/seagrass_tuft.svg',frames:1},
  {kind:'plant',species:'mangrove',filename:'mangrove_roots.svg',src:'/assets/sprites/flora/mangrove_roots.svg',frames:1},
  {kind:'plant',species:'coral',filename:'coral_staghorn.svg',src:'/assets/sprites/flora/coral_staghorn.svg',frames:1},
  {kind:'prop',species:'rock',filename:'reef_rock.svg',src:'/assets/sprites/props/reef_rock.svg',frames:1},
  {kind:'bird',species:'generic',filename:'seagull.svg',src:'/assets/sprites/birds/seagull.svg',frames:1},
  {kind:'creature',species:'yellow_tang',view:'side',filename:'side.png',src:'/assets/sprites/generated/turnarounds/yellow_tang/side.png',frames:1,render_width:3.8,render_height:2.8}
 ]})}),
 Image:class FakeImage{constructor(){this.naturalWidth=64;this.naturalHeight=64;this.decoding='';}set src(value){this._src=value;this.onload?.();}get src(){return this._src;}},
 CustomEvent:class CustomEvent{},URL,performance:{now:()=>1},console:{info(){}}
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
assert.equal(sandbox.window.NexusSprites.resolveView({animation_state:'turning',view:'side',animation_elapsed:.85,turn_target_view:'rear'}),'rear');
assert.equal(sandbox.window.NexusSprites.resolveView({animation_state:'turning',animation_elapsed:.45,turn_target_view:'rear'}),'rear_three_quarter');
async function verifyUnifiedSprites(){
 await new Promise(resolve=>{sandbox.window.dispatchEvent=resolve;});
 const calls=[];
 const ctx={save(){},restore(){},translate(){},rotate(){},scale(){},drawImage(){calls.push('drawImage');}};
 for(const category of ['kelp','seagrass','mangrove','coral']){
  assert.equal(sandbox.window.NexusSprites.drawPlant(ctx,10,100,36,90,1,7,category),true,category+' resolves to a unified SVG sprite');
 }
 assert.equal(sandbox.window.NexusSprites.drawProp(ctx,'rock',20,100,80,45,1,1),true,'rock prop resolves to unified art');
 assert.equal(sandbox.window.NexusSprites.drawBird(ctx,{species:'seagull',vx:1},20,20,{time:1,index:1}),true,'seabird resolves to unified art');
 assert.equal(sandbox.window.NexusSprites.drawOrganism(ctx,{species:'reef_fish',vx:1,vy:0,id:1},30,30,{time:1}),true,'unrepresented fish species use a standard-style production fallback');
 assert.equal(calls.length,7,'each test path draws a real sprite image');
 console.log('Unified sprite runtime checks passed.');
}
verifyUnifiedSprites().catch(error=>{console.error(error);process.exitCode=1;});
