import assert from "node:assert/strict";
import { test } from "node:test";
import {
  catalogView,
  EMPTY_PHOTO,
  homeView,
  partnerPage,
  placeView,
} from "./catalog.mjs";

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

test("home recommendations list every partner, then only unbound Mike picks", () => {
  const partners = [
    {
      id: "p-esim",
      name: "Mike eSIM",
      blurb: "",
      logo_url: "",
      sort_order: 2,
      type_label: "eSIM",
    },
    {
      id: "p-money",
      name: "Money Shop",
      blurb: "Обмен",
      logo_url: "https://cdn.example/logo.png",
      sort_order: 1,
      type_label: "Обмен",
    },
  ];
  const places = [
    {
      ...recommended,
      name: "Касса",
      category: "Магазин",
      photo_url: "https://cdn.example/kata.jpg",
      partner: { id: "p-money", name: "Money Shop" },
    },
    { ...recommended, name: "Якорная", partner: null },
    { ...plain, name: "Анапа", partner: null },
  ];

  const view = homeView(partners, places);
  const names = (cards) => cards.map((card) => card.name);

  assert.deepEqual(view.recommendations.partners, [
    { id: "p-money", name: "Money Shop", logoUrl: "https://cdn.example/logo.png" },
    { id: "p-esim", name: "Mike eSIM", logoUrl: "" },
  ]);
  assert.deepEqual(names(view.recommendations.places), ["Якорная"]);
  assert.equal(names(view.recommendations.places).includes("Касса"), false);
  assert.equal(names(view.places.places).includes("Касса"), false);
});

test("the places row lists every unbound place, including Mike picks", () => {
  const places = [
    { ...plain, name: "Анапа", partner: null },
    {
      ...plain,
      name: "Касса",
      partner: { id: "p-money", name: "Money Shop" },
    },
    { ...recommended, name: "Якорная", partner: null },
  ];

  const view = homeView([], places);
  const names = (cards) => cards.map((card) => card.name);

  assert.deepEqual(names(view.places.places), ["Якорная", "Анапа"]);
  assert.deepEqual(names(view.recommendations.places), ["Якорная"]);
});

test("a partner office exposes its name, photo, badge, and maps link", () => {
  const money = { id: "p-money", name: "Money Shop" };
  const office = {
    ...recommended,
    name: "Касса",
    partner: { id: "p-money", name: "Money Shop" },
  };

  const card = partnerPage(money, [office]).places[0];

  assert.equal(card.name, "Касса");
  assert.equal(card.photoUrl, "https://cdn.example/promthep.jpg");
  assert.equal(card.badge, true);
  assert.equal(card.mapsUrl, "https://maps.example/promthep");
  assert.equal(card.mapsLabel, "Открыть в картах");
});

test("a partner office without a map keeps its name, photo, and badge", () => {
  const money = { id: "p-money", name: "Money Shop" };
  const office = {
    ...plain,
    name: "Стойка",
    maps_url: "",
    partner: { id: "p-money", name: "Money Shop" },
  };

  const card = partnerPage(money, [office]).places[0];

  assert.equal(card.name, "Стойка");
  assert.equal(card.photoUrl, "https://cdn.example/kata.jpg");
  assert.equal(card.badge, false);
  assert.equal(card.mapsUrl, null);
  assert.equal(card.mapsLabel, null);
});

test("a partner page titles its offices only when that partner has places", () => {
  const money = { id: "p-money", name: "Money Shop" };
  const esim = { id: "p-esim", name: "Mike eSIM" };
  const places = [
    { ...plain, name: "Касса", partner: { id: "p-money", name: "Money Shop" } },
    { ...recommended, name: "Якорная", partner: null },
    { ...plain, name: "Стойка", partner: { id: "p-other", name: "Other" } },
  ];

  const withOffices = partnerPage(money, places);
  assert.equal(withOffices.officesTitle, "Офисы партнёра");
  assert.deepEqual(
    withOffices.places.map((card) => card.name),
    ["Касса"],
  );

  const withoutOffices = partnerPage(esim, places);
  assert.equal(withoutOffices.officesTitle, null);
  assert.deepEqual(withoutOffices.places, []);
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
