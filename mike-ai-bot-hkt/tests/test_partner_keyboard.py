from __future__ import annotations

from partners import PartnerType, build_partner_keyboard_rows


def _type(slug: str, sort_order: int, label: str) -> PartnerType:
    return PartnerType(
        slug=slug,
        is_menu_visible=True,
        sort_order=sort_order,
        button_label=label,
        topic_label=label.replace("\n", ""),
        intro="intro",
        fallback="fallback",
        caption_emoji="•",
        caption_cta="cta",
        button_template="{name}",
    )


def test_partner_keyboard_rows_one_button_per_row_in_sort_order():
    types = [
        _type("excursions", 30, "🇹🇭 \nЭкскурсии"),
        _type("money_exchange", 10, "💰 \nОбмен Рублей"),
        _type("vehicle_rental", 20, "🛵 \nАренда транспорта"),
    ]

    rows = build_partner_keyboard_rows(types)

    assert rows == [
        ["💰 \nОбмен Рублей"],
        ["🛵 \nАренда транспорта"],
        ["🇹🇭 \nЭкскурсии"],
    ]


def test_partner_keyboard_rows_empty_when_no_types():
    assert build_partner_keyboard_rows([]) == []
