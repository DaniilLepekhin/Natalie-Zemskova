-- Статистика по стоимости API запросов

-- 1. Общая статистика
SELECT 
    COUNT(*) as total_analyses,
    SUM(api_cost_usd) as total_cost_usd,
    AVG(api_cost_usd) as avg_cost_per_analysis,
    MIN(api_cost_usd) as min_cost,
    MAX(api_cost_usd) as max_cost,
    SUM(tokens_used) as total_tokens,
    AVG(tokens_used) as avg_tokens_per_analysis
FROM analyses
WHERE api_cost_usd IS NOT NULL;

-- 2. Статистика по пользователям (топ-10 по расходам)
SELECT 
    u.username,
    u.first_name,
    COUNT(a.id) as analyses_count,
    SUM(a.api_cost_usd) as total_spent_usd,
    AVG(a.api_cost_usd) as avg_cost_per_analysis,
    SUM(a.tokens_used) as total_tokens
FROM users u
JOIN analyses a ON u.user_id = a.user_id
WHERE a.api_cost_usd IS NOT NULL
GROUP BY u.user_id, u.username, u.first_name
ORDER BY total_spent_usd DESC
LIMIT 10;

-- 3. Статистика по дням (последние 30 дней)
SELECT 
    DATE(created_at) as date,
    COUNT(*) as analyses_count,
    SUM(api_cost_usd) as daily_cost_usd,
    AVG(api_cost_usd) as avg_cost,
    SUM(tokens_used) as daily_tokens
FROM analyses
WHERE api_cost_usd IS NOT NULL
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 4. Топ-10 самых дорогих анализов
SELECT 
    a.id,
    u.username,
    LEFT(a.request_text, 50) as request_preview,
    a.api_cost_usd,
    a.tokens_used,
    a.created_at
FROM analyses a
JOIN users u ON a.user_id = u.user_id
WHERE a.api_cost_usd IS NOT NULL
ORDER BY a.api_cost_usd DESC
LIMIT 10;
