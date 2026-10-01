export function readPx(value) {
  const match = String(value || "").trim().match(/^(\d+(?:\.\d+)?)px$/);
  return match ? Number(match[1]) : 0;
}

export function visibleAppHeight(measure) {
  const visual = measure.visualViewportHeight > 0 ? measure.visualViewportHeight : measure.innerHeight;
  if (measure.telegramViewportKnown && measure.telegramHeight > 0 && visual > 0) {
    return Math.round(Math.min(measure.telegramHeight, visual));
  }
  if (measure.telegramViewportKnown && measure.telegramHeight > 0) {
    return Math.round(measure.telegramHeight);
  }
  return Math.round(visual || 0);
}

export function measureAppViewport(win) {
  const styles = win.getComputedStyle(win.document.documentElement);
  const current = readPx(styles.getPropertyValue("--tg-viewport-height"));
  const stable = readPx(styles.getPropertyValue("--tg-viewport-stable-height"));
  const tg = win.Telegram && win.Telegram.WebApp;
  const fromApi = tg && Number(tg.viewportHeight) > 0 ? Number(tg.viewportHeight) : 0;
  // viewportChanged fires before telegram-web-app.js writes the CSS variables,
  // but WebApp.viewportHeight is already the sheet height.
  const telegramHeight = current || stable || fromApi;
  const viewport = win.visualViewport;
  return {
    telegramViewportKnown: telegramHeight > 0,
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
  if (typeof tg.ready === "function") tg.ready();
  if (typeof tg.expand === "function") tg.expand();
  if (typeof tg.onEvent === "function") tg.onEvent("viewportChanged", onViewport);
}
