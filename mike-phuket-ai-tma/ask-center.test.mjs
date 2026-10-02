import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));

function chromePath() {
  return (
    process.env.CHROME_PATH ||
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  );
}

test("the ask button is inset equally on both sides", () => {
  const dir = mkdtempSync(join(tmpdir(), "ask-center-"));
  const page = join(dir, "page.html");
  writeFileSync(
    page,
    `<!doctype html>
<link rel="stylesheet" href="${pathToFileURL(join(root, "styles.css")).href}">
<div class="device">
  <section class="screen screen-home" id="home" style="display:flex">
    <div class="dock">
      <button class="ask" type="button">Спросите Майка о Пхукете</button>
    </div>
  </section>
</div>
<script>
  const screen = document.querySelector(".screen").getBoundingClientRect();
  const ask = document.querySelector(".ask").getBoundingClientRect();
  const left = Math.round(ask.left - screen.left);
  const right = Math.round(screen.right - ask.right);
  document.documentElement.dataset.askInset = left + "," + right;
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
  const match = result.stdout.match(/data-ask-inset="([^"]*)"/);
  assert.ok(match, result.stdout);
  const [left, right] = match[1].split(",").map(Number);
  assert.equal(left, right, `ask button insets left ${left}px, right ${right}px`);
  assert.ok(left >= 0, `ask button overflows the screen by ${-left}px`);
});
