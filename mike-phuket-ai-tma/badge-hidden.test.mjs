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

function displayed(body) {
  const dir = mkdtempSync(join(tmpdir(), "hidden-"));
  const page = join(dir, "page.html");
  writeFileSync(
    page,
    `<!doctype html>
<link rel="stylesheet" href="${pathToFileURL(join(root, "styles.css")).href}">
${body}
<script>
  document.documentElement.dataset.shown = getComputedStyle(
    document.getElementById("probe"),
  ).display;
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
  const match = result.stdout.match(/data-shown="([^"]*)"/);
  assert.ok(match, result.stdout);
  return match[1];
}

test("a hidden recommend badge stays hidden when images are display:block", () => {
  assert.equal(
    displayed(`<img id="probe" class="recommend-badge" alt="MIKE рекомендует" hidden>`),
    "none",
  );
});

test("a hidden profile letter stays hidden when the letter is display:grid", () => {
  assert.equal(
    displayed(`<span id="probe" class="profile-letter" hidden>Г</span>`),
    "none",
  );
});
