-- ============================================
-- Миграция 001: Создание таблиц для воронки продаж MetaLiza
-- Дата: 2025-10-18
-- Префикс таблиц: metaliza_
-- ============================================

-- ============================================
-- 1. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
-- ============================================

CREATE TABLE IF NOT EXISTS metaliza_users (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE NOT NULL,
    tg_username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),

    -- Контакты для бесплатного доступа
    email VARCHAR(255),
    phone VARCHAR(50),

    -- Текущий тариф
    current_tariff VARCHAR(50),                       -- '1scan', '3scans', 'year', 'vip', 'free', NULL
    subscription_end_date TIMESTAMP,                  -- Дата окончания подписки (для year/vip/free)

    -- Воронка
    quiz_answer VARCHAR(50),                          -- relationships/money/energy/realization
    funnel_stage VARCHAR(50) DEFAULT 'start',         -- start/quiz/welcome/about/examples/pricing/paid

    -- Даты
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_metaliza_users_tg_id ON metaliza_users(tg_id);
CREATE INDEX IF NOT EXISTS idx_metaliza_users_subscription_end ON metaliza_users(subscription_end_date);
CREATE INDEX IF NOT EXISTS idx_metaliza_users_current_tariff ON metaliza_users(current_tariff);

-- Комментарии
COMMENT ON TABLE metaliza_users IS 'Пользователи MetaLiza бота';
COMMENT ON COLUMN metaliza_users.current_tariff IS '1scan/3scans/year/vip/free или NULL';
COMMENT ON COLUMN metaliza_users.subscription_end_date IS 'До какой даты активна подписка (year/vip/free)';

-- ============================================
-- 2. ТАБЛИЦА ТРАНЗАКЦИЙ (ПОКУПКИ)
-- ============================================

CREATE TABLE IF NOT EXISTS metaliza_transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,

    -- Информация о тарифе
    tariff VARCHAR(50) NOT NULL,                      -- '1scan', '3scans', 'year', 'vip', 'free'
    amount_rub DECIMAL(10, 2) DEFAULT 0,

    -- Платёжная система
    payment_provider VARCHAR(50),                     -- 'yookassa', 'tinkoff', 'manual', 'free'
    payment_id VARCHAR(255),
    payment_status VARCHAR(50) DEFAULT 'pending',     -- 'pending', 'paid', 'failed', 'refunded'

    -- Что получил пользователь
    scans_granted INTEGER DEFAULT 0,                  -- Для 1scan/3scans
    subscription_days_granted INTEGER DEFAULT 0,      -- Для year/vip/free

    -- Метаданные
    metadata JSONB,

    -- Даты
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,

    -- Внешний ключ
    FOREIGN KEY (user_id) REFERENCES metaliza_users(tg_id) ON DELETE CASCADE
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_metaliza_trans_user_id ON metaliza_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_metaliza_trans_payment_id ON metaliza_transactions(payment_id);
CREATE INDEX IF NOT EXISTS idx_metaliza_trans_status ON metaliza_transactions(payment_status);
CREATE INDEX IF NOT EXISTS idx_metaliza_trans_tariff ON metaliza_transactions(tariff);
CREATE INDEX IF NOT EXISTS idx_metaliza_trans_created_at ON metaliza_transactions(created_at);

COMMENT ON TABLE metaliza_transactions IS 'История покупок и активаций тарифов';

-- ============================================
-- 3. ТАБЛИЦА ИСПОЛЬЗОВАНИЯ СКАНОВ
-- ============================================

CREATE TABLE IF NOT EXISTS metaliza_scan_usage (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,

    -- Запрос
    request_text TEXT NOT NULL,
    photo_path TEXT,
    photo_base64 TEXT,

    -- Результат
    analysis_result TEXT,
    pdf_path TEXT,

    -- Метрики
    processing_time INTEGER,
    tokens_used INTEGER,
    api_cost_usd DECIMAL(10, 6),
    model_used VARCHAR(50) DEFAULT 'gpt-4o',

    -- Тариф в момент скана
    tariff_at_scan VARCHAR(50),

    -- Дата
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Внешний ключ
    FOREIGN KEY (user_id) REFERENCES metaliza_users(tg_id) ON DELETE CASCADE
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_metaliza_scan_user_id ON metaliza_scan_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_metaliza_scan_created_at ON metaliza_scan_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_metaliza_scan_tariff ON metaliza_scan_usage(tariff_at_scan);

COMMENT ON TABLE metaliza_scan_usage IS 'Каждое использование сканера';

-- ============================================
-- 4. ТАБЛИЦА ЗАЯВОК НА БЕСПЛАТНЫЙ ДОСТУП
-- ============================================

CREATE TABLE IF NOT EXISTS metaliza_free_access_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,

    -- Контакты
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),

    -- Параметры
    days_granted INTEGER DEFAULT 7,
    status VARCHAR(50) DEFAULT 'pending',             -- 'pending', 'approved', 'rejected', 'expired'

    -- Модерация
    approved_by BIGINT,
    rejection_reason TEXT,

    -- Даты
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    expires_at TIMESTAMP,

    -- Внешний ключ
    FOREIGN KEY (user_id) REFERENCES metaliza_users(tg_id) ON DELETE CASCADE
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_metaliza_free_user_id ON metaliza_free_access_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_metaliza_free_status ON metaliza_free_access_requests(status);
CREATE INDEX IF NOT EXISTS idx_metaliza_free_email ON metaliza_free_access_requests(email);

COMMENT ON TABLE metaliza_free_access_requests IS 'Заявки на бесплатный пробный доступ';

-- ============================================
-- 5. ТАБЛИЦА АНАЛИТИКИ ВОРОНКИ
-- ============================================

CREATE TABLE IF NOT EXISTS metaliza_funnel_analytics (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,

    -- Квиз
    quiz_answer VARCHAR(50),

    -- Этапы воронки
    reached_welcome BOOLEAN DEFAULT FALSE,
    reached_about BOOLEAN DEFAULT FALSE,
    reached_examples BOOLEAN DEFAULT FALSE,
    reached_pricing BOOLEAN DEFAULT FALSE,
    reached_payment BOOLEAN DEFAULT FALSE,
    completed_payment BOOLEAN DEFAULT FALSE,

    -- Использование
    first_scan_completed BOOLEAN DEFAULT FALSE,

    -- Дожимы
    followup_24h_sent BOOLEAN DEFAULT FALSE,
    followup_48h_sent BOOLEAN DEFAULT FALSE,
    followup_72h_sent BOOLEAN DEFAULT FALSE,

    -- Конверсия
    converted_at_stage VARCHAR(50),                   -- pricing/24h/48h/72h
    purchased_tariff VARCHAR(50),

    -- Даты
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    converted_at TIMESTAMP,

    -- Внешний ключ
    FOREIGN KEY (user_id) REFERENCES metaliza_users(tg_id) ON DELETE CASCADE,

    -- Один пользователь = одна запись
    UNIQUE(user_id)
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_metaliza_funnel_user_id ON metaliza_funnel_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_metaliza_funnel_quiz ON metaliza_funnel_analytics(quiz_answer);
CREATE INDEX IF NOT EXISTS idx_metaliza_funnel_converted ON metaliza_funnel_analytics(completed_payment);
CREATE INDEX IF NOT EXISTS idx_metaliza_funnel_stage ON metaliza_funnel_analytics(converted_at_stage);

COMMENT ON TABLE metaliza_funnel_analytics IS 'Аналитика прохождения воронки каждым пользователем';

-- ============================================
-- 6. VIEW ДЛЯ АНАЛИТИКИ
-- ============================================

-- Статистика по тарифам
CREATE OR REPLACE VIEW v_metaliza_tariff_stats AS
SELECT
    tariff,
    COUNT(*) as total_purchases,
    SUM(amount_rub) as total_revenue,
    AVG(amount_rub) as avg_check,
    COUNT(DISTINCT user_id) as unique_users
FROM metaliza_transactions
WHERE payment_status = 'paid'
GROUP BY tariff
ORDER BY total_revenue DESC;

-- Конверсия воронки
CREATE OR REPLACE VIEW v_metaliza_funnel_conversion AS
SELECT
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE reached_welcome) as reached_welcome,
    COUNT(*) FILTER (WHERE reached_about) as reached_about,
    COUNT(*) FILTER (WHERE reached_examples) as reached_examples,
    COUNT(*) FILTER (WHERE reached_pricing) as reached_pricing,
    COUNT(*) FILTER (WHERE reached_payment) as reached_payment,
    COUNT(*) FILTER (WHERE completed_payment) as completed_payment,
    COUNT(*) FILTER (WHERE first_scan_completed) as first_scan_completed,
    ROUND(100.0 * COUNT(*) FILTER (WHERE completed_payment) / NULLIF(COUNT(*), 0), 2) as conversion_rate
FROM metaliza_funnel_analytics;

-- Эффективность дожимов
CREATE OR REPLACE VIEW v_metaliza_followup_effectiveness AS
SELECT
    converted_at_stage,
    COUNT(*) as conversions,
    AVG(EXTRACT(EPOCH FROM (converted_at - created_at)) / 3600)::INTEGER as avg_hours_to_convert
FROM metaliza_funnel_analytics
WHERE completed_payment = TRUE AND converted_at_stage IS NOT NULL
GROUP BY converted_at_stage
ORDER BY conversions DESC;

-- Популярность сфер квиза
CREATE OR REPLACE VIEW v_metaliza_quiz_popularity AS
SELECT
    quiz_answer,
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE completed_payment) as converted_users,
    ROUND(100.0 * COUNT(*) FILTER (WHERE completed_payment) / NULLIF(COUNT(*), 0), 2) as conversion_rate
FROM metaliza_funnel_analytics
WHERE quiz_answer IS NOT NULL
GROUP BY quiz_answer
ORDER BY total_users DESC;

-- ============================================
-- 7. ФУНКЦИИ ДЛЯ БИЗНЕС-ЛОГИКИ
-- ============================================

-- Проверка активности подписки
CREATE OR REPLACE FUNCTION metaliza_is_subscription_active(p_user_id BIGINT)
RETURNS BOOLEAN AS $$
DECLARE
    v_tariff VARCHAR(50);
    v_end_date TIMESTAMP;
BEGIN
    SELECT current_tariff, subscription_end_date
    INTO v_tariff, v_end_date
    FROM metaliza_users
    WHERE tg_id = p_user_id;

    IF v_tariff IN ('year', 'vip', 'free') THEN
        RETURN v_end_date IS NOT NULL AND v_end_date > NOW();
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Подсчёт оставшихся сканов
CREATE OR REPLACE FUNCTION metaliza_get_remaining_scans(p_user_id BIGINT)
RETURNS INTEGER AS $$
DECLARE
    v_tariff VARCHAR(50);
    v_last_transaction_date TIMESTAMP;
    v_scans_granted INTEGER;
    v_scans_used INTEGER;
BEGIN
    SELECT current_tariff INTO v_tariff FROM metaliza_users WHERE tg_id = p_user_id;

    -- Подписка = безлимит
    IF v_tariff IN ('year', 'vip', 'free') THEN
        RETURN 999999;
    END IF;

    -- Лимитный тариф
    IF v_tariff IN ('1scan', '3scans') THEN
        SELECT created_at, scans_granted
        INTO v_last_transaction_date, v_scans_granted
        FROM metaliza_transactions
        WHERE user_id = p_user_id AND tariff = v_tariff AND payment_status = 'paid'
        ORDER BY created_at DESC
        LIMIT 1;

        IF v_last_transaction_date IS NULL THEN
            RETURN 0;
        END IF;

        SELECT COUNT(*)
        INTO v_scans_used
        FROM metaliza_scan_usage
        WHERE user_id = p_user_id AND created_at >= v_last_transaction_date;

        RETURN GREATEST(0, v_scans_granted - v_scans_used);
    END IF;

    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 8. ТРИГГЕРЫ
-- ============================================

CREATE OR REPLACE FUNCTION metaliza_update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_metaliza_users_updated_at
    BEFORE UPDATE ON metaliza_users
    FOR EACH ROW
    EXECUTE FUNCTION metaliza_update_updated_at();

-- ============================================
-- ЗАВЕРШЕНИЕ
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Миграция 001 для MetaLiza успешно применена!';
    RAISE NOTICE 'Созданы таблицы:';
    RAISE NOTICE '  - metaliza_users';
    RAISE NOTICE '  - metaliza_transactions';
    RAISE NOTICE '  - metaliza_scan_usage';
    RAISE NOTICE '  - metaliza_free_access_requests';
    RAISE NOTICE '  - metaliza_funnel_analytics';
END $$;
