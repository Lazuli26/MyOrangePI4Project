# AC Control Service

LAN-first AC control stack for the ADINA Onix unit paired through `Smart Life`.

The project now has two operator surfaces:

- a lightweight `FastAPI` API for scripts, assistants, OpenClaw, and direct integrations
- a browser-based smart controller dashboard served by the same backend for LAN access from the Orange Pi

## What It Does

- Runs on Windows for local development and on Ubuntu on the Orange Pi with the same codebase.
- Uses a `mock` backend for safe UI and automation development.
- Uses a `tinytuya` backend for direct local LAN control of the real AC.
- Serves a React web app that loads the current AC state on page load and after each command.
- Stores smart-control settings, sleep profiles, weather snapshots, usage history, and feedback locally in SQLite.
- Uses local time, indoor temperature, weather, forecast, and user feedback to recommend or send automatic AC adjustments.
- Trains a lightweight context-regression predictor from saved comfort samples, then chooses AC mode deterministically from the predicted target and the current room temperature.
- Resolves saved coordinates to an IANA timezone for local-time automation and chart rendering.
- Supports optional LAN presence detection from one or more monitored IP addresses.
- Supports PWA install metadata so the dashboard can be saved to a phone home screen.

## Project Files

- `ac_service.py`
  - FastAPI app, AC routes, smart-controller routes, and frontend static serving.
- `smart_controller.py`
  - Automation engine, projection logic, learning heuristics, and scheduled evaluation loop.
- `smart_store.py`
  - SQLite persistence for settings, sleep profiles, usage, feedback, weather, and smart decisions.
- `smart_weather.py`
  - Open-Meteo integration for current conditions and forecast data.
- `smart_models.py`
  - Shared Pydantic models for the smart-control backend.
- `frontend/`
  - React, TypeScript, Zustand, Tailwind, and Recharts smart-controller web app.
- `gui_app.py`
  - Desktop control panel for manual API testing.
- `launch_server.ps1`
  - Windows launcher that finds the project virtual environment and starts the API.
- `ac-control-service.service`
  - Systemd unit for hosting the API and web app on the Orange Pi.
- `.env.example`
  - Runtime settings, including smart-controller DB and frontend build paths.
- `IMPLEMENTATION-NOTES.md`
  - Confirmed DPS mapping, current smart-controller behavior, and follow-up items.

## Smart Web App

The browser app is designed to add value over the mobile app while still exposing the basic controls cleanly.

### Pages

- `/`
  - Main dashboard with live AC status, manual controls, smart-control summary, projection chart, and recent activity.
- `/insights`
  - Projection and history-focused view for learning trends and hourly averages.
- `/settings`
  - Location, timezone, smart-control behavior, and sleep profile configuration.

### Smart Features

- Loads the current AC status when the page opens.
- Refreshes the status again after manual apply actions and comfort feedback.
- Supports a global smart-control on or off toggle.
- Uses current local time, current indoor temperature, current weather, and forecast high or low.
- Learns from manual usage and `Too cold` or `Too hot` comfort feedback.
- Keeps a configurable learning-memory window so older comfort samples can be ignored.
- Lets you clear predictor memory from Settings when you want to retrain from scratch.
- Supports sleep profiles by time range with target temperature and optional fan speed.
- Keeps automation from powering the AC on unless `Allow automation to power the AC on` is enabled.
- Shows a time-of-day projection chart where:
  - the past reflects learned hourly averages
  - the future reflects current predictions
  - line color communicates the AC mode
- Applies safeguards like minimum cycle time, quiet hours, and step limits to reduce unnecessary changes.

### Useful Measurable Inputs

The current implementation uses or stores:

- indoor temperature reported by the AC
- current target temperature
- current mode and fan speed
- local time and timezone
- outside temperature and apparent temperature
- forecast high and low
- humidity and wind speed when weather data is available
- manual adjustments and comfort feedback history
- predictor training samples with environmental context and preferred target temperature
- optional LAN presence reachability state

Potential future signals that could be worth adding later:

- room occupancy
- door or window open state
- power consumption if the AC or plug can expose it
- sunlight or brightness near the room
- season and day-of-week context if the current weather-first model later proves too coarse

## Quick Start On This PC

1. Create a virtual environment:

```powershell
cd "E:\OrangePi project\ac-control-service"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install backend dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy the sample env file:

```powershell
Copy-Item .env.example .env
```

4. Install frontend dependencies and build the web app:

```powershell
cd frontend
npm install
npm run build
cd ..
```

5. Start the API:

```powershell
$env:AC_BACKEND="mock"
$env:AC_API_TOKEN="change-me"
uvicorn run:app --host 127.0.0.1 --port 8008 --reload
```

Or use the Windows launcher:

```powershell
.\launch_server.ps1
```

6. Open the local interfaces:

- Dashboard: `http://127.0.0.1:8008/`
- Insights: `http://127.0.0.1:8008/insights`
- Settings: `http://127.0.0.1:8008/settings`
- OpenAPI docs: `http://127.0.0.1:8008/docs`

7. Optional: start the desktop control panel in a second terminal:

```powershell
python .\gui_app.py
```

## Orange Pi Deployment

Deploy to the board-hosted service:

```bash
cd /home/orangepi/ac-control-service
. .venv/bin/activate
pip install -r requirements.txt
cd frontend
npm install
npm run build
cd ..
sudo systemctl restart ac-control-service
```

Expected LAN URLs:

- Dashboard: `http://192.168.50.71:8008/`
- Insights: `http://192.168.50.71:8008/insights`
- Settings: `http://192.168.50.71:8008/settings`
- Health: `http://192.168.50.71:8008/health`
- OpenAPI docs: `http://192.168.50.71:8008/docs`

## Configuration

Important `.env` values:

```env
AC_BACKEND=mock
AC_BIND_HOST=127.0.0.1
AC_BIND_PORT=8008
AC_API_TOKEN=change-me
SMART_DB_PATH=
FRONTEND_DIST_PATH=
```

Notes:

- Leave `SMART_DB_PATH` empty to use the default local SQLite file `smart_controller.db`.
- Leave `FRONTEND_DIST_PATH` empty to use `frontend/dist`.
- The web app still works with `AC_BACKEND=mock`, which is useful for UI or automation testing before touching the real AC.
- The first practical setup step in the smart UI is entering the location and timezone so weather-backed automation has meaningful data.

## API Surface

### Core AC Routes

- `GET /health`
- `GET /ac/status`
- `POST /ac/power`
- `POST /ac/mode`
- `POST /ac/temperature`
- `POST /ac/fan`
- `POST /ac/sleep`
- `POST /ac/uvc`
- `POST /ac/display`
- `POST /ac/swing/horizontal`
- `POST /ac/swing/vertical`
- `POST /ac/apply`
- `POST /ac/apply-batch`

All `/ac/*` routes except `/health` require the `X-API-Token` header.

### Smart-Control Routes

- `GET /api/dashboard`
  - Aggregated response for the main UI: AC status, smart state, weather, projections, activity, and sleep profiles.
- `POST /api/manual/apply`
  - Applies grouped manual control changes and records the usage event.
- `POST /api/manual/feedback`
  - Handles `too_cold` or `too_hot`, sends an immediate correction, and records learning data.
- `GET /api/smart-control`
  - Reads current automation state and explanation.
- `POST /api/smart-control`
  - Updates automation parameters like enabled state, cycle interval, step limit, learning rate, and quiet hours.
- `POST /api/smart-control/evaluate`
  - Forces an immediate smart evaluation pass.
- `GET /api/projections/day`
  - Returns projection and hourly-average series used by the charts.
- `GET /api/sleep-profiles`
- `POST /api/sleep-profiles`
- `DELETE /api/sleep-profiles/{profile_id}`
- `GET /api/settings`
- `POST /api/settings`
- `POST /api/settings/clear-learning-memory`

## Example Requests

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

Apply a grouped AC change:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8008/ac/apply-batch" `
  -Headers @{ "X-API-Token" = "change-me" } `
  -ContentType "application/json" `
  -Body '{"power":true,"mode":"cool","target_temp_c":24,"fan_speed":"auto","display":false}'
```

Fetch the smart dashboard payload:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8008/api/dashboard"
```

Send comfort feedback:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8008/api/manual/feedback" `
  -ContentType "application/json" `
  -Body '{"direction":"too_hot","note":"midday sun on the room"}'
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
- The GUI apply buttons use `/ac/apply-batch` so grouped changes can reach the AC in one device write when multi-DPS updates are accepted.
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

## Frontend Development

Local frontend workflow:

```powershell
cd frontend
npm run dev
```

Useful scripts:

- `npm run dev`
- `npm run build`
- `npm run check`
- `npm run lint`
- `npm run test`

The Vite dev server proxies `/api`, `/ac`, and `/health` to the local FastAPI backend.

## Orange Pi Deployment

The hosted setup on the board serves both the API and the smart web app from the same `uvicorn` process.

1. Copy the `ac-control-service` folder to `/home/orangepi/ac-control-service`.
2. On the Orange Pi:

```bash
cd /home/orangepi/ac-control-service
sudo apt-get install -y python3.10-venv
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cd frontend
npm install
npm run build
cd ..
sudo cp ac-control-service.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ac-control-service
```

Expected LAN endpoints after deployment:

- `http://192.168.50.71:8008/`
- `http://192.168.50.71:8008/insights`
- `http://192.168.50.71:8008/settings`
- `http://192.168.50.71:8008/health`
- `http://192.168.50.71:8008/docs`

## Current Backend Modes

### `mock`

- Works right now.
- Stores AC state in memory.
- Lets you build and test callers before touching the real unit.
- Supports the smart-controller UI and automation loop for development.

### `tinytuya`

- Provides local Tuya control over the LAN.
- The current ADINA Onix / Smart Life unit has confirmed core mapping:
  - power: `1`
  - target temp: `2`
  - current temp: `3`
  - mode: `4`
  - fan speed: `5`
  - UVC: `11`
  - sleep: `25`
  - vertical swing: `31`
  - horizontal swing: `33`
  - display: `36`
  - fault: `108`
- The public API intentionally applies conservative app-observed limits for this unit:
  - modes exposed: `auto`, `cool`, `dry`, `fan`
  - target temperature range: `16..32 C`
  - vertical swing exposed as `fixed` or `swing`
- Those limits are based on current Smart Life app behavior and are pending further testing.

Common values needed in `.env`:

- `TUYA_DEVICE_ID`
- `TUYA_DEVICE_IP`
- `TUYA_LOCAL_KEY`
- `TUYA_DEVICE_VERSION`

## Local-First Workflow

If the AC is already in `Smart Life` and everything is on the same LAN, this is the recommended order:

1. Find the device on the LAN with `discover_tuya.py`.
2. Fill `.env` with the real Tuya identifiers.
3. Probe the device with `probe_tuya_dps.py`.
4. Toggle settings in `Smart Life` and probe again.
5. Use the changed DPS values to finish or validate the local adapter behavior.

### Discover local Tuya devices

```powershell
python .\discover_tuya.py
python .\discover_tuya.py --raw
```

### Probe a specific device

```powershell
python .\probe_tuya_dps.py `
  --device-id "your-device-id" `
  --ip "192.168.x.x" `
  --local-key "your-local-key" `
  --version "3.3"
```

Or, after filling `.env`:

```powershell
python .\probe_tuya_dps.py
```

### Switch the API to local control

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
TUYA_UVC_DPID=11
TUYA_SLEEP_DPID=25
TUYA_VERTICAL_SWING_DPID=31
TUYA_HORIZONTAL_SWING_DPID=33
TUYA_DISPLAY_DPID=36
TUYA_FAULT_DPID=108
```

Then restart the API and test:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8008/ac/status" `
  -Headers @{ "X-API-Token" = "change-me" }
```

## Project Notes

See [IMPLEMENTATION-NOTES.md](file:///E:/OrangePi%20project/ac-control-service/IMPLEMENTATION-NOTES.md) for the current device mapping, smart-controller details, and pending follow-up tests.
