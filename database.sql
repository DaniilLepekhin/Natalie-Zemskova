-- База данных для сбора кейсов Мета-Метод бота
-- Создаём БД и структуру таблиц

-- Создание базы данных (выполняется отдельно)
-- CREATE DATABASE metamethod_bot;

-- Подключаемся к БД
\c metamethod_bot;

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_analyses INTEGER DEFAULT 0
);

-- Индекс для быстрого поиска по username
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at);

-- Таблица анализов (диалогов)
CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,

    -- Входные данные
    photo_path VARCHAR(500),
    photo_url TEXT,
    request_text TEXT NOT NULL,

    -- Результаты анализа
    analysis_result TEXT,
    pdf_path VARCHAR(500),

    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_seconds INTEGER,
    tokens_used INTEGER,
    model_used VARCHAR(50) DEFAULT 'gpt-4o',

    -- Для датасета
    is_approved_for_dataset BOOLEAN DEFAULT FALSE,
    dataset_notes TEXT,
    quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5)
);

-- Индексы для аналитики
CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_analyses_approved ON analyses(is_approved_for_dataset);
CREATE INDEX IF NOT EXISTS idx_analyses_rating ON analyses(quality_rating);

-- Таблица для хранения фото в base64 (для датасета)
CREATE TABLE IF NOT EXISTS photos (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    photo_base64 TEXT,
    photo_size_kb INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_photos_analysis ON photos(analysis_id);

-- Таблица статистики по темам запросов
CREATE TABLE IF NOT EXISTS request_themes (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    theme VARCHAR(100) NOT NULL, -- 'финансы', 'отношения', 'здоровье', 'реализация'
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_themes_analysis ON request_themes(analysis_id);
CREATE INDEX IF NOT EXISTS idx_themes_type ON request_themes(theme);

-- Таблица для фидбека пользователей
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_analysis ON feedback(analysis_id);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);

-- Представление для аналитики
CREATE OR REPLACE VIEW analytics_summary AS
SELECT
    DATE(a.created_at) as date,
    COUNT(*) as total_analyses,
    COUNT(DISTINCT a.user_id) as unique_users,
    AVG(a.processing_time_seconds) as avg_processing_time,
    SUM(a.tokens_used) as total_tokens,
    AVG(f.rating) as avg_rating,
    COUNT(CASE WHEN a.is_approved_for_dataset THEN 1 END) as approved_for_dataset
FROM analyses a
LEFT JOIN feedback f ON a.id = f.analysis_id
GROUP BY DATE(a.created_at)
ORDER BY date DESC;

-- Представление для подготовки датасета
CREATE OR REPLACE VIEW dataset_ready AS
SELECT
    a.id,
    u.user_id,
    u.first_name,
    a.request_text,
    a.analysis_result,
    p.photo_base64,
    a.created_at,
    a.quality_rating,
    f.rating as user_rating,
    f.comment as user_comment
FROM analyses a
JOIN users u ON a.user_id = u.user_id
LEFT JOIN photos p ON a.id = p.analysis_id
LEFT JOIN feedback f ON a.id = f.analysis_id
WHERE a.is_approved_for_dataset = TRUE
  AND a.quality_rating >= 4
ORDER BY a.created_at DESC;

-- Функция для автоопределения темы запроса
CREATE OR REPLACE FUNCTION detect_request_theme(request TEXT)
RETURNS VARCHAR(100) AS $$
BEGIN
    IF request ~* '(деньги|финанс|доход|заработ|бизнес|богат|бедн)' THEN
        RETURN 'финансы';
    ELSIF request ~* '(отношени|любов|партнер|муж|жена|семь|развод)' THEN
        RETURN 'отношения';
    ELSIF request ~* '(здоров|болезн|тело|энерги|устал|выгоран)' THEN
        RETURN 'здоровье';
    ELSIF request ~* '(реализ|проявл|бизнес|работ|карьер|призван|миссия)' THEN
        RETURN 'реализация';
    ELSE
        RETURN 'другое';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического определения темы
CREATE OR REPLACE FUNCTION auto_detect_theme()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO request_themes (analysis_id, theme)
    VALUES (NEW.id, detect_request_theme(NEW.request_text));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_detect_theme
AFTER INSERT ON analyses
FOR EACH ROW
EXECUTE FUNCTION auto_detect_theme();

-- Функция для обновления статистики пользователя
CREATE OR REPLACE FUNCTION update_user_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users
    SET total_analyses = total_analyses + 1,
        last_active = CURRENT_TIMESTAMP
    WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_stats
AFTER INSERT ON analyses
FOR EACH ROW
EXECUTE FUNCTION update_user_stats();

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Пользователи бота';
COMMENT ON TABLE analyses IS 'История всех анализов для подготовки датасета';
COMMENT ON TABLE photos IS 'Фотографии в base64 для fine-tuning';
COMMENT ON TABLE request_themes IS 'Категории запросов для аналитики';
COMMENT ON TABLE feedback IS 'Отзывы пользователей о качестве анализа';

COMMENT ON COLUMN analyses.is_approved_for_dataset IS 'Одобрено для включения в датасет для fine-tuning';
COMMENT ON COLUMN analyses.quality_rating IS 'Оценка качества анализа (1-5) от оператора';
COMMENT ON COLUMN analyses.tokens_used IS 'Количество токенов использованных в запросе';

-- Вставка тестовых данных (опционально)
-- INSERT INTO users (user_id, username, first_name) VALUES
-- (123456789, 'test_user', 'Тест');

GRANT ALL PRIVILEGES ON DATABASE metamethod_bot TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
