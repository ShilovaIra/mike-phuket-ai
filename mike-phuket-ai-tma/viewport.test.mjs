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

test("before Telegram reports a sheet, the visual viewport still beats the innerHeight fallback", () => {
  const win = {
    Telegram: { WebApp: { viewportHeight: 844, viewportStableHeight: 844 } },
    document: { documentElement: {} },
    getComputedStyle() {
      return { getPropertyValue: () => "100vh" };
    },
    visualViewport: { height: 620 },
    innerHeight: 844,
  };

  assert.equal(visibleAppHeight(measureAppViewport(win)), 620);
});

test("expanding past the collapsed sheet ignores the previous CSS height", () => {
  // telegram-web-app.js emits viewportChanged before it writes --tg-viewport-height.
  // The collapsed px value is still there while WebApp.viewportHeight is already the sheet.
  const win = {
    Telegram: { WebApp: { viewportHeight: 740, viewportStableHeight: 740 } },
    document: { documentElement: {} },
    getComputedStyle() {
      return {
        getPropertyValue(name) {
          if (name === "--tg-viewport-height" || name === "--tg-viewport-stable-height") return "520px";
          return "";
        },
      };
    },
    visualViewport: { height: 520 },
    innerHeight: 520,
  };

  assert.equal(visibleAppHeight(measureAppViewport(win)), 740);
});

test("a visual viewport still at the collapsed height does not keep the tab bar mid-screen", () => {
  assert.equal(
    visibleAppHeight({
      telegramViewportKnown: true,
      trustedSheet: true,
      telegramHeight: 740,
      visualViewportHeight: 520,
      innerHeight: 520,
    }),
    740,
  );
});

test("opening the mini app subscribes before expand and measures the sheet it produces", () => {
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
    () => {
      calls.push("measure");
    },
  );
  assert.deepEqual(calls, ["viewportChanged", "ready", "expand", "measure"]);
});
