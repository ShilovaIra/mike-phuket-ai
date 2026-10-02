import assert from "node:assert/strict";
import { test } from "node:test";
import { EMPTY_PHOTO } from "./catalog.mjs";
import { favouritesView, heartView, loadFavourites, openSession, setSaved } from "./favourites.mjs";

test("an empty favourites list is an empty state", () => {
  const view = favouritesView([]);

  assert.equal(view.empty, true);
  assert.deepEqual(view.cards, []);
});

test("favourites cards keep api order and the home card fields", () => {
  const view = favouritesView([
    {
      id: "newer",
      name: "Анапа",
      category: "Магазин",
      photo_url: "https://cdn.example/kata.jpg",
      mike_recommends: false,
    },
    {
      id: "older",
      name: "Якорная",
      category: "Пляж",
      photo_url: "https://cdn.example/media/places/placeholder.jpg",
      mike_recommends: true,
    },
  ]);

  assert.equal(view.empty, false);
  assert.deepEqual(view.cards, [
    {
      id: "newer",
      name: "Анапа",
      category: "Магазин",
      photoUrl: "https://cdn.example/kata.jpg",
      badge: false,
    },
    {
      id: "older",
      name: "Якорная",
      category: "Пляж",
      photoUrl: EMPTY_PHOTO,
      badge: true,
    },
  ]);
});

test("the heart is filled only when saved, and a failure keeps that heart", () => {
  assert.deepEqual(heartView({ saved: false, failed: false }), {
    filled: false,
    error: "",
  });
  assert.deepEqual(heartView({ saved: true, failed: false }), {
    filled: true,
    error: "",
  });
  assert.deepEqual(heartView({ saved: false, failed: true }), {
    filled: false,
    error: "Не удалось сохранить",
  });
  assert.deepEqual(heartView({ saved: true, failed: true }), {
    filled: true,
    error: "Не удалось сохранить",
  });
});

test("saving sends the signed choice and returns it", async () => {
  let called;
  const saved = await setSaved({
    id: "place-1",
    saved: true,
    initData: "signed",
    fetch: async (url, options) => {
      called = { url, options };
      return { ok: true, json: async () => ({ saved: true }) };
    },
  });

  assert.equal(called.url, "/api/tma/favourites/place-1");
  assert.equal(called.options.method, "PUT");
  assert.equal(called.options.headers.Authorization, "tma signed");
  assert.deepEqual(JSON.parse(called.options.body), { saved: true });
  assert.equal(saved, true);
});

test("a failed save does not report a new heart", async () => {
  await assert.rejects(() =>
    setSaved({
      id: "place-1",
      saved: true,
      initData: "signed",
      fetch: async () => ({
        ok: false,
        status: 401,
        json: async () => ({ saved: true }),
      }),
    }),
  );
});

test("loading favourites sends the signed init data and returns the places", async () => {
  const places = [{ id: "place-1", name: "Якорная" }];
  let called;
  const loaded = await loadFavourites({
    initData: "signed",
    fetch: async (url, options) => {
      called = { url, options };
      return { ok: true, json: async () => places };
    },
  });

  assert.equal(called.url, "/api/tma/favourites");
  assert.equal(called.options.headers.Authorization, "tma signed");
  assert.deepEqual(loaded, places);
});

test("opening a session sends the signed init data", async () => {
  let called;
  await openSession({
    initData: "signed",
    fetch: async (url, options) => {
      called = { url, options };
      return { ok: true };
    },
  });

  assert.equal(called.url, "/api/tma/session");
  assert.equal(called.options.method, "POST");
  assert.equal(called.options.headers.Authorization, "tma signed");
});
