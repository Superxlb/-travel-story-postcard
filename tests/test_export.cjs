// Optional browser integration tests: node tests/test_export.cjs /actual/browser/path
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { createHash } = require('node:crypto');
const { exportPostcard } = require('../scripts/export_postcard.cjs');

(async () => {
  const temp = await fs.mkdtemp(path.join(os.tmpdir(), 'postcard-export-test-'));
  const source = path.resolve(__dirname, '../demo/photo-adjusted-postcard.html');
  const browser = process.argv[2];
  const options = { html: source, outputDir: path.join(temp, 'valid'), browser, scale: 2 };
  const report = await exportPostcard(options);
  assert.equal(report.source_sha256, createHash('sha256').update(await fs.readFile(source)).digest('hex'));
  assert.equal(report.files.length, 3);
  for (const file of report.files) {
    const png = await fs.readFile(path.join(options.outputDir, file.name));
    assert.equal(png.subarray(1, 4).toString(), 'PNG');
    assert.ok(file.width > 1000 && file.height > 100);
  }
  console.log('PASS: three real PNGs, dimensions, and matching source hash');
  await assert.rejects(exportPostcard(options), /already exists/);
  console.log('PASS: no overwrite');
  const original = await fs.readFile(source, 'utf8');
  for (const [name, html, pattern] of [
    ['missing-region', original.replace('aria-label="明信片背面"', 'aria-label="unknown"').replace('data-postcard-side="back"', ''), /exactly one export region/],
    ['broken-image', original.replace(/src="data:[^"]+"/, 'src="missing.jpg"'), /decode|image|encoding/i],
    ['external', original.replace('</head>', '<link rel="stylesheet" href="https://example.invalid/style.css"></head>'), /external resources/],
    ['overflow', original.replace('</head>', '<style>.story{height:10px;overflow:hidden}</style></head>'), /overflowing content/],
  ]) {
    const input = path.join(temp, name + '.html');
    const outputDir = path.join(temp, name);
    await fs.writeFile(input, html);
    await assert.rejects(exportPostcard({ html: input, outputDir, browser }), pattern);
    await assert.rejects(fs.access(outputDir));
    console.log('PASS: reject ' + name + ' without exporting files');
  }
  console.log('All 6 export checks passed. Temporary artifacts: ' + temp);
})().catch(error => { console.error(error); process.exitCode = 1; });
