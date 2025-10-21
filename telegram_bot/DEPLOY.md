# 🚀 Деплой бота из GitHub

## Вариант 1: Клонирование на локальную машину

```bash
# Клонируй репозиторий
git clone https://github.com/DaniilLepekhin/Natalie-Zemskova.git

# Перейди в папку
cd Natalie-Zemskova

# Установи зависимости
pip install -r requirements.txt

# Создай .env файл
cp .env.example .env

# Открой .env и заполни токены
nano .env  # или любой редактор

# Запусти бота
python bot.py
```

## Вариант 2: Деплой на VPS (Ubuntu/Debian)

### Шаг 1: Подключись к серверу

```bash
ssh user@your-server-ip
```

### Шаг 2: Установи зависимости

```bash
sudo apt update
sudo apt install python3 python3-pip git -y
```

### Шаг 3: Клонируй репозиторий

```bash
git clone https://github.com/DaniilLepekhin/Natalie-Zemskova.git
cd Natalie-Zemskova
```

### Шаг 4: Установи Python библиотеки

```bash
pip3 install -r requirements.txt
```

### Шаг 5: Настрой .env

```bash
cp .env.example .env
nano .env
```

Вставь свои токены и сохрани (Ctrl+X, Y, Enter)

### Шаг 6: Запусти бота в фоне

```bash
nohup python3 bot.py > bot.log 2>&1 &
```

Проверь что работает:
```bash
tail -f bot.log
```

### Шаг 7 (опционально): Настрой systemd

Создай файл сервиса:

```bash
sudo nano /etc/systemd/system/metamethod-bot.service
```

Вставь:

```ini
[Unit]
Description=Meta-Method Telegram Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/Natalie-Zemskova
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /home/your-username/Natalie-Zemskova/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Замени `your-username` на своё имя пользователя.

Активируй сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable metamethod-bot
sudo systemctl start metamethod-bot
```

Проверь статус:

```bash
sudo systemctl status metamethod-bot
```

Логи:

```bash
sudo journalctl -u metamethod-bot -f
```

## Вариант 3: Heroku

### Шаг 1: Установи Heroku CLI

https://devcenter.heroku.com/articles/heroku-cli

### Шаг 2: Залогинься

```bash
heroku login
```

### Шаг 3: Создай приложение

```bash
cd Natalie-Zemskova
heroku create your-metamethod-bot
```

### Шаг 4: Добавь Procfile

```bash
echo "worker: python bot.py" > Procfile
```

### Шаг 5: Установи переменные окружения

```bash
heroku config:set TELEGRAM_TOKEN=your_token
heroku config:set OPENAI_API_KEY=your_key
heroku config:set OPENAI_MODEL=gpt-4o-mini
```

### Шаг 6: Деплой

```bash
git add .
git commit -m "Add Procfile"
git push heroku main
```

### Шаг 7: Запусти worker

```bash
heroku ps:scale worker=1
```

Проверь логи:

```bash
heroku logs --tail
```

## Вариант 4: Railway.app

### Шаг 1: Зайди на railway.app

https://railway.app/

### Шаг 2: New Project → Deploy from GitHub

Выбери репозиторий `DaniilLepekhin/Natalie-Zemskova`

### Шаг 3: Добавь переменные окружения

В настройках проекта добавь:
- `TELEGRAM_TOKEN`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`

### Шаг 4: Deploy!

Railway автоматически развернёт бота.

## Обновление бота

### На локальной машине:

```bash
cd Natalie-Zemskova
git pull origin main
pip install -r requirements.txt  # если были изменения
# Перезапусти бота
```

### На VPS с systemd:

```bash
cd Natalie-Zemskova
git pull origin main
pip3 install -r requirements.txt
sudo systemctl restart metamethod-bot
```

### На Heroku:

```bash
git pull origin main
git push heroku main
```

### На Railway:

Railway автоматически обновится при push в GitHub.

## Мониторинг

### Проверка работы:

```bash
# Локально или VPS
tail -f bot.log

# systemd
sudo journalctl -u metamethod-bot -f

# Heroku
heroku logs --tail

# Railway
Смотри логи в dashboard
```

### Проверка расхода OpenAI:

https://platform.openai.com/usage

## Бэкап

### Сохрани сгенерированные PDF:

```bash
# Локально
tar -czf pdfs_backup_$(date +%Y%m%d).tar.gz generated_pdfs/

# На VPS - скачай на локальную машину
scp user@server:/path/to/Natalie-Zemskova/generated_pdfs/*.pdf ./backup/
```

### Сохрани фото пользователей (если нужно):

```bash
tar -czf photos_backup_$(date +%Y%m%d).tar.gz user_photos/
```

## Безопасность

### ✅ Рекомендации:

1. **Никогда не коммить .env в git**
   - Уже добавлен в .gitignore

2. **Используй отдельного пользователя на VPS**
   ```bash
   sudo adduser botuser
   sudo -u botuser -s  # работай от этого пользователя
   ```

3. **Настрой firewall**
   ```bash
   sudo ufw allow ssh
   sudo ufw enable
   ```

4. **Регулярно обновляй систему**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

5. **Ротация токенов**
   - Периодически меняй токены OpenAI и Telegram

## Стоимость серверов

- **VPS (Hetzner)**: от €4/месяц
- **DigitalOcean**: от $4/месяц
- **AWS EC2 t2.micro**: ~$8/месяц (есть free tier)
- **Heroku**: $7/месяц (или бесплатно с ограничениями)
- **Railway**: $5/месяц

Плюс стоимость OpenAI API (~$0.15₽ за анализ на gpt-4o-mini).

## Проблемы?

### Бот не запускается

Проверь:
```bash
python3 --version  # Должен быть 3.9+
pip3 list | grep telegram  # Должен быть установлен
cat .env  # Проверь токены
```

### Бот не отвечает в Telegram

1. Проверь что процесс запущен
2. Проверь логи на ошибки
3. Проверь токен в @BotFather
4. Проверь баланс OpenAI

### Ошибки с PDF

Установи шрифты:
```bash
# Ubuntu/Debian
sudo apt install fonts-dejavu

# macOS (обычно есть по умолчанию)
brew install --cask font-dejavu
```

---

**Готово! 🚀**

Бот развёрнут и работает 24/7.
