import assert from "node:assert/strict";
import { test } from "node:test";
import { catalogView, EMPTY_PHOTO, placeView, recommendationsView } from "./catalog.mjs";

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

test("a partner place sits under its partner and stays out of the places row", () => {
  const bound = {
    ...plain,
    name: "Касса",
    partner: {
      name: "Money Shop",
      blurb: "Обмен",
      logo_url: "https://cdn.example/logo.png",
      sort_order: 1,
    },
  };
  const view = recommendationsView([bound, { ...recommended, partner: null }]);

  assert.equal(view.partners.length, 1);
  assert.equal(view.partners[0].name, "Money Shop");
  assert.deepEqual(view.partners[0].places, [
    {
      name: "Касса",
      category: "Магазин",
      photoUrl: "https://cdn.example/kata.jpg",
      badge: false,
    },
  ]);
  assert.deepEqual(
    view.places.map((card) => card.name),
    ["Якорная"],
  );
});

test("partners follow sort order then name, and places put recommended first", () => {
  const partner = (name, sort_order) => ({
    name,
    blurb: "",
    logo_url: "",
    sort_order,
  });
  const view = recommendationsView([
    {
      ...plain,
      name: "Бар",
      mike_recommends: false,
      partner: partner("Boomerang", 2),
    },
    { ...plain, name: "Анапа", partner: null },
    {
      ...recommended,
      name: "Зона",
      partner: partner("Boomerang", 2),
    },
    {
      ...plain,
      name: "Стойка",
      partner: partner("Alpha", 2),
    },
    { ...recommended, name: "Якорная", partner: null },
    {
      ...plain,
      name: "Касса",
      partner: partner("Money Shop", 1),
    },
  ]);

  assert.deepEqual(
    view.partners.map((block) => block.name),
    ["Money Shop", "Alpha", "Boomerang"],
  );
  assert.deepEqual(
    view.partners[2].places.map((card) => card.name),
    ["Зона", "Бар"],
  );
  assert.deepEqual(
    view.places.map((card) => card.name),
    ["Якорная", "Анапа"],
  );
});

test("the places heading shows only beside partners, and a missing logo is a letter", () => {
  const both = recommendationsView([
    {
      ...plain,
      name: "Касса",
      partner: { name: "Money Shop", blurb: "", logo_url: "", sort_order: 1 },
    },
    { ...recommended, partner: null },
  ]);
  assert.equal(both.showPlacesHeading, true);
  assert.equal(both.empty, false);
  assert.equal(both.partners[0].logoUrl, "");
  assert.equal(both.partners[0].initial, "M");
  assert.equal(both.partners[0].blurb, "");

  const partnersOnly = recommendationsView([
    {
      ...plain,
      partner: {
        name: "Money Shop",
        blurb: "Обмен",
        logo_url: "https://cdn.example/logo.png",
        sort_order: 1,
      },
    },
  ]);
  assert.equal(partnersOnly.showPlacesHeading, false);
  assert.equal(partnersOnly.empty, false);
  assert.equal(partnersOnly.partners[0].blurb, "Обмен");
  assert.equal(partnersOnly.partners[0].logoUrl, "https://cdn.example/logo.png");

  const placesOnly = recommendationsView([{ ...recommended, partner: null }]);
  assert.equal(placesOnly.showPlacesHeading, false);
  assert.equal(placesOnly.empty, false);

  const none = recommendationsView([]);
  assert.equal(none.empty, true);
  assert.equal(none.showPlacesHeading, false);
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
