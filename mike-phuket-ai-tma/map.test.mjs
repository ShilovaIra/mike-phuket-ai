import assert from "node:assert/strict";
import { test } from "node:test";
import {
  cameraFor,
  createPinButton,
  externalUrl,
  markerOptions,
  PHUKET,
  pinCard,
  PIN_RED,
  selectionAfter,
  usablePins,
} from "./map.mjs";

const recommended = {
  name: "Якорная",
  latitude: 7.7622,
  longitude: 98.3055,
  mike_recommends: true,
  photo_url: "https://cdn.example/promthep.jpg",
};

const plain = {
  name: "Анапа",
  latitude: 7.8201,
  longitude: 98.298,
  mike_recommends: false,
  photo_url: "https://cdn.example/kata.jpg",
};

test("a maps link opens on the mini app origin when it is ours", () => {
  assert.equal(
    externalUrl("/api/places/place-1/maps", "https://tma.example"),
    "https://tma.example/api/places/place-1/maps",
  );
  assert.equal(
    externalUrl("https://maps.example/promthep", "https://tma.example"),
    "https://maps.example/promthep",
  );
});

test("a pin card shows the photo, name, category, plain blurb, and Открыть", () => {
  const card = pinCard({
    id: "yakornaya",
    name: "Якорная",
    category: "Пляж",
    photo_url: "https://cdn.example/promthep.jpg",
    blurb: "Закат",
  });
  assert.equal(card.photoUrl, "https://cdn.example/promthep.jpg");
  assert.equal(card.name, "Якорная");
  assert.equal(card.category, "Пляж");
  assert.equal(card.description, "Закат");
  assert.equal(card.actionLabel, "Открыть");
});

test("Открыть uses the saved maps link, or the pin point when that link is missing", () => {
  const saved = pinCard({
    name: "Якорная",
    category: "Пляж",
    photo_url: "https://cdn.example/promthep.jpg",
    blurb: "Закат",
    maps_url: "https://maps.example/promthep",
    latitude: 7.7622,
    longitude: 98.3055,
  });
  assert.equal(saved.mapsUrl, "https://maps.example/promthep");
  assert.equal(saved.actionLabel, "Открыть");

  const point = pinCard({
    name: "Анапа",
    category: "Магазин",
    photo_url: "https://cdn.example/kata.jpg",
    maps_url: "  ",
    latitude: 7.8201,
    longitude: 98.298,
  });
  assert.equal(
    point.mapsUrl,
    "https://www.google.com/maps/search/?api=1&query=7.8201,98.298",
  );
});

test("a blank blurb is left off the card and a url stays plain text", () => {
  const blank = pinCard({
    name: "Анапа",
    category: "Магазин",
    photo_url: "https://cdn.example/kata.jpg",
    blurb: "  ",
  });
  assert.equal(blank.description, null);

  const linked = pinCard({
    name: "Анапа",
    category: "Магазин",
    photo_url: "https://cdn.example/kata.jpg",
    blurb: "Сайт https://example.com/a",
  });
  assert.equal(linked.description, "Сайт https://example.com/a");
});

test("another pin replaces the card, a map tap clears it, and leaving keeps it", () => {
  assert.equal(selectionAfter("yakornaya", { type: "pin", id: "anapa" }), "anapa");
  assert.equal(selectionAfter("yakornaya", { type: "map" }), null);
  assert.equal(selectionAfter("yakornaya", { type: "keep" }), "yakornaya");
});

test("a pin without coordinates is left off the map", () => {
  const pins = usablePins([recommended, { name: "Пусто", latitude: null, longitude: 98 }]);
  assert.deepEqual(pins, [recommended]);
});

test("every pin is red, with a round photo, and a recommendation stays larger", () => {
  const strong = markerOptions(recommended);
  const quiet = markerOptions(plain);
  assert.equal(strong.color, PIN_RED);
  assert.equal(quiet.color, PIN_RED);
  assert.equal(strong.photoUrl, "https://cdn.example/promthep.jpg");
  assert.equal(quiet.photoUrl, "https://cdn.example/kata.jpg");
  assert.ok(strong.size > quiet.size);
  assert.equal(strong.zIndex > quiet.zIndex, true);
  assert.match(strong.title, /Майк рекомендует/);
  assert.equal(quiet.title, "Анапа");
});

function fakeDocument() {
  const make = (tag) => ({
    tag,
    type: "",
    className: "",
    style: {},
    children: [],
    attrs: {},
    appendChild(child) {
      this.children.push(child);
    },
    setAttribute(name, value) {
      this.attrs[name] = value;
    },
    addEventListener() {},
  });
  return { createElement: make };
}

test("a pin photo is a background, so the map's image rules cannot hide it", () => {
  const button = createPinButton(fakeDocument(), markerOptions(recommended), () => {});
  const photo = button.children[0];
  assert.equal(photo.tag, "span");
  assert.equal(photo.className, "map-pin-photo");
  assert.equal(photo.style.height, "34px");
  assert.equal(photo.style.backgroundImage, 'url("https://cdn.example/promthep.jpg")');
  assert.equal(
    button.children.some((child) => child.tag === "img"),
    false,
  );
});

test("one pin centers on that place", () => {
  assert.deepEqual(cameraFor([plain]), {
    center: { lat: 7.8201, lng: 98.298 },
    zoom: 15,
  });
});

test("several pins frame the island, and none falls back to Phuket", () => {
  const framed = cameraFor([recommended, plain]);
  assert.equal(framed.bounds.south, 7.7622);
  assert.equal(framed.bounds.north, 7.8201);
  assert.deepEqual(cameraFor([]), { center: PHUKET, zoom: 11 });
});
