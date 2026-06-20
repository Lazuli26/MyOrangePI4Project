# Orange Pi Documentation

## Files

- `HANDOFF-2026-06-03.md`
  - Operator handoff summary for future sessions and fresh context windows.
- `ACCESS-INTERNAL.md`
  - Internal-only access details including usernames and passwords.
- `NEXT-TASK-CONTEXT.md`
  - Quick context primer to start new tasks with the right baseline.
- `MAGICMIRROR-INSTALL-2026-06-10.md`
  - MagicMirror installation record, boot behavior, local kiosk notes, and validation results.
- `MAGICMIRROR-CASEMEDIA-2026-06-12.md`
  - Custom media background/widget module for local images and videos, with folder path and playback options.
- `NAS-SETUP-2026-06-19.md`
  - NAS setup note for exposing the attached 500 GB USB drive over SMB on the local network.
- `OPENCLAW-INSTALL-2026-06-03.md`
  - OpenClaw installation record for the Orange Pi, including install path and verification commands.
- `XRDP-AUTOLOGIN-CHANGE-2026-06-03.md`
  - Notes for the LightDM autologin change, XRDP rationale, OpenClaw impact, and rollback steps.
- `orange-pi-4-pro-system-profile-2026-06-03.md`
  - Primary handoff document describing the board, OS, active services, network state, users, and escalation notes.
- `collect_profile_remote.sh`
  - Read-only remote inventory script used to gather baseline information over SSH.
- `assess_sd_root_remote.sh`
  - Script used to verify SD-root storage and current write-reduction settings.
- `inspect_docker_remote.sh`
  - Script used to confirm Docker state and daemon configuration.
- `install_temps_remote.sh`
  - Script used to promote `temps` into a shared command.
- `install_magicmirror_remote.sh`
  - Script used to install MagicMirror, enable `lazuli` autologin, and configure Chromium kiosk mode remotely.
- `install_nas_remote.sh`
  - Script used to mount the attached USB drive by UUID and expose it as an authenticated Samba share.
- `apply_rotation_cleanup_remote.sh`
  - Script used to move display rotation out of the kiosk launcher and into boot/X11 config on the Orange Pi.
- `../magicmirror-modules/MMM-CaseMedia`
  - Custom MagicMirror module source for local image/video playback as a background or widget.
- `reduce_sd_writes_remote.sh`
  - Script used to apply conservative Docker log rotation for SD-card protection.

## Notes

- This folder now contains both a full technical profile and a lightweight handoff set.
- Sensitive credentials are intentionally isolated in `ACCESS-INTERNAL.md` for internal use.
- The baseline started as a read-only documentation pass on `2026-06-03`, and later sessions added small documented system changes.
