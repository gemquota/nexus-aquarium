import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import { PNG } from 'pngjs';

const baseURL = process.env.NEXUS_BASE_URL || 'http://127.0.0.1:4173';
const out = process.env.NEXUS_SCREENSHOT_DIR || 'artifacts/nexus-visual-regression';
const habitats = ['coral_reef','open_ocean','deep_sea','seagrass','kelp_forest','rocky_seabed','sandy_seabed','hydrothermal_vent'];
const zooms = ['overview','home','close'];
const populations = [50,220,400];
const behaviours = ['idle','swim','turning','feeding','hunting','dying'];
const errors = [];
const failedRequests = [];
const spriteFailures = [];
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
page.on('requestfailed', request => failedRequests.push({url:request.url(),failure:request.failure()?.errorText}));
async function waitForReady() {
  await page.locator('#ocean').waitFor({ state: 'visible' });
  await page.waitForFunction(() => Boolean(window.NexusVisualTest && window.NexusSprites));
  await page.waitForFunction(() => window.NexusSprites.status.loaded === window.NexusSprites.status.assets || window.NexusSprites.status.failed > 0, null, { timeout: 45000 });
  await page.evaluate(() => window.NexusVisualTest.pause());
  await page.addStyleTag({content:'*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}'});
  await page.evaluate(() => document.fonts.ready.then(() => true));
  await page.waitForTimeout(500);
}
async function setZoom(zoom) {
  if (zoom === 'overview') await page.locator('#zoom-overview').click();
  if (zoom === 'home') await page.locator('#zoom-reset').click();
  if (zoom === 'close') {
    await page.locator('#zoom-reset').click();
    await page.locator('#zoom-in').click();
    await page.locator('#zoom-in').click();
  }
  await page.waitForTimeout(250);
}
function changedPixelRatio(a,b) {
  const x=PNG.sync.read(a), y=PNG.sync.read(b);
  if(x.width!==y.width||x.height!==y.height) return 1;
  let changed=0,total=x.width*x.height;
  for(let i=0;i<x.data.length;i+=4) {
    if(Math.max(Math.abs(x.data[i]-y.data[i]),Math.abs(x.data[i+1]-y.data[i+1]),Math.abs(x.data[i+2]-y.data[i+2]),Math.abs(x.data[i+3]-y.data[i+3]))>8) changed++;
  }
  return changed/total;
}
try {
  const matrix=[];
  const benchmarks=[];
  for (const population of populations) {
    await page.goto(baseURL+'?visual-regression=1&freeze=1&population='+population, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await waitForReady();
    const actual=await page.evaluate(()=>window.NexusVisualTest.getPopulation());
    if(actual!==population) throw new Error('Population fixture mismatch: expected '+population+', received '+actual);
    for (const habitat of habitats) {
      await page.locator('#habitat-select').selectOption(habitat);
      await page.locator('#apply-habitat').click();
      await page.waitForTimeout(250);
      for (const zoom of zooms) {
        await setZoom(zoom);
        const name=population+'-'+habitat+'-'+zoom+'.png';
        const first=await page.screenshot({path:path.join(out,name),fullPage:false});
        const repeat=await page.screenshot();
        const diff=changedPixelRatio(first,repeat);
        if(diff>0.001) throw new Error('Non-deterministic capture '+name+' changed '+(diff*100).toFixed(3)+'% of pixels');
        matrix.push({population,habitat,zoom,file:name,pixelDiff:diff});
      }
    }
    benchmarks.push({population,...await page.evaluate(()=>window.NexusVisualTest.getPerf())});
    const status=await page.evaluate(()=>window.NexusSprites.status);
    if(status.failed) spriteFailures.push({population,...status});
  }
  await page.goto(baseURL+'?visual-regression=1&freeze=1&population=16', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await waitForReady();
  await page.evaluate(()=>window.NexusVisualTest.setPopulation(16));
  for(const behaviour of behaviours) {
    await page.evaluate(state=>window.NexusVisualTest.setBehaviour(state),behaviour);
    const file='behaviour-'+behaviour+'.png';
    await page.screenshot({path:path.join(out,file),fullPage:false});
    matrix.push({population:16,behaviour,file});
  }
  const report={url:baseURL,viewport:{width:1440,height:1000},habitats,zooms,populations,behaviours,captures:matrix.length,matrix,benchmarks,consoleErrors:errors,failedRequests,spriteFailures};
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));
  if(errors.length||failedRequests.length||spriteFailures.length) throw new Error('Browser diagnostics contain errors; see report.json');
  console.log('Captured '+matrix.length+' deterministic habitat/population/zoom and behaviour screenshots.');
} finally { await browser.close(); }
