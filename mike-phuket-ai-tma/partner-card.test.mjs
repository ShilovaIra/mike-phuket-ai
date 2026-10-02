import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));

function chromePath() {
  const candidates = [
    process.env.CHROME_PATH,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "chromium",
  ].filter(Boolean);
  return candidates[0];
}

test("a partner card logo fills the 4:3 frame instead of sitting in a padded mat", () => {
  const dir = mkdtempSync(join(tmpdir(), "partner-card-"));
  const page = join(dir, "page.html");
  const logo =
    "data:image/svg+xml," +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="white"/><circle cx="100" cy="100" r="100" fill="%232f7cf6"/></svg>',
    );
  writeFileSync(
    page,
    `<!doctype html>
<link rel="stylesheet" href="${pathToFileURL(join(root, "styles.css")).href}">
<div class="rec-row" style="width:390px">
  <a class="partner-tile" href="#partner">
    <span class="partner-mark" id="mark"><img id="logo" alt="" src="${logo}"></span>
    <span class="rec-title">Mike eSIM</span>
  </a>
  <a class="partner-tile" href="#partner">
    <span class="partner-mark" id="fallback">M</span>
  </a>
</div>
<script>
  addEventListener("load", () => {
    const markEl = document.getElementById("mark");
    const mark = markEl.getBoundingClientRect();
    const img = document.getElementById("logo").getBoundingClientRect();
    const logoStyle = getComputedStyle(document.getElementById("logo"));
    const markStyle = getComputedStyle(markEl);
    const fallback = document.getElementById("fallback").getBoundingClientRect();
    document.documentElement.dataset.metrics = JSON.stringify({
      markW: mark.width,
      markH: mark.height,
      contentW: markEl.clientWidth,
      contentH: markEl.clientHeight,
      imgW: img.width,
      imgH: img.height,
      imgTop: img.top - mark.top,
      imgLeft: img.left - mark.left,
      pad: logoStyle.paddingTop,
      fit: logoStyle.objectFit,
      bg: markStyle.backgroundColor,
      fallbackH: fallback.height,
    });
  });
</script>
`,
  );

  const result = spawnSync(
    chromePath(),
    [
      "--headless=new",
      "--disable-gpu",
      "--no-first-run",
      "--virtual-time-budget=2000",
      "--dump-dom",
      pathToFileURL(page).href,
    ],
    { encoding: "utf8" },
  );

  assert.equal(result.status, 0, result.stderr);
  const match = result.stdout.match(/data-metrics="([^"]*)"/);
  assert.ok(match, result.stdout);
  const metrics = JSON.parse(match[1].replaceAll("&quot;", '"'));

  assert.ok(metrics.markW > 100, `card collapsed: ${JSON.stringify(metrics)}`);
  assert.ok(
    Math.abs(metrics.markW / metrics.markH - 4 / 3) < 0.05,
    `card should stay 4:3 so it lines up with place cards: ${JSON.stringify(metrics)}`,
  );
  assert.equal(metrics.pad, "0px", `logo is inset by padding: ${JSON.stringify(metrics)}`);
  assert.equal(metrics.fit, "contain");
  assert.equal(metrics.bg, "rgb(255, 255, 255)");
  assert.ok(
    Math.abs(metrics.imgW - metrics.contentW) < 1 && Math.abs(metrics.imgH - metrics.contentH) < 1,
    `logo box does not fill the card: ${JSON.stringify(metrics)}`,
  );
  assert.ok(
    Math.abs(metrics.imgTop - 1) < 1 && Math.abs(metrics.imgLeft - 1) < 1,
    `logo is offset inside the card: ${JSON.stringify(metrics)}`,
  );
  assert.ok(metrics.fallbackH > 40, `missing-logo tile collapsed: ${JSON.stringify(metrics)}`);
});
