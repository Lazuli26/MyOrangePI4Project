# Internal Access Sheet

## Scope

This file contains internal-only access details for the Orange Pi board.

Do not share outside the internal team.

## Primary Target

- Hostname: `orangepi4pro`
- IP: `192.168.50.71`
- Access methods confirmed:
  - `ssh`
  - `xrdp`

## Credentials

### User: `orangepi`

- Username: `orangepi`
- Password: `orangepi`
- `sudo`: yes, password required

### User: `lazuli`

- Username: `lazuli`
- Password: `lazuli`
- `sudo`: yes, password required

## Access Notes

- `orangepi` is in the `docker` group
- `lazuli` previously had a personal `temps` alias; this has been replaced by a shared `/usr/local/bin/temps` script
- Both accounts can use `temps`

## Common Commands

SSH examples:

```bash
ssh orangepi@192.168.50.71
ssh lazuli@192.168.50.71
```

Temperature command:

```bash
temps
```

Check Docker:

```bash
docker --version
docker ps
docker info
```

## MagicMirror Access

- Main URL:
  - `http://192.168.50.71:8080`
- Remote control UI:
  - `http://192.168.50.71:8080/remote.html`
- Remote control API key:
  - `2b10fe8cd073a15ea1900508c59d845e`
- API key file on board:
  - `/home/lazuli/MagicMirror/config/remote-control-api-key.txt`
- Service name:
  - `magicmirror.service`
- Local kiosk launcher:
  - `/home/lazuli/bin/start-magicmirror-kiosk.sh`
- Case media folder:
  - `/home/lazuli/MagicMirror/modules/MMM-CaseMedia/public/media`
- Case media module source in repo:
  - `magicmirror-modules/MMM-CaseMedia`
- Shared Unix group for MagicMirror files:
  - `magicmirror`
- Shared users:
  - `lazuli`
  - `orangepi`

## Current Warnings

- Passwords are default/simple and should be rotated before any wider exposure
- The board currently depends on Wi-Fi for active management
- Root storage is SD card, so avoid unnecessary write-heavy services
- `lazuli` now auto-logs into the local XFCE seat for MagicMirror, so prefer `orangepi` or SSH for admin work if XRDP session behavior becomes confusing

## MagicMirror File Sharing

- `orangepi` and `lazuli` are both members of the `magicmirror` group
- `/home/lazuli/MagicMirror` is group-owned by `magicmirror`
- directories under that tree use the setgid bit, so new files and folders inherit the `magicmirror` group
- `/home/lazuli` keeps its normal owner/group, but grants the `magicmirror` group execute-only traversal so `orangepi` can reach the shared MagicMirror path without opening the rest of the home directory
