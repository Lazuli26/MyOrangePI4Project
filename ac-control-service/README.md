# AC Control Service

Lightweight Python API for controlling an AC unit from this PC now and moving the same project to the OrangePi later.

## Why this shape

- Runs on Windows for local testing.
- Runs on Ubuntu on the OrangePi with the same code.
- Starts with a `mock` backend so the API can be tested before the real AC mapping is known.
- Leaves a clean seam for a future `tinytuya` backend once the device identifiers and datapoints are available.
- Exposes a small HTTP API that AI assistants, OpenClaw, scripts, or other apps can call.

## Project files

- `ac_service.py`
  - FastAPI app, request models, config, and adapter backends.
- `run.py`
  - Import target for `uvicorn`.
- `gui_app.py`
  - Desktop control panel for manual testing against the local API.
- `launch_server.ps1`
  - Windows launcher that finds the project virtual environment and starts the API.
- `.env.example`
  - Runtime settings.
- `requirements.txt`
  - Python dependencies.
- `IMPLEMENTATION-NOTES.md`
  - Project log of the confirmed DPS mapping, API decisions, and pending follow-up tests.

## Quick start on this PC

1. Create a virtual environment:

```powershell
cd "E:\OrangePi project\ac-control-service"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy the sample env file:

```powershell
Copy-Item .env.example .env
```

4. Start the API:

```powershell
$env:AC_BACKEND="mock"
$env:AC_API_TOKEN="change-me"
uvicorn run:app --host 127.0.0.1 --port 8008 --reload
```

Or use the Windows launcher:

```powershell
.\launch_server.ps1
```

5. Open the docs:

- `http://127.0.0.1:8008/docs`

6. Optional: start the desktop control panel in a second terminal:

```powershell
python .\gui_app.py
```

## Example requests

Health check:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8008/health"
```

Read AC status:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8008/ac/status" `
  -Headers @{ "X-API-Token" = "change-me" }
```

Set a full state:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8008/ac/apply" `
  -Headers @{ "X-API-Token" = "change-me" } `
  -ContentType "application/json" `
  -Body '{"power":true,"mode":"cool","target_temp_c":24,"fan_speed":"auto"}'
```

## Desktop GUI

The project includes a small `tkinter` control panel for manual testing:

```powershell
python .\gui_app.py
```

Notes:

- The GUI talks to the API, not directly to Tuya.
- By default it targets `http://127.0.0.1:8008`.
- It reads `AC_API_TOKEN` from `.env` if present.
- It intentionally mirrors the current app-observed control surface for this AC:
  - modes: `auto`, `cool`, `dry`, `fan`
  - target temp: `16..32 C`
  - vertical swing: `fixed` or `swing`
- Fan-speed options remain intentionally broader because they are still being explored.

## Windows Launcher

The project includes a PowerShell launcher for Windows:

```powershell
.\launch_server.ps1
```

What it does:

- finds `.venv\Scripts\python.exe` or `venv\Scripts\python.exe`
- reads `AC_BIND_HOST` and `AC_BIND_PORT` from `.env`
- starts `uvicorn` from the project root
- enables `--reload` by default

Useful options:

```powershell
.\launch_server.ps1 -Preview
.\launch_server.ps1 -NoReload
```

## Migration to the OrangePi

The intended migration is just:

1. Copy the `ac-control-service` folder to the board.
2. Create a Python virtual environment there.
3. Install the same `requirements.txt`.
4. Switch configuration from `mock` to the real backend.
5. Run it behind `systemd` or in a small container.

Linux example:

```bash
cd ~/ac-control-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export AC_BACKEND=mock
export AC_API_TOKEN=change-me
uvicorn run:app --host 127.0.0.1 --port 8008
```

## Current backend modes

### `mock`

- Works right now.
- Stores AC state in memory.
- Lets you build and test callers before touching the real unit.

### `tinytuya`

- Intended future backend for local Tuya control.
- Local transport is now wired for the core AC controls.
- For the current ADINA Onix / Smart Life unit, the confirmed core mapping is:
  - power: `1`
  - target temp: `2`
  - current temp: `3`
  - mode: `4`
  - fan speed: `5`
  - fault: `108`
- The public API intentionally applies conservative app-observed limits for this unit:
  - modes exposed: `auto`, `cool`, `dry`, `fan`
  - target temperature range: `16..32 C`
  - vertical swing exposed as `fixed` or `swing`
- Those limits are based on current Smart Life app behavior and are pending further testing.

Common values needed later:

- `TUYA_DEVICE_ID`
- `TUYA_DEVICE_IP`
- `TUYA_LOCAL_KEY`
- `TUYA_DEVICE_VERSION`

## Local-first workflow

If your AC is already in `Smart Life` and everything is on the same LAN, this is the recommended order:

1. Find the device on the LAN with `discover_tuya.py`
2. Fill `.env` with the real Tuya identifiers once you have them
3. Probe the device with `probe_tuya_dps.py`
4. Toggle settings in `Smart Life` and probe again
5. Use the changed DPS values to finish the real adapter

### 1. Discover local Tuya devices

```powershell
python .\discover_tuya.py
```

Raw JSON output:

```powershell
python .\discover_tuya.py --raw
```

### 2. Probe a specific device

After you know the IP, device id, and local key:

```powershell
python .\probe_tuya_dps.py `
  --device-id "your-device-id" `
  --ip "192.168.x.x" `
  --local-key "your-local-key" `
  --version "3.3"
```

Or, after filling `.env`, simply:

```powershell
python .\probe_tuya_dps.py
```

### 3. Compare DPS changes

Useful pattern:

1. Run `probe_tuya_dps.py`
2. Change one thing in `Smart Life`, like power or target temperature
3. Run `probe_tuya_dps.py` again
4. Compare the changed DPS value

That usually reveals which datapoints map to:

- power
- mode
- target temperature
- fan speed
- optional extras like swing or eco mode

### 4. Switch the API to local control

After `.env` is filled with the real key and the probe looks good:

```env
AC_BACKEND=tinytuya
TUYA_DEVICE_ID=your-device-id
TUYA_DEVICE_IP=192.168.x.x
TUYA_LOCAL_KEY=your-local-key
TUYA_DEVICE_VERSION=3.3
TUYA_POWER_DPID=1
TUYA_TARGET_TEMP_DPID=2
TUYA_CURRENT_TEMP_DPID=3
TUYA_MODE_DPID=4
TUYA_FAN_SPEED_DPID=5
TUYA_FAULT_DPID=108
```

Then restart the API and test:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8008/ac/status" `
  -Headers @{ "X-API-Token" = "change-me" }
```

## Good next step

Once the API shape is confirmed on this PC, the next practical task is to identify the AC's Tuya datapoints so the `tinytuya` backend can be completed without changing the API that callers use.

## Project Notes

See [IMPLEMENTATION-NOTES.md](file:///E:/OrangePi%20project/ac-control-service/IMPLEMENTATION-NOTES.md) for the current device mapping, confirmed extras, and the app-observed limitations currently enforced by the API.
