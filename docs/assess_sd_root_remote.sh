#!/usr/bin/env bash
set -euo pipefail

echo "## ROOT"
findmnt -no SOURCE,FSTYPE,OPTIONS /
echo

echo "## MMC"
for d in /sys/block/mmcblk*; do
  [ -e "$d" ] || continue
  b="$(basename "$d")"
  echo "[$b]"
  for f in type name manfid oemid serial date hwrev fwrev; do
    [ -r "$d/device/$f" ] && printf '%s=%s\n' "$f" "$(cat "$d/device/$f")"
  done
  echo
done

echo "## LSBLK"
lsblk -o NAME,PATH,SIZE,TYPE,MOUNTPOINT,MODEL,SERIAL,TRAN
echo

echo "## FSTAB"
cat /etc/fstab
echo

echo "## BOOTENV"
cat /boot/orangepiEnv.txt 2>/dev/null || true
echo

echo "## RAMLOG"
systemctl is-enabled orangepi-ramlog.service 2>/dev/null || true
systemctl is-active orangepi-ramlog.service 2>/dev/null || true
mount | grep ' /var/log ' || true
echo

echo "## ZRAM"
swapon --show || true
echo
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT | grep zram || true
echo

echo "## JOURNAL"
grep -RInE '^(Storage|SystemMaxUse|RuntimeMaxUse)=' /etc/systemd/journald.conf /etc/systemd/journald.conf.d 2>/dev/null || true
echo

echo "## DOCKER"
docker info 2>/dev/null | grep -E 'Docker Root Dir|Logging Driver|Storage Driver' || true
echo

echo "## SNAP"
du -sh /var/lib/snapd 2>/dev/null || true
snap list 2>/dev/null | head -n 20 || true
echo

echo "## MOUNTS"
mount | egrep ' on / | on /var/log | on /tmp ' || true
echo

echo "## ROOT_OPTIONS"
findmnt -no OPTIONS /
