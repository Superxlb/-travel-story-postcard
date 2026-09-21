#!/usr/bin/env node
// Optional PNG export: Node.js + Playwright + a local Chromium-family browser.
const fs = require('node:fs/promises');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { createHash } = require('node:crypto');

async function exportPostcard(options) {
  const html = path.resolve(options.html);
  const outputDir = path.resolve(options.outputDir);
  const width = options.width === undefined ? 1440 : Number(options.width);
  const scale = options.scale === undefined ? 2 : Number(options.scale);
  const prefix = options.prefix || 'postcard';
  if (!Number.isInteger(width) || width < 320 || width > 3840) throw new Error('width must be an integer from 320 to 3840.');
  if (!Number.isFinite(scale) || scale < 1 || scale > 3) throw new Error('scale must be between 1 and 3.');
  if (!/^[\p{L}\p{N}_-]+$/u.test(prefix)) throw new Error('prefix may contain letters, numbers, underscores, and hyphens only.');
  if (path.extname(html).toLowerCase() !== '.html') throw new Error('Use a local .html file.');
  const source = await fs.readFile(html);
  if (/\{\{[A-Z_]+\}\}/.test(source.toString('utf8'))) throw new Error('HTML still contains template placeholders.');
  const names = ['front', 'back', 'overview'].map(side => `${prefix}-${side}.png`);
  const reportName = `${prefix}-export.json`;
  for (const name of [...names, reportName]) {
    try { await fs.access(path.join(outputDir, name)); }
    catch (error) { if (error.code === 'ENOENT') continue; throw error; }
    throw new Error(`Output already exists: ${name}. Choose a new prefix or directory.`);
  }
  let chromium;
  try { ({ chromium } = require('playwright')); }
  catch (_) { throw new Error('PNG export needs Playwright. See references/png-export.md; HTML remains usable.'); }
  const launch = { headless: true };
  if (options.browser) launch.executablePath = path.resolve(options.browser);
  const browser = await chromium.launch(launch);
  try {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, deviceScaleFactor: scale, javaScriptEnabled: false });
    const page = await context.newPage();
    const remote = [];
    await page.route(/^https?:\/\//, route => { remote.push(route.request().url()); return route.abort(); });
    await page.goto(pathToFileURL(html).href, { waitUntil: 'load', timeout: 30000 });
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all(Array.from(document.images, image => image.decode()));
    });
    if (remote.length) throw new Error('HTML requests external resources; embed or bundle them before export.');
    const problems = await page.evaluate(() => ({
      scripts: document.querySelectorAll('script').length,
      brokenImage: Array.from(document.images).some(i => !i.complete || !i.naturalWidth),
      overflow: document.documentElement.scrollWidth > innerWidth + 1,
    }));
    if (problems.scripts || problems.brokenImage || problems.overflow) throw new Error(`HTML check failed: ${JSON.stringify(problems)}`);
    const selectors = [
      '[data-postcard-side="front"], [aria-label="明信片正面"]',
      '[data-postcard-side="back"], [aria-label="明信片背面"]',
      '[data-postcard-overview], main',
    ];
    const buffers = [];
    for (const selector of selectors) {
      const region = page.locator(selector);
      if (await region.count() !== 1) throw new Error(`Expected exactly one export region: ${selector}`);
      if (!await region.isVisible()) throw new Error(`Export region is hidden: ${selector}`);
      const clipped = await region.evaluate(element => [element, ...element.querySelectorAll('*')].some(e => {
        if (getComputedStyle(e).display === 'inline' || e.clientWidth === 0) return false;
        return e.scrollWidth > e.clientWidth + 2 || e.scrollHeight > e.clientHeight + 2;
      }));
      if (clipped) throw new Error('An export region has overflowing content. Fix its layout before exporting.');
      const bounds = await region.boundingBox();
      if (!bounds || bounds.width < 1 || bounds.height < 1 || bounds.height * scale > 16000) throw new Error('Export region has invalid dimensions or is too tall. Adjust the layout.');
      buffers.push(await region.screenshot({ type: 'png', animations: 'disabled', caret: 'hide', scale: 'device' }));
    }
    const report = {
      source: path.basename(html),
      source_sha256: createHash('sha256').update(source).digest('hex'),
      viewport_width: width, scale, browser: await browser.version(), external_requests: 0,
      files: buffers.map((buffer, i) => ({ name: names[i], width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) })),
    };
    await fs.mkdir(outputDir, { recursive: true });
    for (let i = 0; i < buffers.length; i++) await fs.writeFile(path.join(outputDir, names[i]), buffers[i], { flag: 'wx' });
    await fs.writeFile(path.join(outputDir, reportName), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
    return report;
  } finally { await browser.close(); }
}

async function main() {
  const args = process.argv.slice(2);
  if (!args.length || args.includes('--help')) {
    console.log('node scripts/export_postcard.cjs --html finished.html --output-dir output [--prefix postcard] [--width 1440] [--scale 2] [--browser /path/to/chrome]');
    return;
  }
  const keys = { '--html': 'html', '--output-dir': 'outputDir', '--prefix': 'prefix', '--width': 'width', '--scale': 'scale', '--browser': 'browser' };
  const options = {};
  for (let i = 0; i < args.length; i += 2) {
    if (!keys[args[i]] || args[i + 1] === undefined) throw new Error('Unknown option or missing value. Use --help.');
    options[keys[args[i]]] = args[i + 1];
  }
  if (!options.html || !options.outputDir) throw new Error('--html and --output-dir are required.');
  console.log(JSON.stringify(await exportPostcard(options), null, 2));
}

module.exports = { exportPostcard };
if (require.main === module) main().catch(error => { console.error('Cannot export PNG: ' + error.message); process.exitCode = 1; });
