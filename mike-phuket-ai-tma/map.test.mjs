import assert from "node:assert/strict";
import { test } from "node:test";
import { cameraFor, markerOptions, PHUKET, PIN_RED, usablePins } from "./map.mjs";

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
