#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${TARGET_USER:-lazuli}"
SUDO_PASS="${SUDO_PASS:-}"
USER_HOME="/home/${TARGET_USER}"
MM_DIR="${USER_HOME}/MagicMirror"
AUTOSTART_DIR="${USER_HOME}/.config/autostart"
BIN_DIR="${USER_HOME}/bin"
LIGHTDM_AUTLOGIN_FILE="/etc/lightdm/lightdm.conf.d/23-${TARGET_USER}-display-autologin.conf"
SERVICE_FILE="/etc/systemd/system/magicmirror.service"
BOOT_ENV_FILE="/boot/orangepiEnv.txt"
XORG_CONF_DIR="/etc/X11/xorg.conf.d"
XORG_CONF_FILE="${XORG_CONF_DIR}/90-hdmi1-rotation.conf"

if [[ -z "${SUDO_PASS}" ]]; then
  echo "SUDO_PASS environment variable is required." >&2
  exit 1
fi

sudo_run() {
  printf '%s\n' "${SUDO_PASS}" | sudo -S "$@"
}

echo "[1/8] Installing system packages"
sudo_run apt-get update
sudo_run apt-get install -y ca-certificates curl build-essential python3 make g++ git x11-xserver-utils unclutter

echo "[2/8] Installing Node.js 22"
if ! command -v node >/dev/null 2>&1 || ! node -v | grep -Eq '^v22\.'; then
  TMP_NODESOURCE="$(mktemp)"
  curl -fsSL https://deb.nodesource.com/setup_22.x -o "${TMP_NODESOURCE}"
  sudo_run bash "${TMP_NODESOURCE}"
  rm -f "${TMP_NODESOURCE}"
  sudo_run apt-get install -y nodejs
fi

echo "[3/8] Cloning or updating MagicMirror"
if [[ -d "${MM_DIR}/.git" ]]; then
  git -C "${MM_DIR}" fetch --tags
  git -C "${MM_DIR}" pull --ff-only
else
  git clone https://github.com/MagicMirrorOrg/MagicMirror.git "${MM_DIR}"
fi

echo "[4/8] Installing MagicMirror dependencies"
cd "${MM_DIR}"
node --run install-mm

echo "[5/8] Installing MMM-Remote-Control"
mkdir -p "${MM_DIR}/modules"
if [[ -d "${MM_DIR}/modules/MMM-Remote-Control/.git" ]]; then
  git -C "${MM_DIR}/modules/MMM-Remote-Control" pull --ff-only
else
  git clone https://github.com/Jopyth/MMM-Remote-Control.git "${MM_DIR}/modules/MMM-Remote-Control"
fi
npm --prefix "${MM_DIR}/modules/MMM-Remote-Control" install

echo "[6/8] Writing MagicMirror configuration"
API_KEY="$(python3 - <<'PY'
import secrets
print(secrets.token_hex(16))
PY
)"

if [[ -f "${MM_DIR}/config/config.js" && ! -f "${MM_DIR}/config/config.js.pre-orangepi-magicmirror.bak" ]]; then
  cp "${MM_DIR}/config/config.js" "${MM_DIR}/config/config.js.pre-orangepi-magicmirror.bak"
fi

cat > "${MM_DIR}/config/config.js" <<EOF_CONFIG
/* Managed by OrangePi project automation on 2026-06-10 */
let config = {
  address: "0.0.0.0",
  port: 8080,
  ipWhitelist: [
    "127.0.0.1",
    "::ffff:127.0.0.1",
    "::1",
    "192.168.50.0/24",
    "::ffff:192.168.50.0/120"
  ],
  language: "en",
  locale: "en-US",
  timeFormat: 24,
  units: "metric",
  zoom: 0.95,
  modules: [
    {
      module: "alert"
    },
    {
      module: "updatenotification",
      position: "top_bar"
    },
    {
      module: "clock",
      position: "top_left"
    },
    {
      module: "calendar",
      header: "Calendar",
      position: "top_right",
      config: {
        maximumEntries: 6,
        maximumNumberOfDays: 30
      }
    },
    {
      module: "compliments",
      position: "lower_third"
    },
    {
      module: "newsfeed",
      position: "bottom_bar",
      config: {
        feeds: [
          {
            title: "BBC World",
            url: "https://feeds.bbci.co.uk/news/world/rss.xml"
          }
        ],
        showSourceTitle: true,
        showPublishDate: true,
        broadcastNewsFeeds: true,
        broadcastNewsUpdates: true
      }
    },
    {
      module: "MMM-Remote-Control",
      config: {
        apiKey: "${API_KEY}",
        secureEndpoints: true,
        showModuleApiMenu: true
      }
    }
  ]
};

if (typeof module !== "undefined") {
  module.exports = config;
}
EOF_CONFIG

echo "${API_KEY}" > "${MM_DIR}/config/remote-control-api-key.txt"
chmod 600 "${MM_DIR}/config/remote-control-api-key.txt"

echo "[7/8] Configuring service and kiosk startup"
mkdir -p "${BIN_DIR}" "${AUTOSTART_DIR}"

cat > "${BIN_DIR}/start-magicmirror-kiosk.sh" <<EOF_KIOSK
#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="\${DISPLAY:-:0}"
export XAUTHORITY="\${XAUTHORITY:-${USER_HOME}/.Xauthority}"
export XDG_RUNTIME_DIR="/run/user/\$(id -u)"

sleep 8

if command -v xset >/dev/null 2>&1; then
  xset -dpms || true
  xset s off || true
  xset s noblank || true
fi

if command -v unclutter >/dev/null 2>&1; then
  pkill unclutter 2>/dev/null || true
  unclutter --timeout 0 --jitter 1 --ignore-scrolling &
fi

pkill -f "chromium.*127.0.0.1:8080" 2>/dev/null || true

exec chromium-browser \
  --kiosk \
  --incognito \
  --noerrdialogs \
  --disable-session-crashed-bubble \
  --disable-infobars \
  --autoplay-policy=no-user-gesture-required \
  --check-for-update-interval=31536000 \
  http://127.0.0.1:8080
EOF_KIOSK
chmod +x "${BIN_DIR}/start-magicmirror-kiosk.sh"

cat > "${AUTOSTART_DIR}/magicmirror-kiosk.desktop" <<EOF_DESKTOP
[Desktop Entry]
Type=Application
Version=1.0
Name=MagicMirror Kiosk
Comment=Launch MagicMirror in Chromium kiosk mode
Exec=${BIN_DIR}/start-magicmirror-kiosk.sh
Terminal=false
X-GNOME-Autostart-enabled=true
EOF_DESKTOP

echo "[7b/8] Configuring persistent display rotation"
if sudo_run grep -q '^extraargs=' "${BOOT_ENV_FILE}"; then
  sudo_run sed -i -E 's/^extraargs=.*/extraargs=fbcon=rotate:2/' "${BOOT_ENV_FILE}"
else
  printf 'extraargs=fbcon=rotate:2\n' | sudo_run tee -a "${BOOT_ENV_FILE}" >/dev/null
fi

sudo_run mkdir -p "${XORG_CONF_DIR}"
sudo_run tee "${XORG_CONF_FILE}" >/dev/null <<'EOF_XORG'
Section "Monitor"
    Identifier "HDMI-1"
    Option "Rotate" "inverted"
    Option "PreferredMode" "480x1920"
EndSection
EOF_XORG

TMP_SERVICE="$(mktemp)"
cat > "${TMP_SERVICE}" <<EOF_SERVICE
[Unit]
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=${TARGET_USER}
WorkingDirectory=${MM_DIR}
Environment=NODE_ENV=production
ExecStart=/usr/bin/node --run server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF_SERVICE
sudo_run install -m 0644 "${TMP_SERVICE}" "${SERVICE_FILE}"
rm -f "${TMP_SERVICE}"

TMP_LIGHTDM="$(mktemp)"
cat > "${TMP_LIGHTDM}" <<EOF_LIGHTDM
[Seat:*]
autologin-user=${TARGET_USER}
autologin-user-timeout=0
user-session=xfce
EOF_LIGHTDM
sudo_run install -m 0644 "${TMP_LIGHTDM}" "${LIGHTDM_AUTLOGIN_FILE}"
rm -f "${TMP_LIGHTDM}"

sudo_run systemctl daemon-reload
sudo_run systemctl enable --now magicmirror.service

echo "[8/8] Verification"
systemctl is-active --quiet --user 2>/dev/null || true
sudo_run systemctl is-enabled magicmirror.service >/dev/null
sudo_run systemctl is-active magicmirror.service >/dev/null

echo "MagicMirror install completed."
echo "Remote URL: http://192.168.50.71:8080"
echo "Remote control URL: http://192.168.50.71:8080/remote.html"
echo "Remote control API key stored at: ${MM_DIR}/config/remote-control-api-key.txt"
