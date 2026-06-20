#!/usr/bin/env bash
set -euo pipefail

TARGET_HOST_IP="${TARGET_HOST_IP:-192.168.50.71}"
SUDO_PASS="${SUDO_PASS:-}"
SMB_PASS="${SMB_PASS:-${SUDO_PASS}}"
USB_UUID="${USB_UUID:-1C0D-3B51}"
MOUNT_DIR="${MOUNT_DIR:-/srv/nas/usb500gb}"
SHARE_NAME="${SHARE_NAME:-usb500gb}"
UNIX_USER="${UNIX_USER:-orangepi}"
UNIX_GROUP="${UNIX_GROUP:-orangepi}"
LAN_PREFIX="${LAN_PREFIX:-192.168.50.}"
FSTAB_FILE="/etc/fstab"
SMB_CONF_FILE="/etc/samba/smb.conf"
FSTAB_LINE="UUID=${USB_UUID} ${MOUNT_DIR} vfat uid=1000,gid=1000,fmask=0002,dmask=0002,utf8=1,shortname=mixed,nofail,x-systemd.automount,x-systemd.idle-timeout=5min 0 0"
SHARE_BEGIN="# BEGIN ORANGEPI NAS SHARE ${SHARE_NAME}"
SHARE_END="# END ORANGEPI NAS SHARE ${SHARE_NAME}"

if [[ -z "${SUDO_PASS}" ]]; then
  echo "SUDO_PASS environment variable is required." >&2
  exit 1
fi

if [[ -z "${SMB_PASS}" ]]; then
  echo "SMB_PASS environment variable is required." >&2
  exit 1
fi

sudo_run() {
  printf '%s\n' "${SUDO_PASS}" | sudo -S -p '' "$@"
}

echo "[1/8] Installing Samba and WS-Discovery support"
sudo_run apt-get update
printf '%s\n' "${SUDO_PASS}" | sudo -S -p '' env DEBIAN_FRONTEND=noninteractive apt-get install -y samba wsdd

echo "[2/8] Preparing mount path"
sudo_run mkdir -p "${MOUNT_DIR}"
sudo_run chown "${UNIX_USER}:${UNIX_GROUP}" "${MOUNT_DIR}"
sudo_run chmod 0775 "${MOUNT_DIR}"

if [[ -f "${FSTAB_FILE}" && ! -f "${FSTAB_FILE}.pre-orangepi-nas.bak" ]]; then
  sudo_run cp "${FSTAB_FILE}" "${FSTAB_FILE}.pre-orangepi-nas.bak"
fi

if ! grep -Fq "UUID=${USB_UUID} " "${FSTAB_FILE}"; then
  TMP_FSTAB="$(mktemp)"
  cp "${FSTAB_FILE}" "${TMP_FSTAB}"
  printf '%s\n' "${FSTAB_LINE}" >> "${TMP_FSTAB}"
  sudo_run install -m 0644 "${TMP_FSTAB}" "${FSTAB_FILE}"
  rm -f "${TMP_FSTAB}"
fi

echo "[3/8] Mounting USB drive"
if ! findmnt -rn "${MOUNT_DIR}" >/dev/null 2>&1; then
  sudo_run mount "${MOUNT_DIR}"
fi

echo "[4/8] Preparing mounted share path"
if [[ ! -d "${MOUNT_DIR}" ]]; then
  echo "Mount path ${MOUNT_DIR} is not available after mounting." >&2
  exit 1
fi

echo "[5/8] Creating Samba credentials"
TMP_SMB_PASS="$(mktemp)"
printf '%s\n%s\n' "${SMB_PASS}" "${SMB_PASS}" > "${TMP_SMB_PASS}"
if sudo_run pdbedit -L -u "${UNIX_USER}" >/dev/null 2>&1; then
  printf '%s\n' "${SUDO_PASS}" | sudo -S -p '' bash -c "smbpasswd -s '${UNIX_USER}' < '${TMP_SMB_PASS}'" >/dev/null
else
  printf '%s\n' "${SUDO_PASS}" | sudo -S -p '' bash -c "smbpasswd -a -s '${UNIX_USER}' < '${TMP_SMB_PASS}'" >/dev/null
fi
rm -f "${TMP_SMB_PASS}"
sudo_run smbpasswd -e "${UNIX_USER}" >/dev/null

echo "[6/8] Writing Samba share configuration"
if [[ -f "${SMB_CONF_FILE}" && ! -f "${SMB_CONF_FILE}.pre-orangepi-nas.bak" ]]; then
  sudo_run cp "${SMB_CONF_FILE}" "${SMB_CONF_FILE}.pre-orangepi-nas.bak"
fi

TMP_SHARE="$(mktemp)"
cat > "${TMP_SHARE}" <<EOF_SHARE
${SHARE_BEGIN}
[${SHARE_NAME}]
   path = ${MOUNT_DIR}
   browseable = yes
   read only = no
   guest ok = no
   valid users = ${UNIX_USER}
   force user = ${UNIX_USER}
   force group = ${UNIX_GROUP}
   create mask = 0664
   directory mask = 0775
   hosts allow = 127. ${LAN_PREFIX}
${SHARE_END}
EOF_SHARE

TMP_SCRIPT="$(mktemp)"
cat > "${TMP_SCRIPT}" <<'EOF_SCRIPT'
from pathlib import Path
import os

conf_path = Path(os.environ["SMB_CONF_FILE"])
share_begin = os.environ["SHARE_BEGIN"]
share_end = os.environ["SHARE_END"]
new_block = Path(os.environ["TMP_SHARE"]).read_text()
text = conf_path.read_text()
start = text.find(share_begin)
end = text.find(share_end)
if start != -1 and end != -1:
    end += len(share_end)
    updated = text[:start].rstrip() + "\n\n" + new_block.strip() + "\n"
else:
    updated = text.rstrip() + "\n\n" + new_block.strip() + "\n"
tmp_out = Path("/tmp/orangepi-smb.conf")
tmp_out.write_text(updated)
print(tmp_out)
EOF_SCRIPT

UPDATED_CONF="$(SMB_CONF_FILE="${SMB_CONF_FILE}" SHARE_BEGIN="${SHARE_BEGIN}" SHARE_END="${SHARE_END}" TMP_SHARE="${TMP_SHARE}" python3 "${TMP_SCRIPT}")"
sudo_run install -m 0644 "${UPDATED_CONF}" "${SMB_CONF_FILE}"
rm -f "${TMP_SHARE}" "${TMP_SCRIPT}" "${UPDATED_CONF}"

echo "[7/8] Enabling Samba and WS-Discovery services"
sudo_run testparm -s >/dev/null
sudo_run systemctl enable --now smbd nmbd
sudo_run systemctl restart smbd nmbd
sudo_run systemctl enable --now wsdd
sudo_run systemctl restart wsdd

echo "[8/8] Verification"
echo "## FINDMNT"
findmnt "${MOUNT_DIR}" || true
echo
echo "## SAMBA_STATUS"
sudo_run systemctl is-enabled smbd nmbd
sudo_run systemctl is-active smbd nmbd
echo
echo "## WSDD_STATUS"
sudo_run systemctl is-enabled wsdd
sudo_run systemctl is-active wsdd
echo
echo "## SMB_PORTS"
sudo_run ss -tlnp | grep -E ':(139|445)\s' || true
echo
echo "## SHARE_HINT"
echo "Host: ${TARGET_HOST_IP}"
echo "Share path: \\\\${TARGET_HOST_IP}\\${SHARE_NAME}"
echo "Username: ${UNIX_USER}"
echo "Mount path: ${MOUNT_DIR}"
