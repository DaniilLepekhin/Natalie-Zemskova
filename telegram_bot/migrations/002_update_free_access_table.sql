-- ============================================
-- Миграция 002: Обновление таблицы бесплатного доступа
-- Дата: 2025-10-18
-- Описание: Изменяем логику - таблица хранит выданные доступы (не заявки)
-- ============================================

-- Удаляем старую таблицу заявок
DROP TABLE IF EXISTS metaliza_free_access_requests CASCADE;

-- Создаём новую таблицу выданных бесплатных доступов
CREATE TABLE IF NOT EXISTS metaliza_free_access (
    id SERIAL PRIMARY KEY,

    -- Контакты (ключ для проверки)
    email VARCHAR(255) UNIQUE NOT NULL,               -- Почта в нижнем регистре
    phone VARCHAR(50),

    -- Даты доступа
    date_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- С какой даты доступ
    date_end TIMESTAMP NOT NULL,                      -- До какой даты доступ

    -- Связь с пользователем (опционально, может быть NULL пока не активирован)
    user_id BIGINT,

    -- Метаданные
    created_by VARCHAR(100),                          -- Кто выдал доступ (админ/система)
    note TEXT,                                        -- Примечание (откуда пришёл, промо и т.д.)

    -- Активация
    activated_at TIMESTAMP,                           -- Когда пользователь активировал доступ
    is_active BOOLEAN DEFAULT TRUE,                   -- Активен ли доступ

    -- Даты
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Внешний ключ (может быть NULL)
    FOREIGN KEY (user_id) REFERENCES metaliza_users(tg_id) ON DELETE SET NULL
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_metaliza_free_email ON metaliza_free_access(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_metaliza_free_user_id ON metaliza_free_access(user_id);
CREATE INDEX IF NOT EXISTS idx_metaliza_free_date_end ON metaliza_free_access(date_end);
CREATE INDEX IF NOT EXISTS idx_metaliza_free_is_active ON metaliza_free_access(is_active);

-- Комментарии
COMMENT ON TABLE metaliza_free_access IS 'Выданные бесплатные доступы к сканеру';
COMMENT ON COLUMN metaliza_free_access.email IS 'Email в нижнем регистре для проверки';
COMMENT ON COLUMN metaliza_free_access.date_end IS 'До какой даты действует бесплатный доступ';
COMMENT ON COLUMN metaliza_free_access.user_id IS 'tg_id пользователя (заполняется при активации)';
COMMENT ON COLUMN metaliza_free_access.activated_at IS 'Когда пользователь ввёл почту в боте и активировал доступ';

-- Функция для проверки бесплатного доступа по почте
CREATE OR REPLACE FUNCTION metaliza_check_free_access(p_email VARCHAR)
RETURNS TABLE(
    has_access BOOLEAN,
    date_end TIMESTAMP,
    days_remaining INTEGER
) AS $$
DECLARE
    v_email_lower VARCHAR;
BEGIN
    -- Приводим к нижнему регистру
    v_email_lower := LOWER(TRIM(p_email));

    -- Проверяем наличие активного доступа
    RETURN QUERY
    SELECT
        TRUE as has_access,
        fa.date_end,
        GREATEST(0, EXTRACT(DAY FROM (fa.date_end - NOW()))::INTEGER) as days_remaining
    FROM metaliza_free_access fa
    WHERE LOWER(fa.email) = v_email_lower
      AND fa.is_active = TRUE
      AND fa.date_end > NOW()
    LIMIT 1;

    -- Если не нашли, возвращаем FALSE
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::TIMESTAMP, 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Функция для активации бесплатного доступа
CREATE OR REPLACE FUNCTION metaliza_activate_free_access(
    p_email VARCHAR,
    p_user_id BIGINT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_email_lower VARCHAR;
    v_date_end TIMESTAMP;
BEGIN
    v_email_lower := LOWER(TRIM(p_email));

    -- Проверяем и активируем доступ
    UPDATE metaliza_free_access
    SET
        user_id = p_user_id,
        activated_at = NOW(),
        updated_at = NOW()
    WHERE LOWER(email) = v_email_lower
      AND is_active = TRUE
      AND date_end > NOW()
      AND user_id IS NULL  -- Ещё не активирован
    RETURNING date_end INTO v_date_end;

    IF FOUND THEN
        -- Обновляем пользователя
        UPDATE metaliza_users
        SET
            current_tariff = 'free',
            subscription_end_date = v_date_end,
            email = v_email_lower,
            updated_at = NOW()
        WHERE tg_id = p_user_id;

        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автообновления updated_at
CREATE TRIGGER update_metaliza_free_access_updated_at
    BEFORE UPDATE ON metaliza_free_access
    FOR EACH ROW
    EXECUTE FUNCTION metaliza_update_updated_at();

-- Примеры данных для теста (закомментировано)
-- INSERT INTO metaliza_free_access (email, phone, date_end, created_by, note)
-- VALUES
--   ('test@example.com', '+79001234567', NOW() + INTERVAL '7 days', 'admin', 'Тестовый доступ'),
--   ('promo@test.ru', NULL, NOW() + INTERVAL '14 days', 'promo_campaign', 'Промо-акция');

-- Завершение
DO $$
BEGIN
    RAISE NOTICE '✅ Миграция 002 успешно применена!';
    RAISE NOTICE 'Таблица metaliza_free_access создана';
    RAISE NOTICE 'Функции metaliza_check_free_access() и metaliza_activate_free_access() добавлены';
END $$;
