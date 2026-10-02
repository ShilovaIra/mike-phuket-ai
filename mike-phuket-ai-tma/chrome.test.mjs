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
  for (const selector of [".hero", ".cover-tools", ".tab-head", ".partner-hero", ".route-head", ".close"]) {
    assert.match(rule(selector), /var\(--chrome-top\)/, `${selector} sits under the Telegram Close button`);
  }
  assert.doesNotMatch(rule(".hero-copy"), /var\(--chrome-top\)/, "the home photo must move, not the title inside it");
});

test("place back and heart sit above the photo", () => {
  const tools = rule(".cover-tools");
  assert.match(tools, /var\(--chrome-top\)/, "the strip still clears Telegram Close");
  assert.doesNotMatch(tools, /position:\s*absolute/, "the strip must not overlay the place photo");
  const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");
  const toolsAt = html.indexOf('class="cover-tools"');
  const coverAt = html.indexOf('<header class="cover">');
  assert.ok(toolsAt !== -1 && coverAt !== -1 && toolsAt < coverAt, "the control strip comes before the photo");
});
