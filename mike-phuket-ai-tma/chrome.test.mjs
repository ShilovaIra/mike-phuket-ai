import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

function rule(selector) {
  const start = css.indexOf(`${selector} {`);
  assert.notEqual(start, -1, `${selector} is missing`);
  return css.slice(start, css.indexOf("}", start));
}

test("wordmark bar clears Telegram Close and inner rows do not add that inset again", () => {
  assert.match(
    rule(":root"),
    /--chrome-top:\s*calc\(\s*var\(--tg-safe-area-inset-top,\s*0px\)\s*\+\s*var\(--tg-content-safe-area-inset-top,\s*0px\)\s*\)/,
  );
  assert.match(rule(":root"), /--wordmark-bar:\s*calc\(\s*52px\s*\+\s*var\(--chrome-top\)\s*\)/);
  assert.match(rule(".wordmark"), /padding-top:\s*var\(--chrome-top\)/);
  assert.match(rule(".hero"), /var\(--chrome-top\)/, "home still clears Telegram Close on the hero");
  assert.doesNotMatch(rule(".hero-copy"), /var\(--chrome-top\)/, "the home photo must move, not the title inside it");
  for (const selector of [".cover-tools", ".tab-head", ".partner-hero", ".route-head", ".close"]) {
    assert.doesNotMatch(rule(selector), /var\(--chrome-top\)/, `${selector} would double the Telegram inset`);
  }
});

test("wordmark returns home and stays hidden while home is showing", () => {
  const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");
  const wordmarks = [...html.matchAll(/<a\b[^>]*class="wordmark"[^>]*>[\s\S]*?<\/a>/g)];
  assert.equal(wordmarks.length, 1);
  const link = wordmarks[0][0];
  assert.match(link, /href="#home"/);
  assert.match(link, /src="\.\/assets\/mike-phuket-ai-header\.png"/);
  assert.match(link, /alt="Mike Phuket AI"/);

  const home = html.slice(html.indexOf('id="home"'), html.indexOf('id="voice"'));
  assert.equal(home.includes('class="wordmark"'), false, "home keeps its own hero");

  assert.match(rule(".wordmark"), /display:\s*none/);
  assert.match(
    rule(".device:has(.screen:target):not(:has(#home:target)) .wordmark"),
    /display:\s*flex/,
  );
});

test("wordmark bar is a pinned white strip with the mark centered", () => {
  const bar = rule(".wordmark");
  assert.match(bar, /position:\s*absolute/);
  assert.match(bar, /z-index:\s*var\(--z-sticky\)/);
  assert.match(bar, /top:\s*0/);
  assert.match(bar, /right:\s*0/);
  assert.match(bar, /left:\s*0/);
  assert.match(bar, /background:\s*#fff/);
  assert.match(bar, /justify-content:\s*center/);
  assert.match(bar, /height:\s*var\(--wordmark-bar\)/);
  assert.match(rule(".wordmark img"), /height:\s*36px/);
  assert.match(
    rule(".device:has(.screen:target):not(:has(#home:target)) .screen:target"),
    /padding-top:\s*var\(--wordmark-bar\)/,
  );
});

test("place back and heart sit above the photo", () => {
  const tools = rule(".cover-tools");
  assert.doesNotMatch(tools, /position:\s*absolute/, "the strip must not overlay the place photo");
  const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");
  const toolsAt = html.indexOf('class="cover-tools"');
  const coverAt = html.indexOf('<header class="cover">');
  assert.ok(toolsAt !== -1 && coverAt !== -1 && toolsAt < coverAt, "the control strip comes before the photo");
});
