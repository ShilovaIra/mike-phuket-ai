import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { themeView } from "./theme.mjs";

const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

function rule(selector) {
  const start = css.indexOf(`${selector} {`);
  assert.notEqual(start, -1, `${selector} is missing`);
  return css.slice(start, css.indexOf("}", start));
}

test("with nothing saved, the theme follows Telegram and stays light outside it", () => {
  assert.equal(themeView({ telegramScheme: "dark" }).choice, "dark");
  assert.equal(themeView({ telegramScheme: "light" }).choice, "light");
  assert.equal(themeView({}).choice, "light");
});

test("a saved choice wins over the current Telegram scheme", () => {
  assert.equal(themeView({ saved: "light", telegramScheme: "dark" }).choice, "light");
  assert.equal(themeView({ saved: "dark", telegramScheme: "light" }).choice, "dark");
});

test("the row names the theme the pill will turn on and parks the knob on the active side", () => {
  const dark = themeView({ saved: "dark", telegramScheme: "light" });
  assert.equal(dark.label, "Светлая тема");
  assert.equal(dark.knob, "dark");

  const light = themeView({ saved: "light", telegramScheme: "dark" });
  assert.equal(light.label, "Тёмная тема");
  assert.equal(light.knob, "light");
});

test("dark chrome uses the navy palette and light chrome stays as it is", () => {
  const light = rule(":root");
  assert.match(light, /--canvas:\s*#f4f7fb/i);
  assert.match(light, /--surface:\s*#ffffff/i);
  assert.match(light, /--ink:\s*#102033/i);
  assert.match(light, /--muted:\s*#3d5270/i);
  assert.match(light, /--line:\s*#d5deea/i);

  const dark = rule('[data-theme="dark"]');
  assert.match(dark, /--canvas:\s*#0e1622/i);
  assert.match(dark, /--surface:\s*#182433/i);
  assert.match(dark, /--ink:\s*#e7eef7/i);
  assert.match(dark, /--muted:\s*#93a6c0/i);
  assert.match(dark, /--line:\s*#2c3c52/i);
});
