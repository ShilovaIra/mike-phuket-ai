import assert from "node:assert/strict";
import { test } from "node:test";
import { bootTelegram, measureAppViewport, readPx, visibleAppHeight } from "./viewport.mjs";

test("the mini app uses Telegram's sheet height when the visual viewport is the full device", () => {
  assert.equal(
    visibleAppHeight({
      telegramViewportKnown: true,
      telegramHeight: 620,
      visualViewportHeight: 844,
      innerHeight: 844,
    }),
    620,
  );
});

test("a shrinking visual viewport wins so the tab bar stays above the keyboard", () => {
  assert.equal(
    visibleAppHeight({
      telegramViewportKnown: true,
      telegramHeight: 700,
      visualViewportHeight: 420,
      innerHeight: 844,
    }),
    420,
  );
});

test("outside Telegram the visual viewport is the app height", () => {
  assert.equal(
    visibleAppHeight({
      telegramViewportKnown: false,
      telegramHeight: 0,
      visualViewportHeight: 700,
      innerHeight: 844,
    }),
    700,
  );
});

test("Telegram's 100vh fallback is not a measured sheet height", () => {
  assert.equal(readPx("100vh"), 0);
  assert.equal(readPx("620px"), 620);
});

test("a viewportChanged callback can see Telegram's height before the CSS variable updates", () => {
  const win = {
    Telegram: { WebApp: { viewportHeight: 620, viewportStableHeight: 620 } },
    document: { documentElement: {} },
    getComputedStyle() {
      return { getPropertyValue: () => "100vh" };
    },
    visualViewport: { height: 844 },
    innerHeight: 844,
  };

  assert.equal(visibleAppHeight(measureAppViewport(win)), 620);
});

test("opening the mini app expands it to the full sheet", () => {
  const calls = [];
  bootTelegram(
    {
      ready() {
        calls.push("ready");
      },
      expand() {
        calls.push("expand");
      },
      onEvent(name) {
        calls.push(name);
      },
    },
    () => {},
  );
  assert.deepEqual(calls, ["ready", "expand", "viewportChanged"]);
});
