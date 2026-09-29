from __future__ import annotations

import re
from urllib.parse import urlparse

_PRECISE_PIN = re.compile(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)")
_VIEWPORT_PIN = re.compile(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")


def read_maps_pin(url: str) -> tuple[float, float] | None:
    """Latitude and longitude from a Google Maps link, when the link has a pin."""
    match = _PRECISE_PIN.search(url) or _VIEWPORT_PIN.search(url)
    if match is None:
        return None
    return float(match.group(1)), float(match.group(2))


_SHORT_HOSTS = {"maps.app.goo.gl", "goo.gl"}


def resolve_maps_link(url: str, follow) -> tuple[str, float, float] | None:
    """Return the long Maps URL and its pin. A short link is opened once."""
    pin = read_maps_pin(url)
    resolved = url
    host = (urlparse(url).hostname or "").lower()
    if pin is None and host in _SHORT_HOSTS:
        resolved = follow(url)
        pin = read_maps_pin(resolved)
    if pin is None:
        return None
    return resolved, pin[0], pin[1]


def follow_maps_redirect(url: str) -> str:
    import httpx

    response = httpx.get(url, follow_redirects=True, timeout=10.0)
    response.raise_for_status()
    return str(response.url)
