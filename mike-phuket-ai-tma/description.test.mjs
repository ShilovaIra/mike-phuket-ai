import assert from "node:assert/strict";
import { test } from "node:test";
import { descriptionParts } from "./description.mjs";

test("an https address in a description becomes a link and the surrounding words stay text", () => {
  const url = "https://t.me/credodivingphuket/7";

  assert.deepEqual(descriptionParts(`Канал ${url} и ещё текст`), [
    { type: "text", value: "Канал " },
    { type: "link", href: url, label: url },
    { type: "text", value: " и ещё текст" },
  ]);
});

test("a bare host becomes an https link and the label stays the typed text", () => {
  assert.deepEqual(descriptionParts("WA: wa.me/874724855 site credo-diving.com"), [
    { type: "text", value: "WA: " },
    { type: "link", href: "https://wa.me/874724855", label: "wa.me/874724855" },
    { type: "text", value: " site " },
    { type: "link", href: "https://credo-diving.com", label: "credo-diving.com" },
  ]);
});

test("a trailing period or comma stays outside the link", () => {
  assert.deepEqual(descriptionParts("Сайт credo-diving.com. Канал https://t.me/credodivingphuket,"), [
    { type: "text", value: "Сайт " },
    { type: "link", href: "https://credo-diving.com", label: "credo-diving.com" },
    { type: "text", value: ". Канал " },
    { type: "link", href: "https://t.me/credodivingphuket", label: "https://t.me/credodivingphuket" },
    { type: "text", value: "," },
  ]);
});

test("an @handle and an email stay text", () => {
  assert.deepEqual(descriptionParts("Tg: @DivingPhuket mail@credo-diving.com"), [
    { type: "text", value: "Tg: @DivingPhuket mail@credo-diving.com" },
  ]);
});

test("spaces, tabs, and line breaks in the description stay in the text", () => {
  const text = "Дайвинг\n\n  Пробные\tпогружения\nhttps://t.me/credodivingphuket/7";

  assert.deepEqual(descriptionParts(text), [
    { type: "text", value: "Дайвинг\n\n  Пробные\tпогружения\n" },
    {
      type: "link",
      href: "https://t.me/credodivingphuket/7",
      label: "https://t.me/credodivingphuket/7",
    },
  ]);
});
