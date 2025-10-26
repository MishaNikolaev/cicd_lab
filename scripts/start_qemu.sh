#!/bin/bash

set -e

echo "=== Запуск QEMU с OpenBMC ==="

cd /var/jenkins_home/workspace/romulus

if [ ! -f "obmc-phosphor-image-romulus-20250902012112.static.mtd" ]; then
    echo "ОШИБКА: MTD файл не найден!"
    exit 1
fi

echo "MTD файл найден: obmc-phosphor-image-romulus-20250902012112.static.mtd"

QEMU_LOG="/tmp/qemu.log"

echo "Запуск QEMU..."
nohup qemu-system-arm \
    -M romulus-bmc \
    -nographic \
    -drive file=obmc-phosphor-image-romulus-20250902012112.static.mtd,format=raw,if=mtd \
    -net user,hostfwd=tcp::8443-:443,hostfwd=tcp::8082-:80 \
    -bios /usr/share/qemu-efi-aarch64/QEMU_EFI.fd \
    > "$QEMU_LOG" 2>&1 &

QEMU_PID=$!
echo "QEMU запущен с PID: $QEMU_PID"

echo "$QEMU_PID" > /tmp/qemu.pid

echo "Ожидание запуска OpenBMC..."
MAX_WAIT=60
WAIT_TIME=0
INTERVAL=10

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if grep -q "romulus login:" "$QEMU_LOG" 2>/dev/null; then
        echo "OpenBMC система загрузилась! Приглашение к входу обнаружено."
        echo "QEMU PID: $QEMU_PID"
        echo "Система готова для тестирования"
        exit 0
    elif curl -k -s https://localhost:8443 > /dev/null 2>&1; then
        echo "OpenBMC успешно запущен и доступен на https://localhost:8443"
        echo "QEMU PID: $QEMU_PID"
        exit 0
    elif curl -s http://localhost:8082 > /dev/null 2>&1; then
        echo "OpenBMC успешно запущен и доступен на http://localhost:8082"
        echo "QEMU PID: $QEMU_PID"
        exit 0
    fi
    
    echo "Ожидание... ($WAIT_TIME/$MAX_WAIT секунд)"
    
    if grep -q "Starting kernel" "$QEMU_LOG" 2>/dev/null; then
        echo "✓ Ядро Linux запущено"
    fi
    if grep -q "systemd" "$QEMU_LOG" 2>/dev/null; then
        echo "✓ Systemd сервисы запускаются"
    fi
    if grep -q "Phosphor OpenBMC" "$QEMU_LOG" 2>/dev/null; then
        echo "✓ OpenBMC система инициализируется"
    fi
    
    echo "Проверка сетевого подключения:"
    echo "  - Проверка HTTPS (8443): $(curl -k -s -o /dev/null -w '%{http_code}' https://localhost:8443 2>/dev/null || echo 'недоступен')"
    echo "  - Проверка HTTP (8082): $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8082 2>/dev/null || echo 'недоступен')"
    sleep $INTERVAL
    WAIT_TIME=$((WAIT_TIME + INTERVAL))
done

echo "ПРЕДУПРЕЖДЕНИЕ: OpenBMC не ответил в течение $MAX_WAIT секунд"
echo "Но QEMU продолжает работать в фоне с PID: $QEMU_PID"

if grep -q "romulus login:" "$QEMU_LOG" 2>/dev/null; then
    echo "✓ Система загрузилась! Приглашение к входу найдено."
    echo "✓ OpenBMC готов для тестирования через консоль"
else
    echo "⚠ Система еще загружается..."
fi

echo ""
echo "Для подключения к OpenBMC используйте:"
echo "  HTTPS: https://localhost:8443"
echo "  HTTP:  http://localhost:8082"
echo "  Консоль: docker exec jenkins tail -f /tmp/qemu.log"
echo ""
echo "QEMU процесс оставлен запущенным для дальнейшего тестирования"
exit 0
