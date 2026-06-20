#!/usr/bin/env bash
set -euo pipefail

mkdir -p /tmp/orangepi-sd-tune

cat >/tmp/orangepi-sd-tune/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

printf '%s\n' 'orangepi' | sudo -S -p '' mkdir -p /etc/docker

if [ -f /etc/docker/daemon.json ]; then
  printf '%s\n' 'orangepi' | sudo -S -p '' cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
fi

printf '%s\n' 'orangepi' | sudo -S -p '' install -m 644 /tmp/orangepi-sd-tune/daemon.json /etc/docker/daemon.json

if systemctl is-active --quiet docker; then
  printf '%s\n' 'orangepi' | sudo -S -p '' systemctl restart docker
fi

echo "## DAEMON_JSON"
cat /etc/docker/daemon.json
echo

echo "## DOCKER_INFO"
docker info 2>/dev/null | grep -E 'Logging Driver|Docker Root Dir|Storage Driver' || true

rm -rf /tmp/orangepi-sd-tune
