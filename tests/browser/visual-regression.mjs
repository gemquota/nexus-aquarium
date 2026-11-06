import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseURL = process.env.NEXUS_BASE_URL || 'http://127.0.0.1:4173';
const out = process.env.NEXUS_SCREENSHOT_DIR || 'artifacts/nexus-visual-regression';
const habitats = ['coral_reef','open_ocean','deep_sea','seagrass','kelp_forest','rocky_seabed','sandy_seabed','hydrothermal_vent'];
const zooms = ['overview','home','close'];
const errors = [];
const failedRequests = [];
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
page.on('requestfailed', request => failedRequests.push({url:request.url(),failure:request.failure()?.errorText}));
try {
  await page.goto(baseURL, { waitUntil: 'networkidle', timeout: 60000 });
  await page.locator('#ocean').waitFor({ state: 'visible' });
  await page.waitForTimeout(2500);
  const initial = await page.locator('#population-total').textContent();
  if (!initial || !initial.trim()) throw new Error('Population telemetry did not initialise');
  for (const habitat of habitats) {
    await page.locator('#habitat-select').selectOption(habitat);
    await page.locator('#apply-habitat').click();
    await page.waitForTimeout(350);
    for (const zoom of zooms) {
      if (zoom === 'overview') await page.locator('#zoom-overview').click();
      if (zoom === 'home') await page.locator('#zoom-reset').click();
      if (zoom === 'close') { await page.locator('#zoom-reset').click(); await page.locator('#zoom-in').click(); await page.locator('#zoom-in').click(); }
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(out, habitat + '-' + zoom + '.png'), fullPage: false });
    }
  }
  const report = {url:baseURL,habitats,zooms,population:initial,consoleErrors:errors,failedRequests};
  await fs.writeFile(path.join(out,'report.json'), JSON.stringify(report,null,2));
  if (errors.length || failedRequests.length) throw new Error('Browser diagnostics contain errors; see report.json');
  console.log('Captured ' + habitats.length*zooms.length + ' habitat/zoom screenshots at population ' + initial);
} finally { await browser.close(); }
