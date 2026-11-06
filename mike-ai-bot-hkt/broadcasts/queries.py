INSERT_BROADCAST_RETURNING = """
INSERT INTO broadcasts (text, scheduled_at, button_url, button_label)
VALUES ($1, $2, $3, $4)
RETURNING id, text, scheduled_at, status, button_url, button_label
"""

SELECT_BROADCASTS_ORDERED_BY_SCHEDULE = """
SELECT id, text, scheduled_at, status, button_url, button_label
FROM broadcasts
ORDER BY scheduled_at ASC, created_at ASC
"""

SELECT_BROADCAST_STATUS_BY_ID = "SELECT status FROM broadcasts WHERE id = $1"

UPDATE_SCHEDULED_BROADCAST = """
UPDATE broadcasts
SET text = $2,
    scheduled_at = $3,
    button_url = $4,
    button_label = $5
WHERE id = $1 AND status = 'scheduled'
RETURNING id, text, scheduled_at, status, button_url, button_label
"""

DELETE_BROADCAST_BY_ID = "DELETE FROM broadcasts WHERE id = $1"

MARK_DUE_SCHEDULED_BROADCASTS_SENT = """
UPDATE broadcasts
SET status = 'sent'
WHERE status = 'scheduled' AND scheduled_at <= $1
RETURNING id, text, button_url, button_label
"""

SELECT_UNBLOCKED_TELEGRAM_IDENTITIES = """
SELECT u.id AS user_id, i.external_id
FROM identities i
JOIN users u ON u.id = i.user_id
WHERE i.channel = 'telegram'
  AND u.follow_up_blocked_at IS NULL
ORDER BY i.created_at ASC
"""

INSERT_CLAIMED_BROADCAST_FOLLOW_UP_JOB = """
INSERT INTO follow_up_jobs (
    user_id, kind, topic, scheduled_at, status
)
VALUES ($1, 'broadcast', NULL, $2, 'claimed')
RETURNING id
"""

INSERT_BROADCAST_LIST_RETURNING = """
INSERT INTO broadcast_lists (name)
VALUES ($1)
RETURNING id, name
"""

SELECT_BROADCAST_LIST_EXISTS = "SELECT 1 FROM broadcast_lists WHERE id = $1"

SELECT_INTERVAL_BROADCAST_FOR_LIST = (
    "SELECT 1 FROM interval_broadcasts WHERE list_id = $1 LIMIT 1"
)

DELETE_BROADCAST_LIST_BY_ID = "DELETE FROM broadcast_lists WHERE id = $1"

INSERT_BROADCAST_LIST_MESSAGE_AT_END = """
INSERT INTO broadcast_list_messages (
    list_id, text, position, button_url, button_label
)
VALUES (
    $1,
    $2,
    COALESCE(
        (SELECT MAX(position) FROM broadcast_list_messages WHERE list_id = $1),
        0
    ) + 1,
    $3,
    $4
)
RETURNING id, text, button_url, button_label
"""

SELECT_BROADCAST_LISTS_BY_CREATED_AT = """
SELECT id, name
FROM broadcast_lists
ORDER BY created_at ASC
"""

SELECT_BROADCAST_LIST_MESSAGES_IN_ORDER = """
SELECT id, list_id, text, button_url, button_label
FROM broadcast_list_messages
ORDER BY position ASC, created_at ASC
"""

SELECT_BROADCAST_LIST_MESSAGE_IN_LIST = """
SELECT id, position
FROM broadcast_list_messages
WHERE id = $1 AND list_id = $2
"""

SELECT_BROADCAST_LIST_MESSAGE_WITH_LOWER_POSITION = """
SELECT id, position
FROM broadcast_list_messages
WHERE list_id = $1 AND position < $2
ORDER BY position DESC
LIMIT 1
"""

SELECT_BROADCAST_LIST_MESSAGE_WITH_HIGHER_POSITION = """
SELECT id, position
FROM broadcast_list_messages
WHERE list_id = $1 AND position > $2
ORDER BY position ASC
LIMIT 1
"""

UPDATE_BROADCAST_LIST_MESSAGE_POSITION = (
    "UPDATE broadcast_list_messages SET position = $2 WHERE id = $1"
)

SELECT_INTERVAL_BROADCASTS_WITH_LIST = """
SELECT b.id, b.list_id, b.scheduled_at, b.interval_days, b.last_message_id,
       l.name AS list_name
FROM interval_broadcasts b
JOIN broadcast_lists l ON l.id = b.list_id
ORDER BY b.scheduled_at ASC, b.created_at ASC
"""

SELECT_INTERVAL_BROADCAST_WITH_LIST_BY_ID = """
SELECT b.id, b.list_id, b.scheduled_at, b.interval_days, b.last_message_id,
       l.name AS list_name
FROM interval_broadcasts b
JOIN broadcast_lists l ON l.id = b.list_id
WHERE b.id = $1
"""

SELECT_MESSAGES_FOR_LISTS_IN_ORDER = """
SELECT id, list_id, text, button_url, button_label
FROM broadcast_list_messages
WHERE list_id = ANY($1::uuid[])
ORDER BY position ASC, created_at ASC
"""

INSERT_INTERVAL_BROADCAST_RETURNING_ID = """
INSERT INTO interval_broadcasts (list_id, scheduled_at, interval_days)
VALUES ($1, $2, $3)
RETURNING id
"""

UPDATE_INTERVAL_BROADCAST_DAYS = """
UPDATE interval_broadcasts
SET interval_days = $2
WHERE id = $1
RETURNING id
"""

UPDATE_INTERVAL_BROADCAST_SCHEDULED_AT = """
UPDATE interval_broadcasts
SET scheduled_at = $2
WHERE id = $1
RETURNING id
"""

UPDATE_INTERVAL_BROADCAST_DAYS_AND_SCHEDULED_AT = """
UPDATE interval_broadcasts
SET interval_days = $2, scheduled_at = $3
WHERE id = $1
RETURNING id
"""

SELECT_INTERVAL_BROADCAST_EXISTS = (
    "SELECT 1 FROM interval_broadcasts WHERE id = $1"
)

DELETE_INTERVAL_BROADCAST = "DELETE FROM interval_broadcasts WHERE id = $1"

LOCK_DUE_INTERVAL_BROADCASTS = """
SELECT id, list_id, scheduled_at, interval_days, last_message_id
FROM interval_broadcasts
WHERE scheduled_at <= $1
FOR UPDATE
"""

UPDATE_INTERVAL_BROADCAST_SCHEDULED_AT_ONLY = (
    "UPDATE interval_broadcasts SET scheduled_at = $2 WHERE id = $1"
)

UPDATE_INTERVAL_BROADCAST_LAST_MESSAGE_AND_SCHEDULED_AT = """
UPDATE interval_broadcasts
SET last_message_id = $2, scheduled_at = $3
WHERE id = $1
"""
