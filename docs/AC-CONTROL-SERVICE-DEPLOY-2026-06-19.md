# AC Control Service Deployment

## Purpose

This note records the Orange Pi deployment model for the `ac-control-service` project, including the smart LAN web app added after the initial API-only deployment.

## Deployment Target

- Hostname: `orangepi4pro`
- IP: `192.168.50.71`
- User used for app files: `orangepi`
- Service model: system-wide `systemd` unit running as user `orangepi`

## Installed Paths

- App folder:
  - `/home/orangepi/ac-control-service`
- Virtual environment:
  - `/home/orangepi/ac-control-service/.venv`
- Service unit:
  - `/etc/systemd/system/ac-control-service.service`
- Default SQLite store:
  - `/home/orangepi/ac-control-service/smart_controller.db`
- Default frontend build:
  - `/home/orangepi/ac-control-service/frontend/dist`

## Additional Packages Installed On The Board

- `python3.10-venv`
- `apscheduler` installed in the project virtual environment

## Runtime Shape

- Server:
  - `uvicorn`
- Bind host:
  - `0.0.0.0`
- Port:
  - `8008`
- Process user:
  - `orangepi`
- Service responsibility:
  - AC API, smart-controller API, and static frontend hosting

## Configuration Notes

- The deployed app uses the project `.env` file inside `/home/orangepi/ac-control-service`.
- The service binds on all interfaces so other devices on the LAN can access both the API and the web dashboard.
- The desktop `tkinter` GUI is not installed as a service; only the web/API backend is hosted on the board.
- If `SMART_DB_PATH` is left blank, the service writes to `smart_controller.db` in the project root.
- If `FRONTEND_DIST_PATH` is left blank, the service expects the built web app at `frontend/dist`.
- The backend now resolves an IANA timezone from saved coordinates when the timezone is left blank or set to `UTC`.
- The frontend includes PWA metadata and a service worker for home-screen installation behavior on supported browsers.

## Smart Web App Deployment Steps

After copying updated source files to the board, rebuild the frontend and restart the service:

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

If the service unit does not exist yet:

```bash
cd /home/orangepi/ac-control-service
sudo cp ac-control-service.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ac-control-service
```

## Expected LAN URLs

- Dashboard:
  - `http://192.168.50.71:8008/`
- Insights:
  - `http://192.168.50.71:8008/insights`
- Settings:
  - `http://192.168.50.71:8008/settings`
- Health:
  - `http://192.168.50.71:8008/health`
- OpenAPI docs:
  - `http://192.168.50.71:8008/docs`

## Validation Checklist

- `systemctl status ac-control-service`
- `curl http://127.0.0.1:8008/health`
- `curl http://192.168.50.71:8008/health`
- `curl http://127.0.0.1:8008/api/settings`
- `curl http://127.0.0.1:8008/api/dashboard`
- `curl -X POST http://127.0.0.1:8008/api/settings/clear-learning-memory`
- open `http://192.168.50.71:8008/` from another LAN device

## Validation Results

Initial API deployment already confirmed:

- `ac-control-service.service` is enabled
- `ac-control-service.service` is active
- `curl http://127.0.0.1:8008/health` returned:
  - `{"status":"ok","backend":"tinytuya"}`
- `http://192.168.50.71:8008/health` is reachable from the LAN

Smart web app validation to perform after the updated build is copied:

- confirmed `frontend/dist/index.html` exists on the board
- confirmed `/api/settings` and `/api/dashboard` return JSON locally on the board
- confirmed `/`, `/insights`, and `/settings` render from another LAN device
- confirmed manual control and comfort feedback refresh the displayed AC status
- confirmed predictor settings and memory-reset controls render in `/settings`
- confirmed the board API reports predictor state including predicted target, sample count, and memory window

## Operational Commands

```bash
sudo systemctl status ac-control-service
sudo systemctl restart ac-control-service
sudo journalctl -u ac-control-service -n 100 --no-pager
ls -la /home/orangepi/ac-control-service/frontend/dist
sqlite3 /home/orangepi/ac-control-service/smart_controller.db ".tables"
```

## Notes

- Root storage is still on SD card, so the deployment stays lightweight:
  - Python virtual environment
  - one `uvicorn` process
  - one small SQLite database
  - no container runtime added for this service
- The same backend now serves both machine-facing API routes and the human-facing LAN dashboard.
- The API remains compatible with the Windows desktop GUI and future OpenClaw or Python callers because they still target the same HTTP interface.
- Predictor training data lives in the same SQLite file as other smart-controller state and can be reset from the Settings page or `POST /api/settings/clear-learning-memory`.
