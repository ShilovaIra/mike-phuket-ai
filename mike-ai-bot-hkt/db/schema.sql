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
    button_template TEXT NOT NULL
);

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
    button_template
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
    'Обменять с {name}'
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
    'Арендовать у {name}'
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
    'Забронировать с {name}'
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
    button_template = EXCLUDED.button_template;

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
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    referral_url = EXCLUDED.referral_url,
    blurb = EXCLUDED.blurb,
    logo_path = EXCLUDED.logo_path,
    is_active = EXCLUDED.is_active,
    sort_order = EXCLUDED.sort_order;
