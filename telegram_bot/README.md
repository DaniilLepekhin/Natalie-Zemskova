# 🔮 Сканер подсознания - Telegram Bot

Telegram бот для анализа фотографий по Мета-Методу Natalie Zemskova с использованием GPT-4o.

## 📋 Возможности

- ✅ Анализ фото по Мета-Методу через 5-шаговый процесс
- ✅ Генерация PDF с красивым дизайном и фоном
- ✅ Хранение всех анализов в PostgreSQL
- ✅ Логирование стоимости каждого API запроса
- ✅ Сбор датасета для fine-tuning GPT
- ✅ Глубина анализа 7-10 минут (как у эксперта)
- ✅ Конкретные поколения (бабушка/прабабушка по маминой/папиной линии)
- ✅ Расшифровка контрактов с примерами проявления
- ✅ Процентные показатели работы чакр с цветовыми индикаторами
- ✅ Феминизация всех фраз (я не достоин/достойна)

## 🏗 Архитектура

```
bot_with_db.py              # Основной файл бота
├── metamethod_analyzer.py  # 5-шаговый анализ через GPT-4o
├── pdf_generator_with_background.py  # Генерация PDF с фоном
├── database.py             # Работа с PostgreSQL
├── cost_calculator.py      # Расчёт стоимости API запросов
└── config.py              # Конфигурация (не в git)
```

## 🚀 Установка

### 1. Клонировать репозиторий
```bash
git clone https://github.com/DaniilLepekhin/Natalie-Zemskova.git
cd Natalie-Zemskova
```

### 2. Создать виртуальное окружение
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Настроить PostgreSQL
```bash
# Создать базу данных
createdb metamethod_bot

# Импортировать схему (если есть)
psql -d metamethod_bot -f schema.sql
```

### 4. Создать config.py
```python
TELEGRAM_TOKEN = "your_telegram_bot_token"
OPENAI_API_KEY = "your_openai_api_key"
OPENAI_MODEL = "gpt-4o"

# PostgreSQL
DB_HOST = "localhost"
DB_NAME = "metamethod_bot"
DB_USER = "postgres"
DB_PASSWORD = "your_password"
```

### 5. Запустить бота
```bash
python3 bot_with_db.py
```

## 📊 Мониторинг стоимости

### Просмотр статистики
```bash
source venv/bin/activate
python3 show_cost_stats.py
```

### Быстрая проверка через SQL
```bash
psql -d metamethod_bot -c "SELECT COUNT(*) as analyses, ROUND(CAST(SUM(api_cost_usd) AS numeric), 4) as total_cost FROM analyses WHERE api_cost_usd IS NOT NULL;"
```

## 📁 Структура базы данных

### Таблица `analyses`
- Все анализы с результатами
- Токены и стоимость каждого запроса
- Время обработки

### Таблица `photos`
- Фотографии в base64
- Для создания датасета и fine-tuning GPT

### Таблица `users`
- Информация о пользователях
- Статистика использования

## 🔧 Деплой (systemd)

Создать сервис:
```bash
sudo nano /etc/systemd/system/natalie-bot.service
```

```ini
[Unit]
Description=Natalie Zemskova Meta-Method Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/Natalie_Zemskova
ExecStart=/opt/Natalie_Zemskova/venv/bin/python3 /opt/Natalie_Zemskova/bot_with_db.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запустить:
```bash
sudo systemctl daemon-reload
sudo systemctl enable natalie-bot
sudo systemctl start natalie-bot
sudo systemctl status natalie-bot
```

## 📈 Прогноз роста БД

| Анализов | Размер БД |
|----------|-----------|
| 1,000    | ~55 MB    |
| 10,000   | ~550 MB   |
| 100,000  | ~5.5 GB   |

## 📚 Документация

- [COST_TRACKING_README.md](COST_TRACKING_README.md) - Логирование стоимости API
- [QUICK_START.md](QUICK_START.md) - Быстрый старт
- [cost_stats.sql](cost_stats.sql) - SQL запросы для статистики

## 🤖 Бот

- **Username**: @skanermetalizabot
- **Модель**: GPT-4o
- **Анализ**: 5-шаговый процесс
- **Стоимость**: ~$0.08-0.12 за анализ

## 📝 Лицензия

Private - только для Natalie Zemskova

## 👤 Автор

Разработано для Natalie Zemskova
