from db.store import TopicCount
from partners import PartnerType
from topic_labels import labeled_topic_rows


def test_labeled_topic_rows_uses_builtin_and_partner_type_labels():
    topics = {
        "beaches": TopicCount(unique_users=2, taps=3),
        "money_exchange": TopicCount(unique_users=1, taps=1),
    }
    partner_types = [
        PartnerType(
            slug="money_exchange",
            is_menu_visible=True,
            sort_order=10,
            button_label="💰 \nОбмен Рублей",
            topic_label="💰 Обмен",
            intro="i",
            fallback="f",
            caption_emoji="💰",
            caption_cta="c",
            button_template="{name}",
        )
    ]

    rows = labeled_topic_rows(topics, partner_types)

    by_slug = {row["slug"]: row for row in rows}
    assert by_slug["beaches"] == {
        "slug": "beaches",
        "label": "🏖 Пляжи",
        "unique_users": 2,
        "taps": 3,
    }
    assert by_slug["money_exchange"] == {
        "slug": "money_exchange",
        "label": "💰 Обмен",
        "unique_users": 1,
        "taps": 1,
    }


def test_labeled_topic_rows_uses_bez_nazvaniya_for_unknown_slug():
    topics = {"legacy_promo": TopicCount(unique_users=4, taps=9)}

    rows = labeled_topic_rows(topics, partner_types=[])

    assert rows == [
        {
            "slug": "legacy_promo",
            "label": "Без названия",
            "unique_users": 4,
            "taps": 9,
        }
    ]
