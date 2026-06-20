#!/usr/bin/env bash
set -euo pipefail

BOOT_ENV="/boot/orangepiEnv.txt"
KIOSK_SCRIPT="/home/lazuli/bin/start-magicmirror-kiosk.sh"
XORG_CONF_DIR="/etc/X11/xorg.conf.d"
XORG_CONF_FILE="${XORG_CONF_DIR}/90-hdmi1-rotation.conf"

sudo cp "${BOOT_ENV}" "${BOOT_ENV}.pre-rotation-cleanup.bak"
sudo cp "${KIOSK_SCRIPT}" "${KIOSK_SCRIPT}.pre-rotation-cleanup.bak"

if sudo grep -q '^extraargs=' "${BOOT_ENV}"; then
  sudo sed -i -E 's/^extraargs=.*/extraargs=fbcon=rotate:2/' "${BOOT_ENV}"
else
  printf 'extraargs=fbcon=rotate:2\n' | sudo tee -a "${BOOT_ENV}" >/dev/null
fi

python3 <<'PY'
from pathlib import Path

path = Path("/home/lazuli/bin/start-magicmirror-kiosk.sh")
text = path.read_text()

block = """if command -v xrandr >/dev/null 2>&1; then
  output=\"$(xrandr --query | awk '/ connected/{print $1; exit}')\"
  if [[ -n \"${output}\" ]]; then
    xrandr --output \"${output}\" --rotate inverted || true
  fi
fi

"""

if block in text:
    text = text.replace(block, "")

path.write_text(text)
PY

sudo mkdir -p "${XORG_CONF_DIR}"
sudo tee "${XORG_CONF_FILE}" >/dev/null <<'EOF'
Section "Monitor"
    Identifier "HDMI-1"
    Option "Rotate" "inverted"
    Option "PreferredMode" "480x1920"
EndSection
EOF

echo "Updated ${BOOT_ENV}"
echo "Updated ${KIOSK_SCRIPT}"
echo "Wrote ${XORG_CONF_FILE}"
