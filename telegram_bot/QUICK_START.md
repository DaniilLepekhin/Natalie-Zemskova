# 🚀 Быстрый старт: Просмотр статистики по стоимости

## Что было сделано

✅ Добавлено поле `api_cost_usd` в таблицу `analyses`
✅ Создан модуль `cost_calculator.py` для расчёта стоимости
✅ Обновлён `metamethod_analyzer.py` для отслеживания токенов
✅ Обновлён `bot_with_db.py` для сохранения стоимости
✅ Создан скрипт `show_cost_stats.py` для просмотра статистики

## Как посмотреть статистику

### Способ 1: Python скрипт (красиво)
```bash
cd /opt/Natalie_Zemskova
source venv/bin/activate
python3 show_cost_stats.py
```

### Способ 2: SQL запрос (быстро)
```bash
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot -c \
"SELECT COUNT(*) as analyses, ROUND(CAST(SUM(api_cost_usd) AS numeric), 4) as total_cost_usd FROM analyses WHERE api_cost_usd IS NOT NULL;"
```

## Примеры запросов

### Сколько потрачено сегодня?
```bash
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot -c \
"SELECT COUNT(*) as analyses, ROUND(CAST(SUM(api_cost_usd) AS numeric), 4) as cost FROM analyses WHERE DATE(created_at) = CURRENT_DATE;"
```

### Кто больше всех потратил?
```bash
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot -c \
"SELECT u.username, COUNT(a.id) as analyses, ROUND(CAST(SUM(a.api_cost_usd) AS numeric), 4) as total_spent FROM users u JOIN analyses a ON u.user_id = a.user_id WHERE a.api_cost_usd IS NOT NULL GROUP BY u.username ORDER BY total_spent DESC LIMIT 5;"
```

### Последние 5 анализов с ценой
```bash
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot -c \
"SELECT id, LEFT(request_text, 30) as request, api_cost_usd, tokens_used FROM analyses WHERE api_cost_usd IS NOT NULL ORDER BY created_at DESC LIMIT 5;"
```

## Типичные цены

- **1 анализ**: ~$0.08-0.12
- **10 анализов**: ~$0.80-1.20
- **100 анализов**: ~$8-12
- **1000 анализов**: ~$80-120

## Важно

- **Старые анализы** (до этого обновления): `api_cost_usd = NULL`
- **Новые анализы** (после обновления): `api_cost_usd` заполнено автоматически
- **Точность**: стоимость округляется до 6 знаков ($0.084523)
- **Валюта**: только USD

## Файлы

- `/opt/Natalie_Zemskova/cost_calculator.py` - модуль расчёта стоимости
- `/opt/Natalie_Zemskova/show_cost_stats.py` - скрипт статистики
- `/opt/Natalie_Zemskova/cost_stats.sql` - готовые SQL запросы
- `/opt/Natalie_Zemskova/COST_TRACKING_README.md` - полная документация
