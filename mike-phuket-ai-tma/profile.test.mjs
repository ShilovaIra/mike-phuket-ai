import assert from "node:assert/strict";
import { test } from "node:test";
import { profileView } from "./profile.mjs";

test("profile shows first and last name when both exist", () => {
  const view = profileView({ first_name: "Ivan", last_name: "Petrov" });
  assert.equal(view.name, "Ivan Petrov");
});

test("profile shows only the first name when there is no last name", () => {
  const view = profileView({ first_name: "Ivan" });
  assert.equal(view.name, "Ivan");
});

test("profile shows a guest placeholder outside Telegram", () => {
  const view = profileView();
  assert.equal(view.name, "Гость");
  assert.equal(view.letter, "Г");
});

test("profile returns the Telegram photo only when one exists", () => {
  const withPhoto = profileView({
    first_name: "Ivan",
    photo_url: "https://t.me/a.jpg",
  });
  assert.equal(withPhoto.photoUrl, "https://t.me/a.jpg");

  const withoutPhoto = profileView({ first_name: "Ivan" });
  assert.equal(withoutPhoto.photoUrl, null);
});
