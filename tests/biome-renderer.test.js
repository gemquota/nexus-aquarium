'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('assets/biome-renderer.js', 'utf8');
const sandbox = { window: {}, Math, Map, Number };
vm.runInNewContext(source, sandbox, { filename: 'assets/biome-renderer.js' });

const renderer = sandbox.window.NexusBiomeRenderer;
assert.ok(renderer && typeof renderer.draw === 'function', 'renderer exports draw()');
const habitats = Object.keys(renderer.palettes);
assert.equal(habitats.length, 13, 'all 13 declared habitats are available');

function renderCounts(habitat) {
  const counts = Object.create(null);
  const ctx = new Proxy({}, {
    get(target, key) {
      if (key in target) return target[key];
      if (typeof key === 'string') return (...args) => { counts[key] = (counts[key] || 0) + 1; };
      return undefined;
    },
    set(target, key, value) { target[key] = value; return true; }
  });
  renderer.draw(ctx, {
    ox: 0, oy: 0, sx: 0.04, sy: 0.04,
    width: 1200, height: 400,
    worldWidth: 30000, worldHeight: 10000,
    bathymetry: x => 9000 + Math.sin(x / 1500) * 120,
    time: 12.5, zoom: 1.2, defaultHabitat: habitat
  });
  return counts;
}

for (const habitat of habitats) {
  const first = renderCounts(habitat);
  const second = renderCounts(habitat);
  assert.deepEqual(first, second, habitat + ': deterministic draw-call profile');
  assert.ok((first.beginPath || 0) > 0, habitat + ': emits visible geometry');
  assert.ok((first.fill || 0) + (first.stroke || 0) > 0, habitat + ': paints scenery');
}

const reef = renderCounts('coral_reef');
const openOcean = renderCounts('open_ocean');
const kelp = renderCounts('kelp_forest');
const seagrass = renderCounts('seagrass');
assert.ok((reef.stroke || 0) > (openOcean.stroke || 0), 'reef growth exceeds sparse open-ocean growth');
assert.ok((kelp.ellipse || 0) > 0, 'kelp blades are rendered');
assert.ok((seagrass.stroke || 0) > 0, 'seagrass blades are rendered');

const emptyCounts = Object.create(null);
const emptyCtx = new Proxy({}, { get: () => () => { throw new Error('draw called without valid scale'); }, set: () => true });
renderer.draw(emptyCtx, { sx: 0, sy: 0, bathymetry: () => 0 });
console.log('Biome renderer regression checks passed: ' + habitats.length + ' habitats, deterministic geometry, habitat-specific vegetation, and invalid-scale guard.');
