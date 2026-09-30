import assert from "node:assert/strict";
import { test } from "node:test";
import { catalogView, EMPTY_PHOTO, placeView } from "./catalog.mjs";

const recommended = {
  name: "Якорная",
  category: "Пляж",
  blurb: "Закат",
  maps_url: "https://maps.example/promthep",
  photo_url: "https://cdn.example/promthep.jpg",
  mike_recommends: true,
};

const plain = {
  name: "Анапа",
  category: "Магазин",
  blurb: "",
  maps_url: "https://maps.example/kata",
  photo_url: "https://cdn.example/kata.jpg",
  mike_recommends: false,
};

test("home cards show the recommend badge only on a recommended place", () => {
  const view = catalogView([recommended, plain]);

  assert.equal(view.cards[0].badge, true);
  assert.equal(view.cards[1].badge, false);
  assert.equal(view.cards[0].name, "Якорная");
  assert.equal(view.cards[0].photoUrl, "https://cdn.example/promthep.jpg");
});

test("a place without a photo uses the admin placeholder", () => {
  const fromCatalog = catalogView([
    { ...plain, photo_url: "https://cdn.example/media/places/placeholder.jpg" },
  ]);
  assert.equal(fromCatalog.cards[0].photoUrl, EMPTY_PHOTO);

  const fromPlace = placeView({ ...plain, photo_url: "" });
  assert.equal(fromPlace.photoUrl, EMPTY_PHOTO);
});

test("an empty catalog is an empty state", () => {
  const view = catalogView([]);

  assert.equal(view.empty, true);
  assert.deepEqual(view.cards, []);
});

test("the place screen opens the maps link and keeps the badge", () => {
  const view = placeView(recommended);

  assert.equal(view.mapsUrl, "https://maps.example/promthep");
  assert.equal(view.mapsLabel, "Открыть в картах");
  assert.equal(view.badge, true);
  assert.equal(view.blurb, "Закат");
  assert.equal(view.name, "Якорная");
  assert.equal(view.category, "Пляж");
});
