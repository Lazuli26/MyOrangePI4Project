#!/usr/bin/env bash
set -euo pipefail

echo "## DOCKER_BIN"
docker --version 2>/dev/null || true
echo

echo "## DOCKER_SERVICE"
systemctl is-enabled docker 2>/dev/null || true
systemctl is-active docker 2>/dev/null || true
systemctl is-enabled containerd 2>/dev/null || true
systemctl is-active containerd 2>/dev/null || true
echo

echo "## DOCKER_INFO"
docker info 2>/dev/null | grep -E 'Server Version|Docker Root Dir|Logging Driver|Storage Driver|Cgroup Driver' || true
echo

echo "## DAEMON_JSON"
cat /etc/docker/daemon.json 2>/dev/null || echo "absent"
