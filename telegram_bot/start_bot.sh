#!/bin/bash

# Скрипт для запуска единственного экземпляра бота Мета Лиза

BOT_DIR="/Users/daniillepekhin/My Python/Natalie Zemskova/telegram_bot"
PID_FILE="$BOT_DIR/bot.pid"
LOG_FILE="$BOT_DIR/bot.log"

cd "$BOT_DIR"

# Функция для остановки всех экземпляров бота
stop_all_bots() {
    echo "Останавливаю все экземпляры бота..."

    # Убиваем по PID файлу если есть
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            kill -9 $OLD_PID 2>/dev/null
            echo "Убит процесс PID: $OLD_PID"
        fi
        rm -f "$PID_FILE"
    fi

    # Убиваем все процессы bot_with_sales_funnel
    pkill -9 -f "bot_with_sales_funnel.py" 2>/dev/null

    # Дополнительная проверка и убийство
    ps aux | grep "bot_with_sales_funnel.py" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null

    sleep 2
    echo "✅ Все процессы остановлены"
}

# Останавливаем все существующие экземпляры
stop_all_bots

# Проверяем что точно ничего не запущено
RUNNING=$(ps aux | grep "bot_with_sales_funnel.py" | grep -v grep | wc -l)
if [ "$RUNNING" -gt 0 ]; then
    echo "❌ ОШИБКА: Всё ещё запущены процессы бота!"
    ps aux | grep "bot_with_sales_funnel.py" | grep -v grep
    exit 1
fi

echo "Запускаю единственный экземпляр бота..."

# Запускаем бота в фоне
nohup python3 -u bot_with_sales_funnel.py > "$LOG_FILE" 2>&1 &
BOT_PID=$!

# Сохраняем PID
echo $BOT_PID > "$PID_FILE"

# Даём время на запуск
sleep 3

# Проверяем что бот запустился
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "✅ Бот успешно запущен!"
    echo "   PID: $BOT_PID"
    echo "   Логи: $LOG_FILE"
    echo ""
    echo "Последние строки лога:"
    tail -10 "$LOG_FILE"
else
    echo "❌ Ошибка запуска бота!"
    echo "Проверьте лог: $LOG_FILE"
    exit 1
fi
