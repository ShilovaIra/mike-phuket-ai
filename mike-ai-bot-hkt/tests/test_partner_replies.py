from __future__ import annotations

from uuid import uuid4

from partners import Partner, build_partner_list_replies

FALLBACK = (
    "Пока нет доступных партнёров по обмену. "
    "Напишите Майку — подскажу, что можно сделать."
)
INTRO = "Вот партнёры для обмена рублей:"


def test_empty_partners_returns_only_fallback():
    assert build_partner_list_replies([]) == [FALLBACK]


def test_nonempty_partners_return_intro_then_one_message_each():
    partners = [
        Partner(
            id=uuid4(),
            name="Alpha FX",
            type="money_exchange",
            referral_url="https://t.me/alpha?start=ref",
            blurb="Обмен в Равае",
            sort_order=1,
        ),
        Partner(
            id=uuid4(),
            name="Beta FX",
            type="money_exchange",
            referral_url="https://t.me/beta?start=ref",
            blurb=None,
            sort_order=2,
        ),
    ]

    assert build_partner_list_replies(partners) == [
        INTRO,
        "Alpha FX\n\nОбмен в Равае\n\nhttps://t.me/alpha?start=ref",
        "Beta FX\n\nhttps://t.me/beta?start=ref",
    ]
