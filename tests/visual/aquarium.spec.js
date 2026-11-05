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
    organisms: window.NexusDebug.data.organisms,
    sprites: window.NexusDebug.sprites,
    frame: window.NexusDebug.capture()
  }));
  expect(initial.organisms.length).toBe(220);
  expect(new Set(initial.organisms.map(o => o.species)).size).toBeGreaterThanOrEqual(10);
  expect(initial.sprites.loaded).toBeGreaterThan(0);
  expect(initial.sprites.failed).toBe(0);

  const waterline = initial.world.h * 0.78;
  const underwater = initial.organisms.filter(o => o.y >= waterline && o.y <= initial.world.h);
  expect(underwater.length / initial.organisms.length).toBeGreaterThan(0.98);

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
