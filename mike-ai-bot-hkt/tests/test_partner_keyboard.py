from __future__ import annotations

from buttons import (
    ASK_MIKE_BUTTON,
    BEACHES_BUTTON,
    NEARBY_BUTTON,
    REAL_ESTATE_BUTTON,
    WHERE_TO_EAT_BUTTON,
    build_reply_keyboard_rows,
)
from partners import PartnerType


def _type(
    slug: str,
    sort_order: int,
    label: str,
    *,
    is_menu_visible: bool = True,
) -> PartnerType:
    return PartnerType(
        slug=slug,
        is_menu_visible=is_menu_visible,
        sort_order=sort_order,
        button_label=label,
        topic_label=label.replace("\n", ""),
        intro="intro",
        fallback="fallback",
        caption_emoji="•",
        caption_cta="cta",
        button_template="{name}",
    )


def test_reply_keyboard_packs_two_up_with_ask_mike_alone():
    types = [
        _type("excursions", 30, "🇹🇭 \nЭкскурсии"),
        _type("money_exchange", 10, "💰 \nОбмен Рублей"),
        _type("vehicle_rental", 20, "🛵 \nАренда транспорта"),
    ]

    rows = build_reply_keyboard_rows(types)

    assert rows == [
        [WHERE_TO_EAT_BUTTON, BEACHES_BUTTON],
        [NEARBY_BUTTON, "💰 \nОбмен Рублей"],
        ["🛵 \nАренда транспорта", "🇹🇭 \nЭкскурсии"],
        [REAL_ESTATE_BUTTON],
        [ASK_MIKE_BUTTON],
    ]


def test_reply_keyboard_omits_hidden_partner_types():
    types = [
        _type("money_exchange", 10, "💰 \nОбмен Рублей"),
        _type(
            "vehicle_rental",
            20,
            "🛵 \nАренда транспорта",
            is_menu_visible=False,
        ),
        _type("excursions", 30, "🇹🇭 \nЭкскурсии"),
    ]

    rows = build_reply_keyboard_rows(types)

    assert rows == [
        [WHERE_TO_EAT_BUTTON, BEACHES_BUTTON],
        [NEARBY_BUTTON, "💰 \nОбмен Рублей"],
        ["🇹🇭 \nЭкскурсии", REAL_ESTATE_BUTTON],
        [ASK_MIKE_BUTTON],
    ]


def test_reply_keyboard_with_no_partners_still_ends_with_ask_mike_alone():
    rows = build_reply_keyboard_rows([])

    assert rows == [
        [WHERE_TO_EAT_BUTTON, BEACHES_BUTTON],
        [NEARBY_BUTTON, REAL_ESTATE_BUTTON],
        [ASK_MIKE_BUTTON],
    ]


def test_reply_keyboard_orders_partners_by_sort_order():
    types = [
        _type("vehicle_rental", 20, "vehicle"),
        _type("money_exchange", 5, "money"),
    ]

    rows = build_reply_keyboard_rows(types)

    assert rows[1] == [NEARBY_BUTTON, "money"]
    assert rows[2] == ["vehicle", REAL_ESTATE_BUTTON]
    assert rows[-1] == [ASK_MIKE_BUTTON]
