// GitHub social preview (1280×640) → assets/social-preview.png
//   node scripts/demo/social_preview.mjs   (run from a folder with playwright installed)
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(path.join(process.cwd(), "x.js"));
const { chromium } = require("playwright");
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const font = (f) => "data:font/woff2;base64," +
  fs.readFileSync(path.join(root, "site/fonts", f)).toString("base64");

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:Martian;src:url(${font("martian-mono-latin-700-normal.woff2")});font-weight:700}
@font-face{font-family:Martian;src:url(${font("martian-mono-latin-500-normal.woff2")});font-weight:500}
@font-face{font-family:Plex;src:url(${font("ibm-plex-sans-latin-400-normal.woff2")})}
@font-face{font-family:PlexMono;src:url(${font("ibm-plex-mono-latin-400-normal.woff2")})}
*{box-sizing:border-box}body{margin:0;width:1280px;height:640px;background:#edefec;color:#14201a;
 font-family:Plex;display:flex;align-items:center;padding:0 64px;gap:56px;overflow:hidden}
.l{flex:1}.brand{display:flex;align-items:center;gap:16px;font:700 34px Martian}
h1{font:700 50px/1.12 Martian;margin:70px 0 28px;letter-spacing:-1px}
.pts{font-size:22px;line-height:1.7;color:#3b4a42}.pts b{color:#14201a;font-weight:400}
.foot{margin-top:40px;font-size:20px;color:#5b6a62}
.t{width:560px;background:#000;border-radius:22px;padding:30px 32px;font:20px/1.75 PlexMono;color:#ececec}
.d{color:#8b8b8b}.g{color:#3ddc84}.w{color:#f5a35c}
</style></head><body><div class="l"><div class="brand">
<svg viewBox="0 0 32 32" width="52" height="52"><rect width="32" height="32" rx="7" fill="#14201A"/><circle cx="11" cy="16" r="5" fill="none" stroke="#3DDC84" stroke-width="3"/><path d="M16 16h11M22 16v4M26 16v3" stroke="#3DDC84" stroke-width="3" stroke-linecap="round"/></svg>
kunji</div>
<h1>Every AI model.<br>Your own keys.<br>One terminal.</h1>
<div class="pts">See what every answer costs · daily budgets<br>Switch models mid-chat · compare side by side</div>
<div class="foot">Free and open source · pip install kunji</div></div>
<div class="t"><div><span class="d">$</span> kunji chat</div><br>
<div><span class="g">›</span> explain recursion in one line</div>
<div>&nbsp;&nbsp;A function that calls itself on a</div>
<div>&nbsp;&nbsp;smaller piece of the problem.</div>
<div class="d">&nbsp;&nbsp;claude-sonnet-4-5 · 52 tok · $0.0006</div><br>
<div><span class="g">›</span> /model groq:llama-3.3-70b</div>
<div><span class="g">✓</span> Switched &nbsp;<span class="d">conversation kept</span></div><br>
<div><span class="w">!</span> 80% of today's budget used: $1.64 / $2</div>
</div></body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 640 }, deviceScaleFactor: 1 });
await page.setContent(html);
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: path.join(root, "assets/social-preview.png") });
await browser.close();
