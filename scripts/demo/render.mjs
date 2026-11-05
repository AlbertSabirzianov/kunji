// Render an asciicast v2 file to PNG frames with xterm.js in headless Chromium.
//
//   node scripts/demo/render.mjs in.cast out_dir [fps] [scale] [title]
//
// Needs `npm i playwright @xterm/xterm@5.5.0 @xterm/addon-canvas@0.7.0` in the
// current folder (or NODE_PATH). Frames are rendered at fixed time steps, so the
// output is identical on every run. Long idle gaps are shortened to MAX_IDLE.
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";

const require = createRequire(path.join(process.cwd(), "x.js"));
const { chromium } = require("playwright");
const [castPath, outDir, fpsArg = "12", scaleArg = "1", title = "kunji"] = process.argv.slice(2);
const fps = Number(fpsArg), scale = Number(scaleArg), MAX_IDLE = 2.5, END_HOLD = 3.0;

const lines = fs.readFileSync(castPath, "utf8").trim().split("\n");
const header = JSON.parse(lines[0]);
let events = lines.slice(1).map((l) => JSON.parse(l));
// Compress idle time.
let shift = 0, prev = 0;
events = events.map(([t, k, d]) => {
  const gap = t - prev;
  if (gap > MAX_IDLE) shift += gap - MAX_IDLE;
  prev = t;
  return [t - shift, k, d];
});
const duration = events.at(-1)[0] + END_HOLD;

const xtermJs = require.resolve("@xterm/xterm/lib/xterm.js");
const xtermCss = path.join(path.dirname(xtermJs), "../css/xterm.css");
const canvasJs = require.resolve("@xterm/addon-canvas/lib/addon-canvas.js");

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
${fs.readFileSync(xtermCss, "utf8")}
html,body{margin:0;background:transparent}
#win{display:inline-block;margin:28px;background:#0d0d0d;border:1px solid #2a2a2a;
  border-radius:12px;overflow:hidden;box-shadow:0 18px 50px rgba(0,0,0,.45)}
#bar{height:36px;display:flex;align-items:center;gap:8px;padding:0 14px;background:#161616;
  border-bottom:1px solid #232323;font:500 13px "JetBrains Mono",monospace;color:#8b8b8b}
.dot{width:12px;height:12px;border-radius:50%}
#bar span.t{flex:1;text-align:center;margin-right:52px}
#term{padding:14px 16px 16px}
.xterm .xterm-viewport{overflow:hidden!important;background:#0d0d0d!important}
</style></head><body><div id="win"><div id="bar"><div class="dot" style="background:#ff5f57"></div>
<div class="dot" style="background:#febc2e"></div><div class="dot" style="background:#28c840"></div>
<span class="t">${title}</span></div><div id="term"></div></div>
<script>${fs.readFileSync(xtermJs, "utf8")}</script>
<script>${fs.readFileSync(canvasJs, "utf8")}</script>
</body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: scale, viewport: { width: 1400, height: 1000 } });
await page.setContent(html);
await page.evaluate(async ({ cols, rows }) => {
  await document.fonts.load('15px "JetBrains Mono"');
  const term = new Terminal({
    cols, rows, fontFamily: '"JetBrains Mono", "DejaVu Sans Mono", monospace', fontSize: 15,
    lineHeight: 1.18, cursorBlink: false, allowProposedApi: true, customGlyphs: true,
    theme: { background: "#0d0d0d", foreground: "#e6e6e6", cursor: "#e6e6e6",
             selectionBackground: "#333333" },
  });
  term.loadAddon(new CanvasAddon.CanvasAddon());
  term.open(document.getElementById("term"));
  window.term = term;
}, { cols: header.width, rows: header.height });

fs.mkdirSync(outDir, { recursive: true });
const win = await page.$("#win");
let i = 0, frame = 0;
for (let t = 0; t <= duration; t += 1 / fps) {
  let chunk = "";
  while (i < events.length && events[i][0] <= t) chunk += events[i++][2];
  if (chunk) await page.evaluate((c) => new Promise((r) => window.term.write(c, r)), chunk);
  await win.screenshot({ path: path.join(outDir, `f${String(frame++).padStart(5, "0")}.png`),
                         omitBackground: true });
}
await browser.close();
console.log(`${frame} frames, ${duration.toFixed(1)} s`);
