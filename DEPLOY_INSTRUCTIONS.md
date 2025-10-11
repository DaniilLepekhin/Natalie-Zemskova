# 🚀 Инструкция по деплою на сервер

## Данные для подключения

**Сервер**: 31.128.38.177
**Пользователь**: root
**Пароль**: `Z)6&te4VMzAw`

**PostgreSQL**:
- User: postgres
- Password: `kH*kyrS&9z7K`
- Database: metamethod_bot

## Вариант 1: Автоматический деплой (рекомендуется)

```bash
chmod +x deploy_server.sh
./deploy_server.sh
```

Скрипт автоматически:
- Подключится к серверу
- Установит Python и PostgreSQL
- Создаст базу данных
- Загрузит все файлы
- Запустит бота как systemd сервис

## Вариант 2: Ручной деплой (пошагово)

### Шаг 1: Подключись к серверу

```bash
ssh root@31.128.38.177
# Пароль: Z)6&te4VMzAw
```

### Шаг 2: Установи необходимое ПО

```bash
apt-get update
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib
```

### Шаг 3: Настрой PostgreSQL

```bash
# Запусти PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Создай базу данных
sudo -u postgres psql
```

В psql выполни:
```sql
CREATE DATABASE metamethod_bot;
\q
```

### Шаг 4: Создай директорию для бота

```bash
mkdir -p /root/metamethod_bot
cd /root/metamethod_bot
```

### Шаг 5: Загрузи файлы

На локальной машине выполни:
```bash
cd "/Users/daniillepekhin/My Python/Natalie Zemskova/telegram_bot"
scp -r ./* root@31.128.38.177:/root/metamethod_bot/
```

### Шаг 6: Настрой виртуальное окружение

На сервере:
```bash
cd /root/metamethod_bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 7: Инициализируй базу данных

```bash
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot -f database.sql
```

Проверь что таблицы создались:
```bash
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot -c "\dt"
```

Должны быть таблицы: users, analyses, photos, request_themes, feedback

### Шаг 8: Проверь .env файл

```bash
cat .env
```

Убедись что все токены на месте:
- TELEGRAM_TOKEN=5705262780:AAFxU5ifkgnu3ENiv1dfwmHqL2iQYoW-LMo
- OPENAI_API_KEY=sk-proj-...
- POSTGRES_HOST=localhost (или 31.128.38.177)

### Шаг 9: Протестируй бота вручную

```bash
source venv/bin/activate
python3 bot_with_db.py
```

Должно появиться:
```
INFO - 🤖 Бот запущен с интеграцией PostgreSQL!
INFO - 📊 Модель: gpt-4o
```

Открой Telegram и протестируй бота: @daniil_lepekhin_test_bot

Если всё работает - нажми Ctrl+C для остановки.

### Шаг 10: Создай systemd сервис

```bash
nano /etc/systemd/system/metamethod-bot.service
```

Вставь:
```ini
[Unit]
Description=Metamethod Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/metamethod_bot
Environment="PATH=/root/metamethod_bot/venv/bin"
ExecStart=/root/metamethod_bot/venv/bin/python3 /root/metamethod_bot/bot_with_db.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Сохрани (Ctrl+X, Y, Enter)

### Шаг 11: Запусти как сервис

```bash
systemctl daemon-reload
systemctl enable metamethod-bot
systemctl start metamethod-bot
```

### Шаг 12: Проверь статус

```bash
systemctl status metamethod-bot
```

Должно быть: **active (running)**

### Шаг 13: Смотри логи

```bash
journalctl -u metamethod-bot -f
```

Нажми Ctrl+C чтобы выйти

## 🎛️ Управление ботом

### Перезапуск
```bash
systemctl restart metamethod-bot
```

### Остановка
```bash
systemctl stop metamethod-bot
```

### Запуск
```bash
systemctl start metamethod-bot
```

### Логи (последние 100 строк)
```bash
journalctl -u metamethod-bot -n 100
```

### Логи в реальном времени
```bash
journalctl -u metamethod-bot -f
```

## 📊 Работа с базой данных

### Подключиться к БД
```bash
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot
```

### Посмотреть всех пользователей
```sql
SELECT * FROM users ORDER BY created_at DESC LIMIT 10;
```

### Посмотреть последние анализы
```sql
SELECT id, user_id, request_text, created_at, tokens_used
FROM analyses
ORDER BY created_at DESC
LIMIT 10;
```

### Статистика по темам
```sql
SELECT theme, COUNT(*) as count
FROM request_themes
GROUP BY theme
ORDER BY count DESC;
```

### Аналитика за последние 7 дней
```sql
SELECT * FROM analytics_summary;
```

### Выход из psql
```sql
\q
```

## 🔍 Проблемы и решения

### Бот не запускается
```bash
journalctl -u metamethod-bot -n 50
```
Смотри ошибки в логах

### База данных не подключается
```bash
systemctl status postgresql
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -c "SELECT 1"
```

### OpenAI ошибка
Проверь баланс: https://platform.openai.com/usage

### Telegram ошибка
Проверь токен в .env файле

## 📦 Экспорт датасета

Когда накопится 50+ анализов:

```bash
cd /root/metamethod_bot
source venv/bin/activate
python3 << EOF
from database import get_db
db = get_db()
count = db.export_dataset_jsonl('dataset_for_finetuning.jsonl', min_rating=4)
print(f"Экспортировано {count} записей")
EOF
```

Скачай датасет на локальную машину:
```bash
scp root@31.128.38.177:/root/metamethod_bot/dataset_for_finetuning.jsonl ./
```

## 🎉 Готово!

Бот работает 24/7 на сервере и сохраняет все анализы в PostgreSQL для подготовки датасета.

**Бот**: @daniil_lepekhin_test_bot
**Сервер**: 31.128.38.177
**Логи**: `ssh root@31.128.38.177 'journalctl -u metamethod-bot -f'`
