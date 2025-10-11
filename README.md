# 🔮 Telegram Bot для Мета-Метод Диагностики

Автоматизированный Telegram бот для проведения диагностики подсознания по Мета-Методу.

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-green.svg)](https://platform.openai.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)

## ✨ Возможности

- 📸 **Анализ фотографии** - GPT-4o Vision анализирует энергетику с фото
- ✍️ **Обработка запроса** - учитывает текстовый запрос клиента
- 🤖 **Мощный AI** - использует GPT-4o/4o-mini для глубокого анализа
- 📄 **PDF отчёт** - генерирует профессиональный документ
- 🎯 **Структурированный анализ** - 10 пунктов по Мета-Методу

## 📋 Структура анализа

1. Контракты и подключки
2. Слои (период происхождения программы)
3. Поток энергии по центрам
4. Главные программы
5. Главные уроки души
6. Родовые влияния
7. Связи из прошлых жизней
8. Что важно изменить
9. Трансформационные фразы
10. Рекомендация: следующий шаг

## 🚀 Быстрый старт

### Установка

```bash
git clone https://github.com/DaniilLepekhin/Natalie-Zemskova.git
cd Natalie-Zemskova
pip install -r requirements.txt
```

### Настройка

1. Создай `.env` файл:
```bash
cp .env.example .env
```

2. Получи токены:
   - **Telegram**: [@BotFather](https://t.me/BotFather) → `/newbot`
   - **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

3. Заполни `.env`:
```env
TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

### Запуск

```bash
python bot.py
```

## 📖 Документация

- **[QUICKSTART_RU.md](QUICKSTART_RU.md)** - подробный гайд на русском (5 минут)
- **[SUMMARY.md](SUMMARY.md)** - краткая сводка проекта
- **[PROMPT_INFO.md](PROMPT_INFO.md)** - про промпт, датасет и fine-tuning
- **[README.md](README.md)** - полная документация (English)

## 💰 Стоимость

### GPT-4o-mini (рекомендуется)
- **~0.15₽ (~$0.0014)** за анализ
- На $5 → ~3,500 анализов
- Отличное качество, доступная цена

### GPT-4o (максимум)
- **~2.5₽ (~$0.024)** за анализ
- На $5 → ~200 анализов
- Максимальная глубина и точность

## 🎨 Пример работы

1. Пользователь отправляет фото
2. Пишет запрос: "Хочу понять блоки в финансах"
3. Бот анализирует 30-60 секунд
4. Получает PDF с полным разбором

## 🔧 Технологии

- **Python 3.9+**
- **python-telegram-bot** - Telegram API
- **OpenAI GPT-4o** - Vision + Text анализ
- **ReportLab** - генерация PDF
- **python-dotenv** - управление конфигом

## 📁 Структура проекта

```
telegram_bot/
├── bot.py                 # Основной бот
├── pdf_generator.py       # Генерация PDF
├── config.py              # Конфигурация
├── requirements.txt       # Зависимости
├── .env.example          # Пример токенов
└── docs/                 # Документация
```

## 🔐 Безопасность

- Токены в `.env` (не в коде!)
- `.env` в `.gitignore`
- Фото хранятся временно
- Нет сбора персональных данных

## 🐛 Известные проблемы

Все решения в разделе "Troubleshooting" в [README.md](README.md)

## 🤝 Вклад

Приветствуются:
- Баг-репорты
- Предложения по улучшению
- Pull requests

## 📄 Лицензия

MIT License - свободное использование для личных и коммерческих проектов

## 👤 Автор

Разработано для проекта **Мета-Метод** by Natalie Zemskova

## ⭐ Поддержка

Если проект полезен - поставь звёздочку! ⭐

---

**Made with ❤️ and GPT-4o**
