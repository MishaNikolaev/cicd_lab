#!/bin/bash

# Скрипт для остановки QEMU
# Используется в Jenkins pipeline

echo "=== Остановка QEMU ==="

PID_FILE="/tmp/qemu.pid"

if [ -f "$PID_FILE" ]; then
    QEMU_PID=$(cat "$PID_FILE")
    echo "Найден PID QEMU: $QEMU_PID"
    
    if ps -p "$QEMU_PID" > /dev/null 2>&1; then
        echo "Завершение процесса QEMU..."
        kill -TERM "$QEMU_PID"
        
        # Ждем завершения процесса
        sleep 5
        
        if ps -p "$QEMU_PID" > /dev/null 2>&1; then
            echo "Принудительное завершение QEMU..."
            kill -KILL "$QEMU_PID"
        fi
        
        echo "QEMU успешно остановлен"
    else
        echo "Процесс QEMU не найден"
    fi
    
    rm -f "$PID_FILE"
else
    echo "PID файл не найден, поиск процессов QEMU..."
    pkill -f "qemu-system-arm" || echo "Процессы QEMU не найдены"
fi

echo "Очистка завершена"
