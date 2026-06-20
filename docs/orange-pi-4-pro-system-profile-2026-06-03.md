# Orange Pi 4 Pro System Profile

## Purpose

This document captures the current observed state of the Orange Pi board at `192.168.50.71` for future troubleshooting, setup planning, and escalation.

Collection date: `2026-06-03`

Collection method:
- Remote read-only inspection over SSH from the local workstation
- Supplemental board-reference notes from Orange Pi public product pages

Scope note:
- The "Observed State" sections below come from the live device.
- The "Vendor / Board Reference" section lists advertised capabilities that were not fully validated during this session.

## Access Summary

- Host/IP: `192.168.50.71`
- Hostname: `orangepi4pro`
- Confirmed access methods:
  - `ssh`
  - `xrdp`
- Known local users on the board:
  - `orangepi`
  - `lazuli`

Security note:
- Passwords are stored separately in `ACCESS-INTERNAL.md` for internal project use.
- Both accounts require a password for `sudo`.

## Observed State

### Board Identity

- Device-tree model output: `sun60iw2`
- Device-tree compatible strings:
  - `xunlong,orangepi-4-pro`
  - `arm,sun60iw2p1`
- Boot overlay prefix: `sun60i-a733`
- Boot DTB: `allwinner/sun60i-a733-orangepi-4-pro.dtb`

Interpretation:
- The running image matches an Orange Pi 4 Pro on the Allwinner A733 family BSP/kernel tree.

### Operating System

- Distribution: `Orange Pi 1.0.6 Jammy`
- Base OS: `Ubuntu 22.04.5 LTS (Jammy Jellyfish)`
- Kernel: `5.15.147-sun60iw2`
- Architecture: `arm64`
- Desktop stack observed:
  - `lightdm`
  - `xfce4`

Observations:
- This is a vendor-customized Orange Pi image, not stock Ubuntu.
- Orange Pi-specific services are enabled, including:
  - `orangepi-firstrun-config.service`
  - `orangepi-hardware-monitor.service`
  - `orangepi-hardware-optimize.service`
  - `orangepi-ramlog.service`
  - `orangepi-zram-config.service`

### CPU and Memory

- CPU topology observed:
  - `2 x Cortex-A76`
  - `6 x Cortex-A55`
- Peak clocks reported by `lscpu`:
  - Cortex-A76 cluster up to about `2002 MHz`
  - Cortex-A55 cluster up to about `1794 MHz`
- Installed RAM observed by the OS: about `5.7 GiB usable`

Interpretation:
- The observed usable RAM aligns with a 6 GB-class device after reserved memory and system overhead.

### Storage

- Root block device: `mmcblk1`
- Root filesystem partition: `mmcblk1p1`
- Root filesystem type: `ext4`
- Root filesystem size: about `57 GiB`
- Root usage at collection time: about `5.4 GiB` used, `51 GiB` available
- Root media type verified later: `SD`
- Card identification observed:
  - name: `SD64G`
  - serial: `0x4d6004c5`
  - manufacturing date: `11/2023`
- Memory-backed storage features:
  - `zram0` swap about `2.9 GiB`
  - `zram1` mounted on `/var/log` about `50 MiB`

Observations:
- The running system is on a microSD card, not eMMC.
- No mounted NVMe SSD was observed during this session.
- Root mount options already include `noatime` and `commit=600`, which reduce write frequency compared with default ext4 settings.
- `/tmp` is mounted as `tmpfs`, and `/var/log` is redirected to zram, both of which reduce SD-card wear.

### SD-Card Wear Assessment

Current state is better than a default Linux-on-SD setup because the image already uses several write-reduction features:
- Root filesystem mounted with `noatime`
- Root filesystem mounted with `commit=600`
- `/tmp` on `tmpfs`
- `/var/log` on `zram`
- `journald` configured with `Storage=volatile`
- Swap on `zram` instead of disk

What still writes to the SD card regularly:
- Docker data under `/var/lib/docker`
- Docker container logs using the `json-file` log driver
- Snap packages and refresh activity under `/var/lib/snapd`
- Package installs, updates, browser profiles, caches, and any database or queue workloads

Interpretation:
- For light desktop use, SSH, occasional package installs, and moderate scripting, the current setup is reasonably protective.
- For long-running containers, databases, AI workloads with caching, browser-heavy use, or continuous logging, SD-card wear becomes a real reliability concern.
- The biggest medium-term risk on this board is not the base OS alone, but high-write application data staying on the SD card.

Mitigation added during this session:
- Docker now has log rotation configured in `/etc/docker/daemon.json`
- Current Docker log limits:
  - `max-size=10m`
  - `max-file=3`

### Networking

- Active network interface: `wlan0`
- Active IPv4 address: `192.168.50.71/24`
- Default route: via `192.168.50.1`
- Active Wi-Fi connection name: `Calero 5G`
- Ethernet interface state: `eth0` present but not connected during collection

Additional observations:
- IPv6 addresses are present on `wlan0`
- The board is currently dependent on Wi-Fi for reachability

### Remote Access and Listening Ports

Confirmed listening ports observed:
- `22/tcp` on all interfaces: SSH
- `3389/tcp`: XRDP
- `3350/tcp` on loopback: XRDP session manager
- `631/tcp` on loopback: CUPS

Remote-access services observed running and enabled:
- `ssh.service`
- `xrdp.service`
- `xrdp-sesman.service`

XRDP note:
- Logs show successful session starts for user `lazuli`
- One XRDP disconnect/error sequence was visible in recent logs, but the service remained up

### Containers and Runtime Tooling

- `containerd.service`: enabled and active
- `docker`: installed and available
- Docker version observed: `29.5.2`
- containerd version observed: `2.2.4`
- User `orangepi` is in the `docker` group
- Docker service state observed: active, but not enabled at boot
- Docker daemon config now exists at `/etc/docker/daemon.json`
- Docker logging remains `json-file`, now with rotation limits for SD-card protection
- No containers were running at validation time
- `/var/lib/docker` usage was negligible at validation time

Interpretation:
- The board is already partially prepared for container-based workloads.
- Docker is present and usable, but persistent container data should still be moved off the SD card if the board will host real services.

### User Accounts and Privilege Model

- `orangepi`
  - UID/GID: `1000`
  - Supplementary groups include:
    - `sudo`
    - `docker`
    - `dialout`
    - `video`
    - `plugdev`
    - `netdev`
    - `bluetooth`
- `lazuli`
  - UID/GID: `1001`
  - Supplementary groups include:
    - `sudo`

Privilege note:
- `sudo` is password-protected for both accounts
- No passwordless sudo was detected

### Services Currently Running

Notable running services at collection time:
- `bluetooth.service`
- `chrony.service`
- `containerd.service`
- `cups.service`
- `lightdm.service`
- `NetworkManager.service`
- `snapd.service`
- `ssh.service`
- `wpa_supplicant.service`
- `xrdp.service`
- `xrdp-sesman.service`

Notable enabled services relevant to future project setup:
- `openvpn.service`
- `dnsmasq.service`
- `smartmontools.service`
- `lm-sensors.service`
- `unattended-upgrades.service`

Escalation note:
- `openvpn` and `dnsmasq` are enabled, which may matter later if the board is repurposed as a gateway, VPN node, AP, or edge appliance.

### Kernel / Driver Clues

Observed kernel modules and identifiers suggest:
- AIC wireless stack present:
  - `aic8800_fdrv`
  - `aic8800_bsp`
  - `aic8800_btlpm`
- Ethernet driver:
  - `sunxi_stmmac`
- Vendor multimedia / accelerator-related modules present:
  - `vipcore`
  - `sunxi_ve`
  - `deinterlace`

Interpretation:
- The image includes vendor BSP drivers for wireless and multimedia/acceleration paths.
- The NPU and media stack may depend on vendor-specific software rather than upstream Linux support.

### Custom Utility Check: `temps`

Original state found during this session:
- `temps` was originally configured only for user `lazuli`
- The definition was stored in `/home/lazuli/.bashrc` as a bash alias
- `orangepi` did not have the alias

Original alias found for `lazuli`:

```bash
alias temps='for z in /sys/class/thermal/thermal_zone*; do printf "%-20s " "$(cat $z/type)"; awk "{printf \"%.1f°C\n\",\$1/1000}" $z/temp; done'
```

Validated behavior before promotion to a script:
- Logging in as `lazuli` and running `temps` worked
- The alias printed all available thermal zones with Celsius values
- Sample observed output:

```text
cpul_thermal_zone    60.3C
cpub_thermal_zone    59.3C
cpul_idle_zone       59.3C
cpub_idle_zone       59.5C
gpu_thermal_zone     58.0C
npu_thermal_zone     58.0C
ddr_thermal_zone     57.6C
skin_zone            35.9C
```

System change applied during this session:
- Installed a shared executable at `/usr/local/bin/temps`
- Removed the `lazuli`-specific alias from `/home/lazuli/.bashrc`
- Verified that both `lazuli` and `orangepi` now resolve `temps` to `/usr/local/bin/temps`

Installed script behavior:
- Iterates over `/sys/class/thermal/thermal_zone*`
- Reads each zone `type` and `temp`
- Prints a simple aligned list with temperatures in Celsius

Validation after installation:
- `lazuli`: `type temps` => `/usr/local/bin/temps`
- `orangepi`: `type temps` => `/usr/local/bin/temps`
- The command works in direct invocation and interactive bash contexts

Escalation note:
- `temps` is now a proper shared command and is suitable for SSH-based support and automation
- Output is live state, so values will vary with workload, ambient temperature, and airflow

## Vendor / Board Reference

Based on Orange Pi public product information, the Orange Pi 4 Pro platform is advertised with:

- Allwinner `A733` SoC
- `2 x Cortex-A76` + `6 x Cortex-A55`
- Up to `3 TOPS` NPU compute
- LPDDR5 memory options up to `16 GB`
- Onboard Wi-Fi 6 and Bluetooth 5.4
- Gigabit Ethernet
- M.2 M-Key PCIe SSD support
- Dual camera support via MIPI CSI
- USB 3 plus USB 2 ports
- HDMI video output
- GPIO expansion header

Validation note:
- Not all advertised hardware capabilities were validated during this session.
- In particular, this session did not test NPU tooling, CSI cameras, GPIO, Bluetooth pairing, Ethernet throughput, HDMI output, or NVMe functionality.

Reference sources:
- Orange Pi 4 Pro product page: <http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-4-Pro.html>
- Orange Pi product index: <http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/index.html>

## Risks, Gaps, and Escalation Notes

- The board is running a vendor BSP kernel (`5.15.147-sun60iw2`), so package compatibility and kernel feature availability may differ from upstream Ubuntu ARM systems.
- Network reachability currently depends on Wi-Fi; if this device becomes infrastructure-critical, Ethernet should be validated and preferably used where practical.
- Default or shared credentials should be rotated before exposing the device beyond a trusted LAN.
- XRDP works, but recent logs show at least one disconnect/error sequence worth revisiting if desktop stability becomes important.
- Container tooling is present, but no project-specific runtime standards are documented yet.
- The root OS is on a microSD card, which is acceptable for light use but is a weaker long-term storage layer for write-heavy services.
- Docker and Snap are currently the most obvious ongoing write sources on the root filesystem.
- Docker log rotation is now capped, but Docker image layers, volumes, and any persistent service data still remain on the SD card.
- No backup, imaging, or rollback baseline was created during this session.

## Recommended Next Baseline Tasks

Before using the board for multiple projects, the next useful setup steps would be:

1. Rotate passwords and decide whether both `orangepi` and `lazuli` should remain active.
2. Decide on the primary management model:
   - desktop-first via XRDP
   - headless/server-first via SSH and Docker
3. Confirm storage strategy:
   - stay on current SD-card root for light use only
   - move write-heavy workloads or root data to NVMe when available
4. Capture a package baseline:
   - `apt-mark showmanual`
   - key project runtimes and versions
5. Reduce SD-card wear before adding serious workloads:
   - move Docker root or persistent app data off the SD card
   - limit container log growth
   - avoid putting databases, queues, or frequent cache directories on the SD card
   - consider disabling Snap packages you do not need
6. Validate board-specific interfaces needed by your future projects:
   - GPIO
   - CSI cameras
   - Bluetooth
   - Docker workloads
   - NPU/media acceleration
7. Create a recovery baseline:
   - system image
   - boot config backup
   - user and service inventory

## Session Change Log

Changes made during this session:
- Added local documentation folder: `docs/`
- Added remote inventory helper script: `docs/collect_profile_remote.sh`
- Performed remote read-only inspection of the board over SSH
- Confirmed that `temps` originally existed only as a `lazuli`-specific alias in `.bashrc`
- Installed a shared `/usr/local/bin/temps` script on the Orange Pi
- Removed the `lazuli` alias so both users now use the script-backed command
- Corrected storage documentation to reflect that root is on SD card rather than eMMC
- Assessed current SD-card wear mitigations and likely write sources
- Confirmed Docker is installed and active on the board
- Added `/etc/docker/daemon.json` with conservative log rotation settings for SD-card protection
- No packages were installed
- Updated `/home/lazuli/.bashrc`
- Added `/usr/local/bin/temps`
- Added `/etc/docker/daemon.json`
- No services were restarted on the Orange Pi

## Quick Snapshot

- Board family: `Orange Pi 4 Pro / Allwinner A733`
- Hostname: `orangepi4pro`
- IP: `192.168.50.71`
- OS: `Orange Pi 1.0.6 Jammy` on `Ubuntu 22.04.5`
- Kernel: `5.15.147-sun60iw2`
- CPU: `2x A76 + 6x A55`
- RAM observed: about `5.7 GiB usable`
- Root storage: about `57 GiB ext4` on SD card `mmcblk1p1`
- Network in use: `wlan0` on `Calero 5G`
- Remote access: `SSH` and `XRDP` active
- Containers: `Docker 29.5.2` and `containerd 2.2.4`, with Docker log rotation configured
- Shared custom command: `temps` at `/usr/local/bin/temps`
