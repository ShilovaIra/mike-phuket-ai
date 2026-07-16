from db.store import BotStats, TopicCount
from stats_report import format_bot_stats


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
    )

    text = format_bot_stats(stats)

    assert "Новые сегодня: 5" in text
    assert "Новые пользователи: 20" in text
    assert "🏖 Пляжи: 12 users (18 taps)" in text
    assert "🏖 Пляжи: 20 users (24 taps)" in text
    assert "За 7 дней: 5 users (6 taps) → 2 заявки" in text
    assert "Всё время: 8 users (9 taps) → 8 заявок" in text
