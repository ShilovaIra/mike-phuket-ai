import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

function rule(selector) {
  const start = css.indexOf(`${selector} {`);
  assert.notEqual(start, -1, `${selector} is missing`);
  return css.slice(start, css.indexOf("}", start));
}

test("fullscreen headers clear Telegram Close by summing both safe areas", () => {
  assert.match(
    rule(":root"),
    /--chrome-top:\s*calc\(\s*var\(--tg-safe-area-inset-top,\s*0px\)\s*\+\s*var\(--tg-content-safe-area-inset-top,\s*0px\)\s*\)/,
  );
  for (const selector of [".hero-copy", ".cover-tools", ".tab-head", ".partner-hero", ".route-head", ".close"]) {
    assert.match(rule(selector), /var\(--chrome-top\)/, `${selector} sits under the Telegram Close button`);
  }
});
