# 💰 Логирование стоимости API запросов

## Что было добавлено

### 1. База данных
- **Новое поле в таблице `analyses`**: `api_cost_usd` (NUMERIC(10,6))
- Хранит стоимость каждого запроса в долларах США с точностью до 6 знаков

### 2. Модули

#### `cost_calculator.py`
Модуль для расчёта стоимости API запросов:
- **Функция `calculate_cost(model, prompt_tokens, completion_tokens)`** - рассчитывает стоимость
- **Цены GPT-4o** (актуальные на декабрь 2024):
  - Prompt: $2.50 за 1M токенов ($0.0025 за 1K)
  - Completion: $10.00 за 1M токенов ($0.010 за 1K)
- **Цены GPT-4o-mini**:
  - Prompt: $0.15 за 1M токенов
  - Completion: $0.60 за 1M токенов

#### Обновлённые модули:
- **`metamethod_analyzer.py`**:
  - Метод `analyze()` теперь возвращает `usage_info` вместо просто `total_tokens`
  - `usage_info` содержит: `total_tokens`, `prompt_tokens`, `completion_tokens`, `cost_usd`
  - Все шаги (`_step1` через `_step5`) возвращают полный `usage` объект от OpenAI

- **`database.py`**:
  - Метод `save_analysis()` принимает параметр `api_cost_usd`
  - Сохраняет стоимость в базу данных

- **`bot_with_db.py`**:
  - Получает `usage_info` от анализатора
  - Передаёт `cost_usd` в `save_analysis()`

## Как использовать

### Просмотр статистики в терминале

Запустите скрипт:
```bash
cd /opt/Natalie_Zemskova
source venv/bin/activate
python3 show_cost_stats.py
```

Вывод:
```
📊 ОБЩАЯ СТАТИСТИКА
Всего анализов: 150
Общая стоимость: $12.5678
Средняя стоимость: $0.0838
Мин/Макс стоимость: $0.0234 / $0.1523
Всего токенов: 234,567
Средне токенов: 1,564

👥 ТОП-10 ПОЛЬЗОВАТЕЛЕЙ ПО РАСХОДАМ
+------------+----------+-----------+----------+----------+
| Username   | Имя      | Анализов  | Всего    | Средняя  |
+============+==========+===========+==========+==========+
| @user1     | Анна     | 25        | $2.1234  | $0.0849  |
| @user2     | Иван     | 18        | $1.5678  | $0.0871  |
...

📝 ПОСЛЕДНИЕ 10 АНАЛИЗОВ
+----+----------+---------------------------+------------+----------+----------------+
| ID | User     | Запрос                    | Стоимость  | Токены   | Дата           |
+====+==========+===========================+============+==========+================+
| 45 | @user1   | Почему у меня не получа...| $0.0845    | 1,234    | 14.10.2025 ...
...
```

### SQL запросы

Готовые SQL запросы доступны в файле `/opt/Natalie_Zemskova/cost_stats.sql`:

```bash
# Общая статистика
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot -f cost_stats.sql
```

Или используйте отдельные запросы:

```sql
-- Общие расходы
SELECT
    COUNT(*) as total_analyses,
    SUM(api_cost_usd) as total_cost_usd,
    AVG(api_cost_usd) as avg_cost
FROM analyses
WHERE api_cost_usd IS NOT NULL;

-- Расходы по дням
SELECT
    DATE(created_at) as date,
    COUNT(*) as count,
    SUM(api_cost_usd) as daily_cost
FROM analyses
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Топ пользователей
SELECT
    u.username,
    COUNT(a.id) as analyses,
    SUM(a.api_cost_usd) as total_spent
FROM users u
JOIN analyses a ON u.user_id = a.user_id
WHERE a.api_cost_usd IS NOT NULL
GROUP BY u.username
ORDER BY total_spent DESC
LIMIT 10;
```

## Примеры данных

Типичная стоимость одного анализа:
- **5 шагов анализа**: ~1,200-1,500 токенов (prompt + completion)
- **Примерная стоимость**: $0.08-$0.12 за анализ
- **100 анализов в день**: ~$8-12
- **3,000 анализов в месяц**: ~$240-360

## Мониторинг расходов

### Ежедневная проверка
```bash
cd /opt/Natalie_Zemskova && source venv/bin/activate && python3 show_cost_stats.py
```

### Создать алерт при превышении лимита
Добавьте в cron:
```bash
# Проверка каждый день в 23:00
0 23 * * * cd /opt/Natalie_Zemskova && source venv/bin/activate && python3 show_cost_stats.py | mail -s "Daily API Cost Report" admin@example.com
```

### Экспорт данных для бухгалтерии
```sql
-- За месяц
COPY (
    SELECT
        TO_CHAR(created_at, 'DD.MM.YYYY') as date,
        u.username,
        a.api_cost_usd,
        a.tokens_used
    FROM analyses a
    JOIN users u ON a.user_id = u.user_id
    WHERE created_at >= DATE_TRUNC('month', NOW())
      AND api_cost_usd IS NOT NULL
    ORDER BY created_at
) TO '/tmp/monthly_api_costs.csv' WITH CSV HEADER;
```

## Обновление цен

Если цены OpenAI изменятся, обновите файл `cost_calculator.py`:

```python
GPT4O_PRICES = {
    'gpt-4o': {
        'prompt': 0.0025,      # Обновите здесь
        'completion': 0.010    # и здесь
    }
}
```

## Troubleshooting

### Старые анализы без стоимости
Для старых записей `api_cost_usd` будет `NULL`. Это нормально - стоимость считается только для новых анализов.

### Проверка работы логирования
После создания нового анализа проверьте:
```sql
SELECT id, tokens_used, api_cost_usd, created_at
FROM analyses
ORDER BY created_at DESC
LIMIT 1;
```

Должен быть заполнен `api_cost_usd`.
