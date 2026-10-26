import { EMPTY_PHOTO } from "./catalog.mjs";

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

export async function setSaved({ kind, id, saved, initData, fetch }) {
  const path = kind === "partner" ? `/api/tma/favourites/partners/${id}` : `/api/tma/favourites/${id}`;
  const response = await fetch(path, {
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

function favouritePhoto(url) {
  if (!url || url.endsWith("media/places/placeholder.jpg")) return EMPTY_PHOTO;
  return url;
}

export function favouritesView(items) {
  return {
    empty: items.length === 0,
    rows: items.map((item) =>
      item.kind === "partner"
        ? {
            kind: "partner",
            id: item.id,
            name: item.name,
            subtitle: item.type_label || "",
            blurb: item.blurb || "",
            imageUrl: item.logo_url || "",
            saved: true,
          }
        : {
            kind: "place",
            id: item.id,
            name: item.name,
            subtitle: item.category,
            blurb: item.blurb || "",
            imageUrl: favouritePhoto(item.photo_url),
            saved: true,
          },
    ),
  };
}
