import { catalogView } from "./catalog.mjs";

const SAVE_ERROR = "Не удалось сохранить";

function tmaHeaders(initData) {
  return { Authorization: `tma ${initData}` };
}

export async function openSession({ initData, fetch }) {
  const response = await fetch("/api/tma/session", {
    method: "POST",
    headers: tmaHeaders(initData),
  });
  if (!response.ok) throw new Error("session");
}

export async function loadFavourites({ initData, fetch }) {
  const response = await fetch("/api/tma/favourites", { headers: tmaHeaders(initData) });
  if (!response.ok) throw new Error("favourites");
  return response.json();
}

export async function setSaved({ id, saved, initData, fetch }) {
  const response = await fetch(`/api/tma/favourites/${id}`, {
    method: "PUT",
    headers: { ...tmaHeaders(initData), "Content-Type": "application/json" },
    body: JSON.stringify({ saved }),
  });
  if (!response.ok) throw new Error("save");
  const body = await response.json();
  return body.saved;
}

export function heartView({ saved, failed }) {
  return {
    filled: Boolean(saved),
    error: failed ? SAVE_ERROR : "",
  };
}

export function favouritesView(places) {
  const view = catalogView(places);
  return {
    empty: view.empty,
    cards: view.cards.map((card, index) => ({
      id: places[index].id,
      name: card.name,
      category: card.category,
      photoUrl: card.photoUrl,
      badge: card.badge,
    })),
  };
}
