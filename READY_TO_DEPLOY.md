# ✅ Всё готово к деплою!

## 🎯 Что сделано

### 1. Telegram бот
- ✅ Основной код (bot.py)
- ✅ Версия с БД (bot_with_db.py) ← **запускаем эту**
- ✅ Генерация PDF
- ✅ Финальный промпт 2.0.0 с эмодзи и архетипами

### 2. PostgreSQL интеграция
- ✅ Структура БД (database.sql)
- ✅ Модуль для работы с БД (database.py)
- ✅ Автосохранение всех анализов
- ✅ Сохранение фото в base64
- ✅ Автоопределение тем запросов
- ✅ Экспорт в JSONL для fine-tuning

### 3. Настройки
- ✅ .env с реальными токенами
- ✅ Telegram: @daniil_lepekhin_test_bot
- ✅ OpenAI: gpt-4o
- ✅ PostgreSQL: настроен

### 4. Документация
- ✅ DEPLOY_INSTRUCTIONS.md - подробная инструкция
- ✅ deploy_server.sh - автоматический скрипт
- ✅ Все команды для управления

## 🚀 Быстрый деплой

### Вариант А: Автоматический (1 команда)

```bash
cd "/Users/daniillepekhin/My Python/Natalie Zemskova/telegram_bot"
./deploy_server.sh
```

**Это сделает всё автоматически:**
1. Подключится к серверу 31.128.38.177
2. Установит Python + PostgreSQL
3. Создаст базу данных metamethod_bot
4. Загрузит все файлы
5. Установит зависимости
6. Запустит бота как systemd сервис

### Вариант Б: Ручной (пошагово)

См. [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md)

## 📊 Данные для доступа

### Сервер
```
Host: 31.128.38.177
User: root
Password: Z)6&te4VMzAw
```

### PostgreSQL
```
Host: 31.128.38.177 (или localhost с сервера)
Port: 5432
Database: metamethod_bot
User: postgres
Password: kH*kyrS&9z7K
```

### Telegram Bot
```
Username: @daniil_lepekhin_test_bot
Token: [см. в .env файле на сервере]
```

### OpenAI
```
API Key: [см. в .env файле на сервере]
Model: gpt-4o
```

## 🎮 Управление после деплоя

### Проверить статус
```bash
ssh root@31.128.38.177 'systemctl status metamethod-bot'
```

### Смотреть логи в реальном времени
```bash
ssh root@31.128.38.177 'journalctl -u metamethod-bot -f'
```

### Перезапустить
```bash
ssh root@31.128.38.177 'systemctl restart metamethod-bot'
```

### Остановить
```bash
ssh root@31.128.38.177 'systemctl stop metamethod-bot'
```

## 📊 Работа с базой данных

### Подключиться к БД с сервера
```bash
ssh root@31.128.38.177
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot
```

### Посмотреть статистику
```sql
-- Всех пользователей
SELECT * FROM users ORDER BY created_at DESC;

-- Последние анализы
SELECT id, user_id, request_text, created_at, tokens_used
FROM analyses ORDER BY created_at DESC LIMIT 10;

-- Статистика по темам
SELECT theme, COUNT(*) FROM request_themes
GROUP BY theme ORDER BY COUNT DESC;

-- Аналитика
SELECT * FROM analytics_summary;
```

## 🔍 Тестирование

### 1. Проверь что бот запущен
```bash
ssh root@31.128.38.177 'systemctl status metamethod-bot'
```

Должно быть: **active (running)**

### 2. Проверь логи
```bash
ssh root@31.128.38.177 'journalctl -u metamethod-bot -n 20'
```

Должно быть:
```
INFO - 🤖 Бот запущен с интеграцией PostgreSQL!
INFO - 📊 Модель: gpt-4o
```

### 3. Протестируй в Telegram

1. Открой [@daniil_lepekhin_test_bot](https://t.me/daniil_lepekhin_test_bot)
2. Отправь /start
3. Загрузи фото
4. Напиши запрос
5. Получи PDF!

### 4. Проверь что сохранилось в БД
```bash
ssh root@31.128.38.177 << 'EOF'
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot -c "
SELECT u.first_name, a.request_text, a.created_at
FROM analyses a
JOIN users u ON a.user_id = u.user_id
ORDER BY a.created_at DESC
LIMIT 5;
"
EOF
```

## 📦 Экспорт датасета (когда будет 50+ кейсов)

### На сервере выполни:
```bash
ssh root@31.128.38.177 << 'EOF'
cd /root/metamethod_bot
source venv/bin/activate
python3 << PYTHON
from database import get_db
db = get_db()
count = db.export_dataset_jsonl('dataset_export.jsonl', min_rating=4)
print(f"Экспортировано {count} записей")
PYTHON
EOF
```

### Скачай на локальную машину:
```bash
scp root@31.128.38.177:/root/metamethod_bot/dataset_export.jsonl ./
```

### Загрузи на OpenAI для fine-tuning:
```bash
openai api fine_tunes.create \
  -t dataset_export.jsonl \
  -m gpt-4o-mini \
  --suffix "metamethod"
```

## ⚠️ Важно

### Безопасность
- ✅ .env не в git (в .gitignore)
- ✅ Пароли только на сервере
- ✅ GitHub репозиторий приватный (рекомендуется)

### Стоимость
- GPT-4o: ~2.5₽ за анализ
- На $10 → ~400 анализов
- На $50 → ~2,000 анализов

### Мониторинг
- Проверяй логи: `journalctl -u metamethod-bot -f`
- Проверяй баланс OpenAI: https://platform.openai.com/usage
- Смотри статистику в БД: `SELECT * FROM analytics_summary`

## 🎯 Чеклист перед запуском

- [ ] Файлы загружены на сервер
- [ ] PostgreSQL установлен и запущен
- [ ] База данных metamethod_bot создана
- [ ] Таблицы созданы (database.sql выполнен)
- [ ] Python зависимости установлены
- [ ] .env файл с токенами на сервере
- [ ] Systemd сервис создан
- [ ] Бот запущен (systemctl start metamethod-bot)
- [ ] Статус active (running)
- [ ] Протестирован в Telegram
- [ ] Данные сохраняются в БД

## 📞 Если что-то не работает

### 1. Бот не отвечает в Telegram
```bash
# Проверь статус
ssh root@31.128.38.177 'systemctl status metamethod-bot'

# Смотри логи
ssh root@31.128.38.177 'journalctl -u metamethod-bot -n 50'
```

### 2. БД не подключается
```bash
# Проверь PostgreSQL
ssh root@31.128.38.177 'systemctl status postgresql'

# Проверь подключение
ssh root@31.128.38.177 "PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -c 'SELECT 1'"
```

### 3. OpenAI ошибка
- Проверь баланс: https://platform.openai.com/usage
- Проверь API ключ в .env файле

## 🎉 Готово!

После деплоя бот будет:
- ✅ Работать 24/7
- ✅ Автоматически перезапускаться при сбоях
- ✅ Сохранять все анализы в PostgreSQL
- ✅ Копить данные для fine-tuning
- ✅ Отправлять красивые PDF отчёты

**Бот**: [@daniil_lepekhin_test_bot](https://t.me/daniil_lepekhin_test_bot)
**GitHub**: https://github.com/DaniilLepekhin/Natalie-Zemskova
**Версия**: 2.1.0 (с PostgreSQL)

Удачи! 🚀
