CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_source TEXT NOT NULL DEFAULT 'unknown',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    external_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (channel, external_id)
);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'unknown',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS one_active_conversation_per_user
    ON conversations (user_id)
    WHERE status = 'active';

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations (id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS messages_conversation_created
    ON messages (conversation_id, created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS topic_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS topic_events_topic_created
    ON topic_events (topic, created_at DESC);

CREATE INDEX IF NOT EXISTS topic_events_user_topic
    ON topic_events (user_id, topic, created_at DESC);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations (id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    snapshot JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (conversation_id)
);

CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    payload_ref TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    attempts INT NOT NULL DEFAULT 0,
    next_retry_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS webhook_events_pending
    ON webhook_events (status, next_retry_at)
    WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS partner_types (
    slug TEXT PRIMARY KEY,
    is_menu_visible BOOLEAN NOT NULL DEFAULT true,
    sort_order INT NOT NULL DEFAULT 0,
    button_label TEXT NOT NULL,
    topic_label TEXT NOT NULL,
    intro TEXT NOT NULL,
    fallback TEXT NOT NULL,
    caption_emoji TEXT NOT NULL,
    caption_cta TEXT NOT NULL,
    button_template TEXT NOT NULL,
    follow_up_text TEXT NOT NULL DEFAULT ''
);

ALTER TABLE partner_types
    ADD COLUMN IF NOT EXISTS follow_up_text TEXT NOT NULL DEFAULT '';

INSERT INTO partner_types (
    slug,
    is_menu_visible,
    sort_order,
    button_label,
    topic_label,
    intro,
    fallback,
    caption_emoji,
    caption_cta,
    button_template,
    follow_up_text
)
VALUES
(
    'money_exchange',
    true,
    10,
    E'💰 \nОбмен Рублей',
    '💰 Обмен',
    'Вот партнёры для обмена рублей:',
    'Пока нет доступных партнёров по обмену. Напишите Майку — подскажу, что можно сделать.',
    '💰',
    '⬇️ Обменять сейчас ⬇️',
    'Обменять с {name}',
    'Как прошел обмен? Нужна ли ещё помощь? 😊'
),
(
    'vehicle_rental',
    true,
    20,
    E'🛵 \nАренда транспорта',
    '🛵 Аренда транспорта',
    'Вот партнёры по аренде транспорта:',
    'Пока нет доступных партнёров по аренде транспорта. Напишите Майку — подскажу, что можно сделать.',
    '🛵',
    '⬇️ Арендовать сейчас ⬇️',
    'Арендовать у {name}',
    ''
),
(
    'excursions',
    true,
    30,
    E'🇹🇭 \nЭкскурсии',
    '🇹🇭 Экскурсии',
    'Вот партнёры по экскурсиям:',
    'Пока нет доступных партнёров по экскурсиям. Напишите Майку — подскажу, что можно сделать.',
    '🇹🇭',
    '⬇️ Забронировать сейчас ⬇️',
    'Забронировать с {name}',
    'Как все прошло? Получилось ли воспользоваться рекомендацией? 😊'
),
(
    'esim',
    true,
    40,
    E'📱 \neSIM',
    '📱 eSIM',
    'Чтобы в любой стране оставаться на связи, можно приобрести eSIM в этом боте:',
    'Пока нет доступного бота для покупки eSIM. Напишите Майку — подскажу, что можно сделать.',
    '📱',
    '⬇️ Купить eSIM ⬇️',
    'Купить eSIM',
    ''
)
ON CONFLICT (slug) DO UPDATE SET
    is_menu_visible = EXCLUDED.is_menu_visible,
    sort_order = EXCLUDED.sort_order,
    button_label = EXCLUDED.button_label,
    topic_label = EXCLUDED.topic_label,
    intro = EXCLUDED.intro,
    fallback = EXCLUDED.fallback,
    caption_emoji = EXCLUDED.caption_emoji,
    caption_cta = EXCLUDED.caption_cta,
    button_template = EXCLUDED.button_template,
    follow_up_text = EXCLUDED.follow_up_text;

CREATE TABLE IF NOT EXISTS partners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    referral_url TEXT NOT NULL,
    blurb TEXT,
    logo_path TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE partners ADD COLUMN IF NOT EXISTS logo_path TEXT;

DO $$
BEGIN
    ALTER TABLE partners
        ADD CONSTRAINT partners_type_fkey
        FOREIGN KEY (type) REFERENCES partner_types (slug) ON DELETE RESTRICT;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS partners_type_active_sort
    ON partners (type, sort_order)
    WHERE is_active;

INSERT INTO partners (id, name, type, referral_url, blurb, logo_path, is_active, sort_order)
VALUES
(
    '00000000-0000-4000-8000-000000000001',
    'Money Shop',
    'money_exchange',
    'https://moneyshopphuket.online/links/pp413',
    'Money Shop - Сеть обменных офисов на Пхукете!',
    'media/partners/moneyshop.jpeg',
    true,
    1
),
(
    '00000000-0000-4000-8000-000000000002',
    'Ex24.pro',
    'money_exchange',
    'https://ex24qr.com/epihelgnld',
    'Лицензированный обмен валюты. Таиланд, Вьетнам, ОАЭ, Китай, Бали. Переводы по всему миру.',
    'media/partners/ex24pro.png',
    true,
    2
),
(
    '00000000-0000-4000-8000-000000000003',
    'Остров Сокровищ',
    'excursions',
    'https://tisland.link/excurs?ref=72s5z3yp3jb79r7',
    'С 2003 года в туризме. Авторские групповые и индивидуальные экскурсии.',
    'media/partners/excursions.png',
    true,
    1
),
(
    '00000000-0000-4000-8000-000000000004',
    'Boomerang',
    'vehicle_rental',
    'https://boomerang.rent/catalog/?utm_source=MikePhuketAIBot',
    'Boomerang - надежный сервис аренды автомобилей и мотобайков на Пхукете. Доставка по всему острову.',
    'media/partners/boomerang.jpeg',
    true,
    1
),
(
    '00000000-0000-4000-8000-000000000005',
    'Mike eSIM',
    'esim',
    'https://t.me/Mike_esim_bot',
    '',
    'media/partners/esim.jpeg',
    true,
    1
)
-- Operators own every other column after the first insert; logos change only by deploy.
ON CONFLICT (id) DO UPDATE SET
    logo_path = EXCLUDED.logo_path;

UPDATE partners
SET logo_path = 'media/partners/esim.jpeg'
WHERE type = 'esim';

CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_inbound_at TIMESTAMPTZ;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS follow_up_blocked_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS follow_up_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('partner_topic', 'win_back')),
    topic TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'claimed', 'sent', 'cancelled', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at TIMESTAMPTZ,
    last_error TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS one_pending_partner_follow_up_per_user
    ON follow_up_jobs (user_id)
    WHERE status = 'pending' AND kind = 'partner_topic';

CREATE UNIQUE INDEX IF NOT EXISTS one_pending_win_back_per_user
    ON follow_up_jobs (user_id)
    WHERE status = 'pending' AND kind = 'win_back';

CREATE INDEX IF NOT EXISTS follow_up_jobs_due
    ON follow_up_jobs (status, scheduled_at)
    WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS partner_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_access (
    partner_user_id UUID NOT NULL REFERENCES partner_users (id) ON DELETE CASCADE,
    partner_id UUID NOT NULL REFERENCES partners (id) ON DELETE CASCADE,
    PRIMARY KEY (partner_user_id, partner_id)
);

CREATE TABLE IF NOT EXISTS partner_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id UUID NOT NULL REFERENCES partners (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_referral_clicks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    view_id UUID NOT NULL REFERENCES partner_views (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
