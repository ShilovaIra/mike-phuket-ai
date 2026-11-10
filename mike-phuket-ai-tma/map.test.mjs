import assert from "node:assert/strict";
import { test } from "node:test";
import {
  cameraFor,
  createPinButton,
  externalUrl,
  locateAfter,
  readFix,
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

test("a tap makes the locate button busy, and another tap during that reading changes nothing", () => {
  const ready = { dot: null, banner: null, button: "ready" };
  const busy = locateAfter(ready, { type: "tap" });
  assert.equal(busy.button, "busy");
  assert.equal(busy.dot, null);
  assert.equal(busy.banner, null);
  assert.deepEqual(locateAfter(busy, { type: "tap" }), busy);
});

test("a fix inside the view places one dot, and a later fix moves it", () => {
  const busy = { dot: null, banner: "Не удалось определить место", button: "busy" };
  const placed = locateAfter(busy, {
    type: "fix",
    latitude: 7.88,
    longitude: 98.39,
    inside: true,
  });
  assert.deepEqual(placed, {
    dot: { latitude: 7.88, longitude: 98.39 },
    banner: null,
    button: "ready",
  });
  const moved = locateAfter(
    { dot: placed.dot, banner: placed.banner, button: "busy" },
    { type: "fix", latitude: 7.9, longitude: 98.4, inside: true },
  );
  assert.deepEqual(moved.dot, { latitude: 7.9, longitude: 98.4 });
  assert.equal(moved.banner, null);
  assert.equal(moved.button, "ready");
});

test("a fix outside the view keeps its banner until the dot comes into view", () => {
  const outside = locateAfter(
    { dot: null, banner: null, button: "busy" },
    { type: "fix", latitude: 13.75, longitude: 100.5, inside: false },
  );
  assert.deepEqual(outside, {
    dot: { latitude: 13.75, longitude: 100.5 },
    banner: "Вы за пределами карты",
    button: "ready",
  });
  const seen = locateAfter(outside, { type: "visible" });
  assert.equal(seen.banner, null);
  assert.deepEqual(seen.dot, outside.dot);
  assert.deepEqual(locateAfter(seen, { type: "visible" }), seen);
});

test("a miss keeps its banner until a later fix is inside the view", () => {
  const missed = locateAfter(
    { dot: null, banner: null, button: "busy" },
    { type: "miss" },
  );
  assert.deepEqual(missed, {
    dot: null,
    banner: "Не удалось определить место",
    button: "ready",
  });
  const waiting = locateAfter(missed, { type: "tap" });
  assert.equal(waiting.banner, "Не удалось определить место");
  assert.equal(waiting.button, "busy");
  const placed = locateAfter(waiting, {
    type: "fix",
    latitude: 7.88,
    longitude: 98.39,
    inside: true,
  });
  assert.equal(placed.banner, null);
});

test("a refusal leaves the pins alone and ignores later taps", () => {
  const refused = locateAfter(
    {
      dot: { latitude: 7.88, longitude: 98.39 },
      banner: "Не удалось определить место",
      button: "busy",
    },
    { type: "refuse" },
  );
  assert.deepEqual(refused, { dot: null, banner: null, button: "hidden" });
  assert.deepEqual(locateAfter(refused, { type: "tap" }), refused);
});

test("a Telegram reading stays off the browser geolocation", async () => {
  const fix = await readFix({
    locationManager: {
      isInited: true,
      isAccessGranted: true,
      getLocation(callback) {
        callback({ latitude: 7.88, longitude: 98.39 });
      },
    },
    geolocation: {
      getCurrentPosition() {
        throw new Error("browser");
      },
    },
  });
  assert.deepEqual(fix, { type: "fix", latitude: 7.88, longitude: 98.39 });
});

test("a denied Telegram reading is a refusal", async () => {
  const result = await readFix({
    locationManager: {
      isInited: true,
      isAccessRequested: true,
      isAccessGranted: false,
      getLocation(callback) {
        callback(null);
      },
    },
    geolocation: {
      getCurrentPosition() {
        throw new Error("browser");
      },
    },
  });
  assert.deepEqual(result, { type: "refuse" });
});

test("a Telegram reading with no position is a miss", async () => {
  const result = await readFix({
    locationManager: {
      isInited: true,
      isAccessGranted: true,
      isAccessRequested: true,
      getLocation(callback) {
        callback(null);
      },
    },
  });
  assert.deepEqual(result, { type: "miss" });
});

test("a browser reading is used when Telegram has no location manager", async () => {
  const fix = await readFix({
    locationManager: null,
    geolocation: {
      getCurrentPosition(success) {
        success({ coords: { latitude: 7.88, longitude: 98.39 } });
      },
    },
  });
  assert.deepEqual(fix, { type: "fix", latitude: 7.88, longitude: 98.39 });
});

test("a denied browser reading is a refusal", async () => {
  const result = await readFix({
    geolocation: {
      getCurrentPosition(_success, failure) {
        failure({ code: 1 });
      },
    },
  });
  assert.deepEqual(result, { type: "refuse" });
});

test("a reading with no browser geolocation is a miss", async () => {
  assert.deepEqual(await readFix({ locationManager: null, geolocation: null }), {
    type: "miss",
  });
});

test("a browser reading with no position is a miss", async () => {
  const result = await readFix({
    geolocation: {
      getCurrentPosition(_success, failure) {
        failure({ code: 2 });
      },
    },
  });
  assert.deepEqual(result, { type: "miss" });
});

test("a Telegram reading waits until the location manager is ready", async () => {
  let ready = false;
  const manager = {
    isInited: false,
    isAccessGranted: true,
    init(callback) {
      ready = true;
      this.isInited = true;
      callback();
    },
    getLocation(callback) {
      callback(ready ? { latitude: 7.88, longitude: 98.39 } : null);
    },
  };
  assert.deepEqual(await readFix({ locationManager: manager }), {
    type: "fix",
    latitude: 7.88,
    longitude: 98.39,
  });
});

test("several pins frame the island, and none falls back to Phuket", () => {
  const framed = cameraFor([recommended, plain]);
  assert.equal(framed.bounds.south, 7.7622);
  assert.equal(framed.bounds.north, 7.8201);
  assert.deepEqual(cameraFor([]), { center: PHUKET, zoom: 11 });
});
