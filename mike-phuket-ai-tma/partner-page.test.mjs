import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
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

test("the partner page logo is the cover, not an avatar inside the back strip", () => {
  const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");
  const partner = html.slice(html.indexOf('id="partner"'), html.indexOf('id="route"'));
  const heroEnd = partner.indexOf("</header>");
  const logoAt = partner.indexOf("data-partner-logo");
  const bodyAt = partner.indexOf('class="place-body"');
  assert.ok(heroEnd !== -1 && logoAt !== -1 && bodyAt !== -1);
  assert.ok(heroEnd < logoAt && logoAt < bodyAt, "the logo sits between the back strip and the sheet");
});

test("a partner logo fills the 248px cover without padding", () => {
  const dir = mkdtempSync(join(tmpdir(), "partner-page-"));
  const page = join(dir, "page.html");
  const logo =
    "data:image/svg+xml," +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="white"/><circle cx="100" cy="100" r="80" fill="%232f7cf6"/></svg>',
    );
  writeFileSync(
    page,
    `<!doctype html>
<link rel="stylesheet" href="${pathToFileURL(join(root, "styles.css")).href}">
<article class="place" style="width:390px">
  <header class="partner-hero"><a class="icon-btn icon-ghost" href="#home">back</a></header>
  <div class="partner-logo" id="logo"><img id="mark" alt="" src="${logo}"></div>
</article>
<script>
  addEventListener("load", () => {
    const logoEl = document.getElementById("logo");
    const box = logoEl.getBoundingClientRect();
    const img = document.getElementById("mark").getBoundingClientRect();
    const imgStyle = getComputedStyle(document.getElementById("mark"));
    document.documentElement.dataset.metrics = JSON.stringify({
      boxW: box.width,
      boxH: box.height,
      imgW: img.width,
      imgH: img.height,
      imgTop: img.top - box.top,
      imgLeft: img.left - box.left,
      pad: imgStyle.paddingTop,
      fit: imgStyle.objectFit,
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
      "--window-size=390,844",
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

  assert.ok(Math.abs(metrics.boxW - 390) < 1, `cover is not full width: ${JSON.stringify(metrics)}`);
  assert.ok(Math.abs(metrics.boxH - 248) < 1, `cover is not the place photo height: ${JSON.stringify(metrics)}`);
  assert.equal(metrics.pad, "0px", `logo is inset by padding: ${JSON.stringify(metrics)}`);
  assert.equal(metrics.fit, "contain");
  assert.ok(
    Math.abs(metrics.imgW - metrics.boxW) < 1 && Math.abs(metrics.imgH - metrics.boxH) < 1,
    `logo does not fill the cover: ${JSON.stringify(metrics)}`,
  );
  assert.ok(
    Math.abs(metrics.imgTop) < 1 && Math.abs(metrics.imgLeft) < 1,
    `logo is offset inside the cover: ${JSON.stringify(metrics)}`,
  );
});
