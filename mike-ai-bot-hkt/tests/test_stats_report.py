from db.store import BotStats, TopicCount
from partners import PartnerType
from stats_report import format_bot_stats


def _stats(**overrides) -> BotStats:
    values = dict(
        total_users=100,
        new_users_today=5,
        active_today=12,
        new_users_7d=20,
        topics_all_time={
            "beaches": TopicCount(unique_users=20, taps=24),
            "real_estate": TopicCount(unique_users=8, taps=9),
        },
        topics_7d={
            "beaches": TopicCount(unique_users=12, taps=18),
            "real_estate": TopicCount(unique_users=5, taps=6),
        },
        leads_all_time=8,
        leads_7d=2,
        users_by_first_source={"instagram": 3, "unknown": 97},
    )
    values.update(overrides)
    return BotStats(**values)


def test_format_bot_stats_shows_users_topics_and_taps():
    stats = BotStats(
        total_users=100,
        new_users_today=5,
        active_today=12,
        new_users_7d=20,
        topics_all_time={
            "beaches": TopicCount(unique_users=20, taps=24),
            "real_estate": TopicCount(unique_users=8, taps=9),
        },
        topics_7d={
            "beaches": TopicCount(unique_users=12, taps=18),
            "real_estate": TopicCount(unique_users=5, taps=6),
        },
        leads_all_time=8,
        leads_7d=2,
        users_by_first_source={"instagram": 3, "unknown": 97},
    )

    text = format_bot_stats(stats)

    assert "Новые сегодня: 5" in text
    assert "Новые пользователи: 20" in text
    assert "🏖 Пляжи: 12 users (18 taps)" in text
    assert "🏖 Пляжи: 20 users (24 taps)" in text
    assert "За 7 дней: 5 users (6 taps) → 2 заявки" in text
    assert "Всё время: 8 users (9 taps) → 8 заявок" in text


def test_format_bot_stats_lists_first_source_counts_with_labels():
    stats = BotStats(
        total_users=100,
        new_users_today=5,
        active_today=12,
        new_users_7d=20,
        topics_all_time={},
        topics_7d={},
        leads_all_time=0,
        leads_7d=0,
        users_by_first_source={"instagram": 3, "unknown": 97},
    )

    text = format_bot_stats(stats)

    assert "Instagram: 3" in text
    assert "Неизвестно: 97" in text


def test_format_bot_stats_places_sources_between_users_and_7d():
    stats = BotStats(
        total_users=10,
        new_users_today=1,
        active_today=2,
        new_users_7d=3,
        topics_all_time={},
        topics_7d={},
        leads_all_time=0,
        leads_7d=0,
        users_by_first_source={"instagram": 4},
    )

    text = format_bot_stats(stats)
    users_idx = text.index("Активны сегодня:")
    sources_idx = text.index("Источники:")
    week_idx = text.index("За 7 дней:")

    assert users_idx < sources_idx < week_idx


def test_format_bot_stats_shows_dash_when_no_sources():
    stats = BotStats(
        total_users=0,
        new_users_today=0,
        active_today=0,
        new_users_7d=0,
        topics_all_time={},
        topics_7d={},
        leads_all_time=0,
        leads_7d=0,
        users_by_first_source={},
    )

    text = format_bot_stats(stats)
    sources_block = text.split("Источники:")[1].split("За 7 дней:")[0]

    assert "—" in sources_block
    assert "Instagram" not in sources_block


def test_format_bot_stats_orders_sources_by_count_desc():
    stats = BotStats(
        total_users=10,
        new_users_today=0,
        active_today=0,
        new_users_7d=0,
        topics_all_time={},
        topics_7d={},
        leads_all_time=0,
        leads_7d=0,
        users_by_first_source={"instagram": 2, "facebook": 5, "unknown": 3},
    )

    text = format_bot_stats(stats)
    sources_block = text.split("Источники:")[1].split("За 7 дней:")[0]
    facebook_idx = sources_block.index("Facebook:")
    unknown_idx = sources_block.index("Неизвестно:")
    instagram_idx = sources_block.index("Instagram:")

    assert facebook_idx < unknown_idx < instagram_idx


def test_format_bot_stats_title_cases_unknown_source_keys():
    stats = BotStats(
        total_users=1,
        new_users_today=0,
        active_today=0,
        new_users_7d=0,
        topics_all_time={},
        topics_7d={},
        leads_all_time=0,
        leads_7d=0,
        users_by_first_source={"tiktok": 1},
    )

    text = format_bot_stats(stats)

    assert "Tiktok: 1" in text


def test_format_bot_stats_uses_partner_type_topic_labels():
    stats = BotStats(
        total_users=10,
        new_users_today=1,
        active_today=2,
        new_users_7d=3,
        topics_all_time={
            "vehicle_rental": TopicCount(unique_users=4, taps=7),
        },
        topics_7d={
            "vehicle_rental": TopicCount(unique_users=2, taps=3),
        },
        leads_all_time=0,
        leads_7d=0,
        users_by_first_source={},
    )
    partner_types = [
        PartnerType(
            slug="vehicle_rental",
            is_menu_visible=True,
            sort_order=20,
            button_label="🛵 \nАренда транспорта",
            topic_label="🛵 Аренда транспорта",
            intro="i",
            fallback="f",
            caption_emoji="🛵",
            caption_cta="c",
            button_template="{name}",
        )
    ]

    text = format_bot_stats(stats, partner_types=partner_types)

    assert "🛵 Аренда транспорта: 2 users (3 taps)" in text
    assert "🛵 Аренда транспорта: 4 users (7 taps)" in text


def test_format_bot_stats_fits_telegram_limit_when_first_sources_are_unique_click_ids():
    sources = {
        "instagram": 22,
        "unknown": 22,
        "instagram_stories": 7,
        "telegram_channel": 6,
        "tiktok": 5,
        "restaurant_qr": 2,
    }
    for i in range(200):
        sources[f"TgTrack-PJ{i:016x}"] = 1

    text = format_bot_stats(_stats(users_by_first_source=sources))

    assert len(text) <= 4096
    assert "Instagram: 22" in text
    assert "Неизвестно: 22" in text
    assert "TgTrack: 200" in text
    assert "TgTrack-PJ" not in text
    assert "Недвижимость:" in text


def test_format_bot_stats_fits_telegram_limit_when_many_distinct_campaign_sources():
    sources = {f"campaign_{i:04d}": 1 for i in range(80)}

    text = format_bot_stats(_stats(users_by_first_source=sources))

    assert len(text) <= 4096
    assert "Другие:" in text
    assert text.count("\n  Campaign_") <= 20
