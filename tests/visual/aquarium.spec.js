import { test, expect } from '@playwright/test';

test('aquarium visual scene renders, moves, and remains legible across zoom levels', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.setViewportSize({ width: 1280, height: 820 });
  await page.goto('/');
  await page.waitForFunction(() => window.NexusDebug && window.NexusSprites?.status.assets > 0);
  await page.waitForFunction(() => window.NexusSprites.status.loaded > 0);
  await page.waitForTimeout(700);

  const initial = await page.evaluate(() => ({
    world: window.NexusDebug.world,
    waterline: window.NexusDebug.data.world.waterline,
    organisms: window.NexusDebug.data.organisms,
    sprites: window.NexusDebug.sprites,
    frame: window.NexusDebug.capture()
  }));
  expect(initial.organisms.length).toBe(220);
  expect(new Set(initial.organisms.map(o => o.species)).size).toBeGreaterThanOrEqual(10);
  expect(initial.sprites.loaded).toBeGreaterThan(0);
  expect(initial.sprites.failed).toBe(0);

  const waterDepth = initial.world.h - initial.waterline;
  const depths = initial.organisms.map(o => (o.y - initial.waterline) / waterDepth);
  expect(depths.every(d => d >= 0 && d <= 1)).toBeTruthy();
  const occupiedDepthBands = new Set(depths.map(d => Math.min(4, Math.floor(d * 5))));
  expect(occupiedDepthBands.size).toBeGreaterThanOrEqual(4);
  expect(initial.organisms.filter(o => o.species === 'reef_fish').length).toBeGreaterThanOrEqual(40);
  expect(initial.organisms.filter(o => o.species === 'lanternfish').length).toBeGreaterThanOrEqual(15);

  await page.waitForTimeout(900);
  const laterFrame = await page.evaluate(() => window.NexusDebug.capture());
  expect(laterFrame).not.toBe(initial.frame);

  for (const [zoom, name] of [[0.25, 'overview'], [6, 'default'], [24, 'close']]) {
    await page.evaluate(value => window.NexusDebug.setZoom(value), zoom);
    await page.waitForTimeout(120);
    await page.screenshot({ path: `test-results/visual/${name}.png`, fullPage: false });
    const state = await page.evaluate(() => ({
      zoom: window.NexusDebug.camera.zoom,
      width: window.NexusDebug.canvas.width,
      height: window.NexusDebug.canvas.height
    }));
    expect(state.zoom).toBe(zoom);
    expect(state.width).toBeGreaterThan(0);
    expect(state.height).toBeGreaterThan(0);
  }

  expect(pageErrors).toEqual([]);
});
