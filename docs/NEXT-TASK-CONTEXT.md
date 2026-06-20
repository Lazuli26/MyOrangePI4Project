# Next Task Context

## Use

Use this file as the quick context primer for any new task in this project.

Suggested workflow:

1. Read `HANDOFF-2026-06-03.md`
2. Read `ACCESS-INTERNAL.md` if the task needs remote login
3. Read `orange-pi-4-pro-system-profile-2026-06-03.md` if the task needs system details
4. Start the new task with a short statement of goal, risk level, and whether changes are allowed on the live board

## Current Baseline

- Board is online at `192.168.50.71`
- Root storage is SD card
- eMMC is not in use yet
- SSH and XRDP are working
- Docker is installed and active
- Docker log rotation has already been configured
- `temps` exists as a shared script at `/usr/local/bin/temps`

## Good Starting Summary

Use something like this in a future session:

```text
Project target: Orange Pi 4 Pro at 192.168.50.71
Current state: Ubuntu Jammy vendor image on SD card, SSH and XRDP working, Docker installed, temps command available, write-reduction tuning already applied
Constraint: prefer low-risk changes until better persistent storage is installed
Task: <insert new task here>
```

## Current Constraints

- Prefer low-write changes where practical because the OS root is on SD card
- Avoid large persistent datasets on the root filesystem
- If Docker workloads are added, treat `/var/lib/docker` as temporary until storage migration
- Keep changes documented in `docs/`

## Good Next Task Categories

- Package/runtime installation for lightweight development
- Network setup and service hardening
- GPIO / CSI / Bluetooth validation
- Docker-based experiments with small, disposable workloads
- Preparation for later storage migration

## Higher-Risk Tasks To Plan Explicitly

- Moving Docker root
- Database deployment on SD-backed root storage
- Continuous logging workloads
- Large AI model caches or build caches
- Full system migration to eMMC or other storage
