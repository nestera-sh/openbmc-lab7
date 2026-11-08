#!/bin/bash
set -e

echo "Starting OpenBMC QEMU (romulus-bmc)..."
mkdir -p reports/qemu

IMAGE_PATH="/images/obmc-phosphor-image-romulus.static.mtd"

if [ ! -f "$IMAGE_PATH" ]; then
    echo "ERROR: Image file not found at $IMAGE_PATH"
    exit 1
fi


nohup qemu-system-arm -m 256 -M romulus-bmc -nographic \
-drive file=${IMAGE_PATH},format=raw,if=mtd,snapshot=on \
-net nic -net user,hostfwd=udp:0.0.0.0:2623-:623,hostfwd=tcp:0.0.0.0:2222-:22,hostfwd=tcp:0.0.0.0:2443-:443,hostname=qemu \
> reports/qemu/qemu.log 2>&1 &

echo $! > reports/qemu/qemu.pid
echo "QEMU started with PID $(cat reports/qemu/qemu.pid)"

echo "Waiting for OpenBMC to boot..."

for i in $(seq 1 30); do
    if nc -z 127.0.0.1 2443; then
        echo "OpenBMC is up and responding on port 2443!"
        exit 0
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo "ERROR: OpenBMC did not start in time."
cat reports/qemu/qemu.log
exit 1