#!/bin/bash
# Скрипт для очистки старых файлов на сервере
# Все данные уже сохранены в PostgreSQL

echo "🧹 Очистка старых файлов..."

# Удаляем старые фото
if [ -d "user_photos" ]; then
    rm -rf user_photos/*
    echo "✅ Удалены фото из user_photos/"
fi

# Удаляем старые PDF
if [ -d "generated_pdfs" ]; then
    rm -rf generated_pdfs/*
    echo "✅ Удалены PDF из generated_pdfs/"
fi

echo "✨ Очистка завершена!"
echo "📊 Все данные сохранены в PostgreSQL"
