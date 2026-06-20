#!/usr/bin/env bash
set -u

section() {
  printf '\n## %s\n' "$1"
}

section "BASIC"
date -Is
hostname
whoami

section "BOARD"
(cat /proc/device-tree/model 2>/dev/null || true) | tr -d '\0'
uname -a

section "OS"
cat /etc/os-release
hostnamectl 2>/dev/null || true

section "CPU"
lscpu || true

section "MEMORY"
free -h || true

section "STORAGE"
lsblk -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINT,MODEL,TRAN,SERIAL || true
df -hT || true
findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS / /boot /boot/firmware 2>/dev/null || true

section "NETWORK"
ip -br a || true
ip route || true
ss -tulpn 2>/dev/null | head -n 200 || true

section "SERVICES_RUNNING"
systemctl --type=service --state=running --no-pager --no-legend 2>/dev/null | head -n 200 || true

section "SERVICES_ENABLED"
systemctl list-unit-files --state=enabled --type=service --no-pager --no-legend 2>/dev/null | head -n 200 || true

section "REMOTE_ACCESS"
systemctl status ssh --no-pager 2>/dev/null | head -n 80 || true
systemctl status xrdp --no-pager 2>/dev/null | head -n 80 || true
systemctl status xrdp-sesman --no-pager 2>/dev/null | head -n 80 || true

section "PACKAGES"
dpkg-query -W -f='${binary:Package} ${Version}\n' \
  xrdp openssh-server docker.io containerd network-manager lightdm xfce4 \
  2>/dev/null || true

section "BOOT_CONFIG"
cat /boot/orangepiEnv.txt 2>/dev/null || true
cat /boot/extlinux/extlinux.conf 2>/dev/null || true

section "KERNEL_MODULES"
lsmod | head -n 120 || true

section "BUS"
lspci -nn 2>/dev/null || true
lsusb 2>/dev/null || true

section "UPTIME"
uptime -p || true
uptime -s || true

section "USERS"
getent passwd orangepi lazuli 2>/dev/null || true
id 2>/dev/null || true
groups 2>/dev/null || true

section "SUDO"
if sudo -n true >/dev/null 2>&1; then
  echo "passwordless_sudo=yes"
else
  echo "passwordless_sudo=no"
fi
