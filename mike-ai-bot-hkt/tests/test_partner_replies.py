from __future__ import annotations

from uuid import uuid4

from partners import Partner, PartnerType, build_partner_cards, resolve_logo_path


def _partner_type(**overrides) -> PartnerType:
    base = dict(
        slug="money_exchange",
        is_menu_visible=True,
        sort_order=10,
        button_label="💰 \nОбмен Рублей",
        topic_label="💰 Обмен",
        intro="Вот партнёры для обмена рублей:",
        fallback=(
            "Пока нет доступных партнёров по обмену. "
            "Напишите Майку — подскажу, что можно сделать."
        ),
        caption_emoji="💰",
        caption_cta="⬇️ Обменять сейчас ⬇️",
        button_template="Обменять с {name}",
    )
    base.update(overrides)
    return PartnerType(**base)


def _partner(**overrides) -> Partner:
    base = dict(
        id=uuid4(),
        name="Alpha FX",
        type="money_exchange",
        referral_url="https://t.me/alpha?start=ref",
        blurb="Обмен в Равае",
        sort_order=1,
        logo_path=None,
    )
    base.update(overrides)
    return Partner(**base)


def test_empty_partners_returns_type_fallback_and_no_cards():
    partner_type = _partner_type(
        fallback="Пока нет доступных партнёров по аренде транспорта. "
        "Напишите Майку — подскажу, что можно сделать."
    )

    text, cards = build_partner_cards([], partner_type)

    assert text == partner_type.fallback
    assert cards == []


def test_nonempty_partners_return_type_intro_and_one_card_each():
    partner_type = _partner_type()
    partners = [
        _partner(name="Alpha FX", blurb="Обмен в Равае", sort_order=1),
        _partner(
            name="Beta FX",
            referral_url="https://t.me/beta?start=ref",
            blurb=None,
            sort_order=2,
        ),
    ]

    text, cards = build_partner_cards(partners, partner_type)

    assert text == partner_type.intro
    assert len(cards) == 2
    assert cards[0].caption_html == (
        '💰 <a href="https://t.me/alpha?start=ref">Alpha FX</a> 💰\n\n'
        f"✅ Обмен в Равае\n\n{partner_type.caption_cta}"
    )
    assert cards[0].button_text == "Обменять с Alpha FX"
    assert cards[0].referral_url == "https://t.me/alpha?start=ref"
    assert cards[1].caption_html == (
        '💰 <a href="https://t.me/beta?start=ref">Beta FX</a> 💰\n\n'
        f"{partner_type.caption_cta}"
    )
    assert cards[1].button_text == "Обменять с Beta FX"


def test_same_builder_uses_vehicle_rental_copy():
    partner_type = _partner_type(
        slug="vehicle_rental",
        intro="Вот партнёры по аренде транспорта:",
        caption_emoji="🛵",
        caption_cta="⬇️ Арендовать сейчас ⬇️",
        button_template="Арендовать у {name}",
    )
    partners = [_partner(name="Bike Co", type="vehicle_rental", blurb="Скутеры")]

    text, cards = build_partner_cards(partners, partner_type)

    assert text == "Вот партнёры по аренде транспорта:"
    assert cards[0].button_text == "Арендовать у Bike Co"
    assert cards[0].caption_html == (
        '🛵 <a href="https://t.me/alpha?start=ref">Bike Co</a> 🛵\n\n'
        "✅ Скутеры\n\n"
        "⬇️ Арендовать сейчас ⬇️"
    )


def test_caption_escapes_html_in_name_and_blurb():
    from partners import build_partner_caption_html

    partner_type = _partner_type(caption_emoji="🇹🇭")
    partner = _partner(name="A<B>&C", blurb="x<y>&z")

    assert build_partner_caption_html(partner, partner_type) == (
        '🇹🇭 <a href="https://t.me/alpha?start=ref">A&lt;B&gt;&amp;C</a> 🇹🇭\n\n'
        f"✅ x&lt;y&gt;&amp;z\n\n{partner_type.caption_cta}"
    )


def test_resolve_logo_path_returns_none_when_missing():
    assert resolve_logo_path(None) is None
    assert resolve_logo_path("media/partners/does-not-exist.png") is None


def test_resolve_logo_path_finds_bundled_logos():
    money = resolve_logo_path("media/partners/moneyshop.jpeg")
    ex24 = resolve_logo_path("media/partners/ex24pro.png")
    excursions = resolve_logo_path("media/partners/excursions.png")
    boomerang = resolve_logo_path("media/partners/boomerang.jpeg")
    esim = resolve_logo_path("media/partners/esim.jpeg")
    assert money is not None and money.is_file()
    assert ex24 is not None and ex24.is_file()
    assert excursions is not None and excursions.is_file()
    assert boomerang is not None and boomerang.is_file()
    assert esim is not None and esim.is_file()
