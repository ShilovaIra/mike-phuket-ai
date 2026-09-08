"""Repair map links in model answers before they reach a Tourist.

The prompt tells Mike to build Google Maps search URLs, but a prompt is not a
guarantee. Any shortened link the model emits is dead on arrival: it invents the
id, and Google retired goo.gl anyway, so the Maps app answers "Unsupported link".
"""

from __future__ import annotations

import re
from urllib.parse import quote_plus

MAPS_SEARCH_BASE = "https://www.google.com/maps/search/?api=1&query="
PLACE_REGION = "Phuket"

# Hosts whose links Mike can never know, only guess.
SHORTENER_HOSTS = frozenset(
    {
        "goo.gl",
        "maps.app.goo.gl",
        "g.page",
        "bit.ly",
        "tinyurl.com",
        "t.co",
        "is.gd",
        "cutt.ly",
        "rb.gy",
        "shorturl.at",
        "ow.ly",
    }
)

_URL = r"https?://[^\s<>()\[\]\"'`]+"
_MARKDOWN_LINK = re.compile(rf"\[([^\]]+)\]\(\s*({_URL})\s*\)")
_BARE_URL = re.compile(_URL)
_HOST = re.compile(r"https?://(?:www\.)?([^/?#]+)")
# Place names stay in Latin script even in Russian answers.
_LATIN_NAME = re.compile(r"[A-Za-z][A-Za-z0-9'&@.\-]*(?:\s+[A-Za-z0-9'&@.\-]+)*")
_TRAILING_PUNCT = ".,;:!?)"


def maps_search_url(place: str) -> str:
    """A Maps search URL always resolves, unlike a guessed place id."""
    query = place.strip(" \t\n" + _TRAILING_PUNCT)
    if PLACE_REGION.lower() not in query.lower():
        query = f"{query} {PLACE_REGION}"
    return MAPS_SEARCH_BASE + quote_plus(query)


def maps_place_url(place: str, place_id: str) -> str:
    """Pin a search to one exact place, so the Maps app opens its card."""
    return f"{maps_search_url(place)}&query_place_id={quote_plus(place_id)}"


def is_shortened(url: str) -> bool:
    match = _HOST.match(url)
    if match is None:
        return False
    return match.group(1).lower().rstrip(".") in SHORTENER_HOSTS


def _last_nonempty_line(text: str) -> str:
    """The place name usually sits on the line introducing the link."""
    for line in reversed(text.splitlines()):
        if line.strip():
            return line
    return ""


def _place_from_label(label: str) -> str | None:
    """Pull a searchable place name out of a link label."""
    label = re.sub(r"(?i)\bgoogle\s*(maps|карт\w*)\b", " ", label)
    label = label.replace("—", " ").replace("-", " ")
    names = [n.strip() for n in _LATIN_NAME.findall(label)]
    names = [n for n in names if len(n) >= 3]
    return max(names, key=len) if names else None


def sanitize_map_links(text: str) -> str:
    """Rewrite shortened links to Maps searches and flatten markdown links.

    Telegram messages go out as plain text, so `[label](url)` would be shown
    verbatim; emit `label: url` instead.
    """
    if not text:
        return text

    def fix_markdown(match: re.Match[str]) -> str:
        label, url = match.group(1).strip(), match.group(2)
        if is_shortened(url):
            place = _place_from_label(label)
            if place is None:
                return label
            url = maps_search_url(place)
        return f"{label}: {url}"

    text = _MARKDOWN_LINK.sub(fix_markdown, text)

    def fix_bare(match: re.Match[str]) -> str:
        url = match.group(0)
        trailing = ""
        while url and url[-1] in _TRAILING_PUNCT:
            url, trailing = url[:-1], url[-1] + trailing
        if not is_shortened(url):
            return url + trailing
        place = _place_from_label(_last_nonempty_line(text[: match.start()]))
        if place is None:
            return trailing.lstrip()
        return maps_search_url(place) + trailing

    return _BARE_URL.sub(fix_bare, text)
