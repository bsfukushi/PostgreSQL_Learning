// Mermaid のコードを、ビルド時に SVG へ変換する。
// 使い方: node render_mermaid.mjs <入力JSON> <出力JSON>
//   入力: {"キー": "mermaidコード", ...}  出力: {"キー": "<svg>...</svg>", ...}
// 目的: 配布したHTMLを、インターネットなし・外部ライブラリなしで表示できるようにする。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const [, , inFile, outFile] = process.argv;
const diagrams = JSON.parse(readFileSync(inFile, 'utf8'));
const mermaidJs = readFileSync(path.join(here, 'node_modules/mermaid/dist/mermaid.min.js'), 'utf8');

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium',
});
const page = await browser.newPage();
await page.setContent('<!doctype html><html><head><meta charset="utf-8"></head><body></body></html>');
await page.addScriptTag({ content: mermaidJs });

const out = {};
for (const [key, code] of Object.entries(diagrams)) {
  out[key] = await page.evaluate(async ({ key, code }) => {
    window.mermaid.initialize({
      startOnLoad: false,
      theme: 'neutral',
      securityLevel: 'strict',
      fontFamily: '"BIZ UDPGothic", "Hiragino Sans", "Yu Gothic UI", "Noto Sans JP", sans-serif',
      er: { useMaxWidth: true },
    });
    const { svg } = await window.mermaid.render('mmd-' + key, code);
    return svg;
  }, { key, code });
}
await browser.close();
writeFileSync(outFile, JSON.stringify(out));
console.log(`rendered ${Object.keys(out).length} diagram(s)`);
