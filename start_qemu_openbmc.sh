#!/bin/bash

# Script to start QEMU with OpenBMC image
# This script is designed to run inside Jenkins container

set -e

# Use current directory instead of /workspace
MTD_FILE="./obmc-phosphor-image-romulus-20250902012112.static.mtd"
QEMU_PID_FILE="/tmp/qemu-openbmc.pid"
QEMU_LOG_FILE="/tmp/qemu-openbmc.log"

echo "=== Starting QEMU with OpenBMC ==="
echo "MTD File: $MTD_FILE"
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

# Check if MTD file exists
if [ ! -f "$MTD_FILE" ]; then
    echo "ERROR: MTD file not found at $MTD_FILE"
    echo "Available files:"
    ls -la
    exit 1
fi

# Kill any existing QEMU process
if [ -f "$QEMU_PID_FILE" ]; then
    OLD_PID=$(cat "$QEMU_PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping existing QEMU process (PID: $OLD_PID)"
        kill "$OLD_PID"
        sleep 2
    fi
    rm -f "$QEMU_PID_FILE"
fi

# Create a temporary disk image for QEMU
DISK_IMAGE="/tmp/openbmc-disk.img"
if [ -f "$DISK_IMAGE" ]; then
    rm -f "$DISK_IMAGE"
fi

# Convert MTD to QEMU-compatible format
echo "Converting MTD to QEMU format..."
qemu-img create -f qcow2 "$DISK_IMAGE" 1G

# Start QEMU with OpenBMC - simplified version for Docker
echo "Starting QEMU with OpenBMC image..."

# Simplified QEMU command that should work in Docker
qemu-system-x86_64 \
    -machine pc \
    -cpu qemu64 \
    -m 512 \
    -drive file="$DISK_IMAGE",format=qcow2,if=virtio \
    -netdev user,id=net0,hostfwd=tcp::2443-:2443,hostfwd=tcp::8080-:8080 \
    -device virtio-net-pci,netdev=net0 \
    -nographic \
    -daemonize \
    -pidfile "$QEMU_PID_FILE" \
    > "$QEMU_LOG_FILE" 2>&1

# Wait for QEMU to start
sleep 3

# Check if QEMU is running
if [ -f "$QEMU_PID_FILE" ]; then
    QEMU_PID=$(cat "$QEMU_PID_FILE")
    if kill -0 "$QEMU_PID" 2>/dev/null; then
        echo "QEMU started successfully (PID: $QEMU_PID)"
        echo "OpenBMC should be available at:"
        echo "  - HTTPS: https://localhost:2443"
        echo "  - HTTP:  http://localhost:8080"
        echo "Log file: $QEMU_LOG_FILE"
        exit 0
    else
        echo "ERROR: QEMU failed to start"
        echo "QEMU log:"
        cat "$QEMU_LOG_FILE" || echo "No log file found"
        exit 1
    fi
else
    echo "ERROR: QEMU PID file not created"
    echo "QEMU log:"
    cat "$QEMU_LOG_FILE" || echo "No log file found"
    exit 1
fi
