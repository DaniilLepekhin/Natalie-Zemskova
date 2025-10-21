#!/bin/bash

# Деплой улучшенной версии metamethod_analyzer на сервер

SERVER="31.128.38.177"
USER="root"
PASSWORD="Z)6&te4VMzAw"
BOT_DIR="/opt/Natalie_Zemskova"

echo "Копируем улучшенный metamethod_analyzer_v2.py на сервер..."

# Заменяем старую версию на новую
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no telegram_bot/metamethod_analyzer_v2.py "$USER@$SERVER:$BOT_DIR/metamethod_analyzer.py"

if [ $? -eq 0 ]; then
    echo "✅ Файл успешно скопирован!"

    echo "Перезапускаем бота..."
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$USER@$SERVER" "systemctl restart natalie-bot"

    if [ $? -eq 0 ]; then
        echo "✅ Бот успешно перезапущен!"
        echo "Проверяем статус..."
        sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$USER@$SERVER" "systemctl status natalie-bot --no-pager -l"
    else
        echo "❌ Ошибка при перезапуске бота"
        exit 1
    fi
else
    echo "❌ Ошибка при копировании файла"
    exit 1
fi
