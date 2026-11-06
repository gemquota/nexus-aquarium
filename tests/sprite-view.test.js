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
assert.equal(choose(0,-1),'front');
assert.equal(choose(0,1),'rear');
assert.equal(choose(1,-1),'front_three_quarter');
assert.equal(choose(1,1),'rear_three_quarter');
console.log('Sprite view selection checks passed.');
