from __future__ import annotations

from uuid import uuid4

from partners import (
    FALLBACK,
    INTRO,
    Partner,
    build_partner_button_text,
    build_partner_caption_html,
    build_partner_cards,
    resolve_logo_path,
)


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


def test_empty_partners_returns_fallback_and_no_cards():
    text, cards = build_partner_cards([])
    assert text == FALLBACK
    assert cards == []


def test_nonempty_partners_return_intro_and_one_card_each():
    partners = [
        _partner(name="Alpha FX", blurb="Обмен в Равае", sort_order=1),
        _partner(
            name="Beta FX",
            referral_url="https://t.me/beta?start=ref",
            blurb=None,
            sort_order=2,
        ),
    ]

    text, cards = build_partner_cards(partners)

    assert text == INTRO
    assert len(cards) == 2
    assert cards[0].caption_html == (
        '<a href="https://t.me/alpha?start=ref">Alpha FX</a>\n\nОбмен в Равае'
    )
    assert cards[0].button_text == "Обменять с Alpha FX"
    assert cards[0].referral_url == "https://t.me/alpha?start=ref"
    assert cards[1].caption_html == '<a href="https://t.me/beta?start=ref">Beta FX</a>'
    assert cards[1].button_text == "Обменять с Beta FX"


def test_caption_escapes_html_in_name_and_blurb():
    partner = _partner(name="A<B>&C", blurb="x<y>&z")
    assert build_partner_caption_html(partner) == (
        '<a href="https://t.me/alpha?start=ref">A&lt;B&gt;&amp;C</a>\n\n'
        "x&lt;y&gt;&amp;z"
    )


def test_button_text_includes_partner_name():
    assert build_partner_button_text(_partner(name="Money Shop")) == (
        "Обменять с Money Shop"
    )


def test_resolve_logo_path_returns_none_when_missing():
    assert resolve_logo_path(None) is None
    assert resolve_logo_path("media/partners/does-not-exist.png") is None


def test_resolve_logo_path_finds_bundled_logos():
    money = resolve_logo_path("media/partners/moneyshop.jpeg")
    ex24 = resolve_logo_path("media/partners/ex24pro.png")
    assert money is not None and money.is_file()
    assert ex24 is not None and ex24.is_file()
