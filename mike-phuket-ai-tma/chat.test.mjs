import assert from "node:assert/strict";
import { test } from "node:test";
import { canSend, failureView, loadThread, postMessage, threadView, waitingView } from "./chat.mjs";

test("an empty thread shows only the greeting", () => {
  const view = threadView([]);

  assert.deepEqual(view.bubbles, [
    { role: "mike", parts: [{ type: "text", value: "Привет! Я Майк. Спрашивай что угодно о Пхукете." }] },
  ]);
});

test("a saved thread hides the greeting and turns map urls into links", () => {
  const url = "https://www.google.com/maps/search/?api=1&query=Kata+Beach+Phuket";
  const view = threadView([
    { role: "user", content: "Где пляж?" },
    { role: "assistant", content: `Пляж Ката. ${url}` },
  ]);

  assert.equal(
    view.bubbles.some((bubble) =>
      bubble.parts.some((part) => part.value && part.value.includes("Привет")),
    ),
    false,
  );
  assert.deepEqual(view.bubbles, [
    { role: "user", parts: [{ type: "text", value: "Где пляж?" }] },
    {
      role: "mike",
      parts: [
        { type: "text", value: "Пляж Ката. " },
        { type: "link", href: url },
      ],
    },
  ]);
});

test("waiting shows dots before the thinking line", () => {
  assert.deepEqual(waitingView(), {
    role: "mike",
    dots: true,
    text: "Думаю как местный 😎",
  });
});

test("a failed turn shows the retry line", () => {
  assert.deepEqual(failureView(), {
    role: "mike",
    parts: [{ type: "text", value: "Не получилось ответить. Напиши ещё раз." }],
  });
});

test("sending needs a signed session, a free composer, and some text", () => {
  assert.equal(canSend({ signedIn: true, busy: false, text: " Привет " }), true);
  assert.equal(canSend({ signedIn: false, busy: false, text: "Привет" }), false);
  assert.equal(canSend({ signedIn: true, busy: true, text: "Привет" }), false);
  assert.equal(canSend({ signedIn: true, busy: false, text: "  " }), false);
});

test("loading the thread sends the signed init data", async () => {
  let called;
  const messages = await loadThread({
    initData: "signed",
    fetch: async (url, options) => {
      called = { url, options };
      return {
        ok: true,
        json: async () => ({ messages: [{ role: "user", content: "Привет" }] }),
      };
    },
  });

  assert.equal(called.url, "/api/tma/messages");
  assert.equal(called.options.headers.Authorization, "tma signed");
  assert.deepEqual(messages, [{ role: "user", content: "Привет" }]);
});

test("sending posts the text with the signed init data and returns the reply", async () => {
  let called;
  const reply = await postMessage({
    text: "Привет",
    initData: "signed",
    fetch: async (url, options) => {
      called = { url, options };
      return { ok: true, json: async () => ({ reply: "Ок" }) };
    },
  });

  assert.equal(called.url, "/api/tma/messages");
  assert.equal(called.options.method, "POST");
  assert.equal(called.options.headers.Authorization, "tma signed");
  assert.deepEqual(JSON.parse(called.options.body), { text: "Привет" });
  assert.equal(reply, "Ок");
});

test("a failed send does not return a reply", async () => {
  await assert.rejects(() =>
    postMessage({
      text: "Привет",
      initData: "signed",
      fetch: async () => ({ ok: false, status: 502 }),
    }),
  );
});
