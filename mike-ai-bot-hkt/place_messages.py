"""Turn one model answer into one outgoing message per place."""

from __future__ import annotations

import re
from dataclasses import dataclass

_MAPS_URL = re.compile(r"https?://\S*google\.com/maps/\S+")


@dataclass(frozen=True)
class OutgoingMessage:
    text: str
    is_place: bool


def _has_maps_link(block: str) -> bool:
    return "google.com/maps" in block


def _has_link(block: str) -> bool:
    return "https://" in block or "http://" in block


def _cut_before_next_place(block: str, previous_end: int, url_start: int) -> int:
    """The next place starts on the line above its Maps link."""
    url_line = block.rfind("\n", previous_end, url_start)
    if url_line == -1:
        return previous_end
    name_line = block.rfind("\n", previous_end, url_line)
    if name_line == -1:
        return url_line + 1
    return name_line + 1


def _one_place_per_block(blocks: list[str]) -> list[str]:
    expanded: list[str] = []
    for block in blocks:
        matches = list(_MAPS_URL.finditer(block))
        if len(matches) < 2:
            expanded.append(block)
            continue
        start = 0
        for index, match in enumerate(matches):
            if index == 0:
                continue
            cut = _cut_before_next_place(block, matches[index - 1].end(), match.start())
            expanded.append(block[start:cut].strip())
            start = cut
        expanded.append(block[start:].strip())
    return [block for block in expanded if block]


def place_messages(answer: str) -> list[OutgoingMessage]:
    text = answer.strip()
    if text.count("google.com/maps") < 2:
        return [OutgoingMessage(text, is_place="google.com/maps" in text)]

    blocks = _one_place_per_block(
        [block.strip() for block in text.split("\n\n") if block.strip()]
    )
    messages: list[OutgoingMessage] = []
    pending: list[str] = []
    for index, block in enumerate(blocks):
        place_still_coming = any(_has_maps_link(later) for later in blocks[index + 1 :])
        if _has_maps_link(block):
            messages.append(
                OutgoingMessage("\n\n".join([*pending, block]), is_place=True)
            )
            pending = []
            continue
        if _has_link(block) and place_still_coming:
            pending.append(block)
            continue
        if not messages:
            continue
        if place_still_coming:
            previous = messages[-1]
            messages[-1] = OutgoingMessage(
                f"{previous.text}\n\n{block}", is_place=previous.is_place
            )
            continue
        messages.append(OutgoingMessage(block, is_place=False))
    return messages
