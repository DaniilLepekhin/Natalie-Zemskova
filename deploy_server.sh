#!/bin/bash
# Скрипт для деплоя бота на сервер

SERVER="root@31.128.38.177"
SERVER_PATH="/root/metamethod_bot"

echo "🚀 Деплой Мета-Метод бота на сервер..."

# Подключаемся к серверу и выполняем команды
ssh $SERVER << 'ENDSSH'

echo "📦 Устанавливаем необходимые пакеты..."
apt-get update
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib

echo "🔧 Настраиваем PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Создаём базу данных
sudo -u postgres psql << EOF
CREATE DATABASE metamethod_bot;
\q
EOF

echo "✅ PostgreSQL настроен"

# Создаём директорию для проекта
mkdir -p /root/metamethod_bot
cd /root/metamethod_bot

echo "📂 Директория создана: /root/metamethod_bot"

ENDSSH

echo "📤 Копируем файлы на сервер..."
scp -r ./* $SERVER:$SERVER_PATH/

echo "⚙️  Настраиваем окружение на сервере..."
ssh $SERVER << 'ENDSSH'

cd /root/metamethod_bot

# Создаём виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Инициализируем базу данных
echo "🗄️  Инициализируем базу данных..."
PGPASSWORD='kH*kyrS&9z7K' psql -h localhost -U postgres -d metamethod_bot -f database.sql

# Создаём systemd service
cat > /etc/systemd/system/metamethod-bot.service << 'EOF'
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
EOF

# Перезагружаем systemd и запускаем бота
systemctl daemon-reload
systemctl enable metamethod-bot
systemctl start metamethod-bot

echo "✅ Бот запущен как systemd сервис"

# Показываем статус
systemctl status metamethod-bot --no-pager

ENDSSH

echo ""
echo "🎉 Деплой завершён!"
echo ""
echo "Команды для управления ботом на сервере:"
echo "  Статус:        ssh $SERVER 'systemctl status metamethod-bot'"
echo "  Логи:          ssh $SERVER 'journalctl -u metamethod-bot -f'"
echo "  Перезапуск:    ssh $SERVER 'systemctl restart metamethod-bot'"
echo "  Остановка:     ssh $SERVER 'systemctl stop metamethod-bot'"
echo ""
