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
    -netdev user,id=net0,hostfwd=tcp::8443-:443,hostfwd=tcp::8082-:80 \
    -device ftgmac100,netdev=net0 \
    -bios /usr/share/qemu-efi-aarch64/QEMU_EFI.fd \
    > "$QEMU_LOG" 2>&1 &

QEMU_PID=$!
echo "QEMU запущен с PID: $QEMU_PID"

echo "$QEMU_PID" > /tmp/qemu.pid

echo "QEMU процесс запущен в фоне"
echo "Для подключения к OpenBMC используйте:"
echo "  HTTPS: https://localhost:8443"
echo "  HTTP:  http://localhost:8082"
echo "  Консоль: docker exec jenkins tail -f /tmp/qemu.log"
echo ""
echo "QEMU процесс оставлен запущенным для дальнейшего тестирования"
exit 0
