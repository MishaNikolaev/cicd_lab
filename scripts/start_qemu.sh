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
MAX_WAIT=130
WAIT_TIME=0
INTERVAL=10

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if curl -k -s https://localhost:8443 > /dev/null 2>&1; then
        echo "OpenBMC успешно запущен и доступен на https://localhost:8443"
        echo "QEMU PID: $QEMU_PID"
        exit 0
    elif curl -s http://localhost:8082 > /dev/null 2>&1; then
        echo "OpenBMC успешно запущен и доступен на http://localhost:8082"
        echo "QEMU PID: $QEMU_PID"
        exit 0
    fi
    
    echo "Ожидание... ($WAIT_TIME/$MAX_WAIT секунд)"
    sleep $INTERVAL
    WAIT_TIME=$((WAIT_TIME + INTERVAL))
done

echo "ОШИБКА: OpenBMC не запустился в течение $MAX_WAIT секунд"
echo "Логи QEMU:"
cat "$QEMU_LOG"
exit 1
