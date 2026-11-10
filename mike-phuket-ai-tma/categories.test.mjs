import assert from "node:assert/strict";
import { test } from "node:test";
import { topicByHash, topicView } from "./categories.mjs";

const places = [
  {
    id: "shop",
    name: "Анапа",
    category: "Магазин",
    category_slug: "shop",
    blurb: "",
    photo_url: "https://cdn.example/shop.jpg",
    mike_recommends: false,
    partner: { id: "money", name: "Money Shop" },
  },
  {
    id: "cafe",
    name: "Чашка",
    category: "Кафе",
    category_slug: "cafe",
    blurb: "Завтрак",
    photo_url: "",
    mike_recommends: false,
    partner: null,
  },
  {
    id: "beach",
    name: "Якорная",
    category: "Пляж",
    category_slug: "beach",
    blurb: "Закат",
    photo_url: "https://cdn.example/beach.jpg",
    mike_recommends: true,
    partner: null,
  },
  {
    id: "club-beach",
    name: "Пляж клуба",
    category: "Пляж",
    category_slug: "beach",
    blurb: "",
    photo_url: "",
    mike_recommends: false,
    partner: { id: "club", name: "Клуб" },
  },
  {
    id: "bar",
    name: "Бар у пирса",
    category: "Бар",
    category_slug: "bar",
    blurb: "",
    photo_url: "",
    mike_recommends: true,
    partner: null,
  },
];

const partners = [
  {
    id: "esim",
    name: "Mike eSIM",
    type: "esim",
    type_label: "eSIM",
    blurb: "",
    logo_url: "",
    sort_order: 40,
  },
  {
    id: "trip",
    name: "Остров",
    type: "excursions",
    type_label: "Экскурсии",
    blurb: "На закате",
    logo_url: "https://cdn.example/trip.png",
    sort_order: 30,
  },
];

const saved = { places: ["beach"], partners: ["trip"] };

test("a category hash resolves to its list, and chat topics stay off that screen", () => {
  assert.equal(topicByHash("#beaches").label, "Пляжи");
  assert.equal(topicByHash("food").kind, "places");
  assert.equal(topicByHash("#chat"), null);
  assert.equal(topicByHash("#property"), null);
});

test("beaches list every beach, including one tied to a partner, and skip other categories", () => {
  const view = topicView(topicByHash("#beaches"), places, partners, saved);

  assert.equal(view.title, "Пляжи");
  assert.equal(view.empty, false);
  assert.deepEqual(
    view.rows.map((row) => row.name),
    ["Якорная", "Пляж клуба"],
  );
  assert.equal(view.rows[0].saved, true);
  assert.equal(view.rows[1].saved, false);
});

test("food lists cafes, restaurants, and bars, with Mike's picks first", () => {
  const view = topicView(topicByHash("#food"), places, partners, { places: [], partners: [] });

  assert.deepEqual(
    view.rows.map((row) => row.name),
    ["Бар у пирса", "Чашка"],
  );
  assert.equal(view.rows[1].blurb, "Завтрак");
});

test("a partner topic lists only that type, and an empty type says so", () => {
  const trips = topicView(topicByHash("#excursions"), places, partners, saved);
  assert.deepEqual(trips.rows, [
    {
      kind: "partner",
      id: "trip",
      name: "Остров",
      subtitle: "Экскурсии",
      blurb: "На закате",
      imageUrl: "https://cdn.example/trip.png",
      saved: true,
    },
  ]);

  const rides = topicView(topicByHash("#transport"), places, partners, saved);
  assert.equal(rides.empty, true);
  assert.equal(rides.emptyText, "Пока нет партнёров по транспорту");
  assert.deepEqual(rides.rows, []);
});
