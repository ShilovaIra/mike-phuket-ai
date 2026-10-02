export function readPx(value) {
  const match = String(value || "").trim().match(/^(\d+(?:\.\d+)?)px$/);
  return match ? Number(match[1]) : 0;
}

export function visibleAppHeight(measure) {
  const visual = measure.visualViewportHeight > 0 ? measure.visualViewportHeight : measure.innerHeight;
  if (!(measure.telegramViewportKnown && measure.telegramHeight > 0)) {
    return Math.round(visual || 0);
  }
  if (!(visual > 0)) return Math.round(measure.telegramHeight);

  const sheet = measure.telegramHeight;
  const inner = measure.innerHeight || 0;
  // The keyboard shrinks the visual viewport while the layout viewport stays tall.
  // A collapsed sheet is the opposite: the webview is still short, or only the
  // visual viewport is, while Telegram has already reported the expanded height.
  const keyboard = inner > sheet + 40 && visual + 40 < inner;
  if (measure.trustedSheet && !keyboard && visual + 1 < sheet && inner <= sheet + 1) {
    return Math.round(sheet);
  }
  return Math.round(Math.min(sheet, visual));
}

export function measureAppViewport(win) {
  const styles = win.getComputedStyle(win.document.documentElement);
  const current = readPx(styles.getPropertyValue("--tg-viewport-height"));
  const stable = readPx(styles.getPropertyValue("--tg-viewport-stable-height"));
  const tg = win.Telegram && win.Telegram.WebApp;
  const fromApi = tg && Number(tg.viewportHeight) > 0 ? Number(tg.viewportHeight) : 0;
  const cssPx = current || stable;
  // viewportChanged runs before telegram-web-app.js writes the CSS variables.
  // The previous pixel height is still on the root; WebApp.viewportHeight is already the sheet.
  const telegramHeight = cssPx > 0 && fromApi > 0 && fromApi !== cssPx ? fromApi : cssPx || fromApi;
  const apiIsFallback = fromApi > 0 && Math.abs(fromApi - (win.innerHeight || 0)) <= 1 && !(current > 0);
  const viewport = win.visualViewport;
  return {
    telegramViewportKnown: telegramHeight > 0,
    trustedSheet: cssPx > 0 || (fromApi > 0 && !apiIsFallback),
    telegramHeight,
    visualViewportHeight: viewport ? viewport.height : 0,
    innerHeight: win.innerHeight,
  };
}

export function pinAppHeight(root, measure) {
  const height = visibleAppHeight(measure);
  root.style.setProperty("--app-height", height + "px");
  return height;
}

export function bootTelegram(tg, onViewport) {
  if (!tg) return;
  // Subscribe first so a synchronous expand still delivers viewportChanged.
  if (typeof tg.onEvent === "function") tg.onEvent("viewportChanged", onViewport);
  if (typeof tg.ready === "function") tg.ready();
  if (typeof tg.expand === "function") tg.expand();
  if (typeof onViewport === "function") onViewport();
}
