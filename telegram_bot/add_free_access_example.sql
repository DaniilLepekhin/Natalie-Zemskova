-- ============================================
-- Быстрое добавление бесплатного доступа
-- Скопируй, отредактируй, выполни в базе metamethod_bot
-- ============================================

-- ШАБЛОН: Один доступ на 7 дней
INSERT INTO metaliza_free_access (email, phone, date_end, created_by, note)
VALUES ('email@example.com', '+79001234567', NOW() + INTERVAL '7 days', 'manual', 'Промо-акция');

-- Массовая выдача на 7 дней (например, участникам вебинара)
INSERT INTO metaliza_free_access (email, phone, date_end, created_by, note)
VALUES
    ('user1@mail.ru', NULL, NOW() + INTERVAL '7 days', 'webinar_oct', 'Участник вебинара 18.10'),
    ('user2@gmail.com', NULL, NOW() + INTERVAL '7 days', 'webinar_oct', 'Участник вебинара 18.10'),
    ('user3@yandex.ru', NULL, NOW() + INTERVAL '7 days', 'webinar_oct', 'Участник вебинара 18.10');

-- VIP-доступ на 30 дней
INSERT INTO metaliza_free_access (email, phone, date_end, created_by, note)
VALUES ('vip@example.com', '+79119876543', NOW() + INTERVAL '30 days', 'manual', 'VIP-клиент Октябрь');

-- Тестовый доступ на 3 дня
INSERT INTO metaliza_free_access (email, phone, date_end, created_by, note)
VALUES ('test@example.com', NULL, NOW() + INTERVAL '3 days', 'manual', 'Тестирование функционала');

-- ============================================
-- ПРОВЕРКА: Посмотреть все активные доступы
-- ============================================

SELECT
    email,
    phone,
    date_end::DATE as "Доступ до",
    EXTRACT(DAY FROM (date_end - NOW()))::INTEGER as "Дней осталось",
    CASE
        WHEN user_id IS NULL THEN '❌ Не активирован'
        ELSE '✅ Активирован'
    END as "Статус",
    note as "Примечание"
FROM metaliza_free_access
WHERE is_active = TRUE
  AND date_end > NOW()
ORDER BY date_end;
