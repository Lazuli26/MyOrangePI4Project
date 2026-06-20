# XRDP And Autologin Change Record

## Purpose

This note records the LightDM autologin change made on the Orange Pi on `2026-06-03` to reduce conflicts between the local desktop seat and XRDP logins.

## What Changed

- Confirmed that `lightdm` was auto-logging `orangepi` into the local XFCE desktop.
- Found the active autologin config at:
  - `/etc/lightdm/lightdm.conf.d/22-orangepi-autologin.conf`
- Backed up the file to:
  - `/etc/lightdm/lightdm.conf.d/22-orangepi-autologin.conf.bak`
- Disabled the active autologin file by renaming it to:
  - `/etc/lightdm/lightdm.conf.d/22-orangepi-autologin.conf.disabled`
- Restarted `lightdm`

## Why

- The physical desktop seat was already occupied by `orangepi` through LightDM autologin.
- XRDP was working for `lazuli` in a separate remote session.
- This makes it plausible that local-seat autologin was interfering with XRDP use for `orangepi`.

## Result

- `lightdm` now starts to the greeter instead of auto-logging `orangepi`
- The previous `lightdm-autologin` log entry for `orangepi` is gone after restart
- The active desktop seat is now owned by the greeter user until someone logs in locally

## Follow-Up XRDP Fix

After reboot, XRDP for `orangepi` still failed even though `lazuli` could log in successfully.

Observed behavior:

- XRDP accepted valid `orangepi` credentials
- Xorg started for the session
- the window manager exited immediately and the client was disconnected

Observed log pattern for `orangepi`:

```text
Authorization required, but no authorization protocol specified
xfce4-session: Cannot open display: .
```

Interpretation:

- The original `orangepi` account had stale X11 session state from the vendor image and earlier local desktop use
- `~/.Xauthority` was old and nearly empty
- XRDP/XFCE for `orangepi` failed because the desktop session could not attach cleanly to the new X11 display
- This was not a password or account-lock issue
- This was not a security hardening measure

Fix applied:

- Created backup directory:
  - `/home/orangepi/xrdp-session-backup`
- Moved the following out of the way so XRDP could recreate them cleanly:
  - `/home/orangepi/.Xauthority`
  - `/home/orangepi/.ICEauthority`
  - session cache files under `/home/orangepi/.cache/sessions/`
- Recreated an empty `/home/orangepi/.Xauthority` with correct ownership and mode

Current result:

- XRDP login for `orangepi` now works

Rollback for the XRDP-session-file cleanup, if ever needed:

```bash
rm -f /home/orangepi/.Xauthority
cp /home/orangepi/xrdp-session-backup/.Xauthority.pre-xrdp-fix /home/orangepi/.Xauthority
cp /home/orangepi/xrdp-session-backup/.ICEauthority.pre-xrdp-fix /home/orangepi/.ICEauthority
cp /home/orangepi/xrdp-session-backup/cache-sessions/* /home/orangepi/.cache/sessions/
chown orangepi:orangepi /home/orangepi/.Xauthority /home/orangepi/.ICEauthority /home/orangepi/.cache/sessions/* 2>/dev/null || true
chmod 600 /home/orangepi/.Xauthority /home/orangepi/.ICEauthority 2>/dev/null || true
```

## Revert To Autologin

To restore the old behavior:

```bash
sudo mv /etc/lightdm/lightdm.conf.d/22-orangepi-autologin.conf.disabled /etc/lightdm/lightdm.conf.d/22-orangepi-autologin.conf
sudo systemctl restart lightdm
```

If you want to compare with the preserved backup first:

```bash
cat /etc/lightdm/lightdm.conf.d/22-orangepi-autologin.conf.bak
```

The original autologin file contents were:

```ini
[Seat:*]
autologin-user=orangepi
autologin-user-timeout=0
user-session=xfce
```

## Operational Impact

- Good for XRDP if you want to log in as `orangepi` instead of keeping a second user only for remote desktop
- Neutral for services that start with `systemd`, Docker, cron, or other boot-time mechanisms
- Potentially undesirable only if you depend on local GUI applications launching automatically as part of a desktop session at boot

## OpenClaw Impact

- `OpenClaw` is not affected by disabling desktop autologin
- It was installed as a user-space CLI under `/home/orangepi/.openclaw`
- Verification after the LightDM change still succeeds:

```bash
/usr/local/bin/openclaw --version
```

Expected result at the time of change:

```text
OpenClaw 2026.5.28 (e932160)
```
