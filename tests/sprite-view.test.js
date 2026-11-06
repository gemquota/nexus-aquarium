'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {URL}=require('node:url');
const source=fs.readFileSync('assets/sprites/sprite-runtime.js','utf8');
const sandbox={
 window:{dispatchEvent(){}},
 document:{currentScript:{src:'https://example.test/assets/sprites/sprite-runtime.js'}},
 fetch:async()=>({ok:true,json:async()=>({assets:[]})}),
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
assert.equal(sandbox.window.NexusSprites.resolveView({animation_state:'turning',animation_elapsed:.05,turn_target_view:'rear'}),'side');
assert.equal(sandbox.window.NexusSprites.resolveView({animation_state:'turning',animation_elapsed:.45,turn_target_view:'rear'}),'rear_three_quarter');
assert.equal(sandbox.window.NexusSprites.resolveView({animation_state:'turning',animation_elapsed:.85,turn_target_view:'rear'}),'rear');
console.log('Sprite view selection checks passed.');
