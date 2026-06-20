# MagicMirror Install Record

## Purpose

This note records the MagicMirror setup applied to the Orange Pi on `2026-06-10` so the board can drive a dedicated HDMI display without acting as a Windows-side extra monitor.

## Installed Components

- Installed `Node.js 22.22.3` from NodeSource
- Cloned `MagicMirror` to:
  - `/home/lazuli/MagicMirror`
- Installed the `MMM-Remote-Control` module under:
  - `/home/lazuli/MagicMirror/modules/MMM-Remote-Control`
- Added a reusable remote installer script in this repo:
  - `docs/install_magicmirror_remote.sh`

## Configured Runtime

- Added a systemd service:
  - `/etc/systemd/system/magicmirror.service`
- Enabled the service at boot:
  - `systemctl enable --now magicmirror.service`
- MagicMirror now runs in `server only` mode on:
  - `http://192.168.50.71:8080`
- Remote control UI is available on:
  - `http://192.168.50.71:8080/remote.html`

## Local Display Behavior

- Enabled `lightdm` autologin for `lazuli` using:
  - `/etc/lightdm/lightdm.conf.d/23-lazuli-display-autologin.conf`
- Added a local XFCE autostart entry:
  - `/home/lazuli/.config/autostart/magicmirror-kiosk.desktop`
- Added the kiosk launcher script:
  - `/home/lazuli/bin/start-magicmirror-kiosk.sh`

The kiosk script currently does the following:

- waits briefly for the desktop and local web app to settle
- disables DPMS / screen blanking via `xset`
- starts `unclutter`
- rotates the first connected X11 output to `right`
- launches `chromium-browser` in kiosk mode against `http://127.0.0.1:8080`

## MagicMirror Config

- Active config file:
  - `/home/lazuli/MagicMirror/config/config.js`
- API key file for `MMM-Remote-Control`:
  - `/home/lazuli/MagicMirror/config/remote-control-api-key.txt`
- A backup of any previous config is preserved at:
  - `/home/lazuli/MagicMirror/config/config.js.pre-orangepi-magicmirror.bak`

The generated config currently includes:

- LAN listening on `0.0.0.0:8080`
- local-network whitelist for `192.168.50.0/24`
- core modules:
  - `alert`
  - `updatenotification`
  - `clock`
  - `calendar`
  - `compliments`
  - `newsfeed`
- `MMM-Remote-Control`

## Validation Performed

Verified after install and reboot:

- `magicmirror.service` is `active`
- LightDM starts an XFCE session for `lazuli`
- `chromium-browser` is running in kiosk mode under `lazuli`
- the MagicMirror UI returns HTTP `200` from another machine on the LAN

## Important Notes

- `orangepi` autologin remains disabled; the new local display path is based on `lazuli`
- this helps preserve `orangepi` as the safer admin account for SSH/XRDP if session conflicts ever appear
- the board was validated while `HDMI-1` showed as disconnected, so the portrait rotation path has been prepared but not fully observed on a live HDMI-attached screen yet
- root storage is still the SD card, so avoid treating this board as a heavy media cache until eMMC or other persistent storage is installed
