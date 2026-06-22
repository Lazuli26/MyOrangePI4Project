# Implementation Notes

This document captures the current state of the local-first AC control stack and the smart LAN web app for the ADINA Onix unit paired through `Smart Life`.

## Current Architecture

- The backend is a lightweight `FastAPI` service for manual control, automation, and frontend hosting.
- The service supports two AC backends:
  - `mock` for safe local development
  - `tinytuya` for local LAN control against the real AC
- A browser-based smart controller is served from the same backend once `frontend/dist` exists.
- Smart-controller state is stored locally in SQLite through `smart_store.py`.
- A desktop harness also exists as `gui_app.py` for manual API testing without using the browser.
- A background automation loop runs through `APScheduler` and evaluates smart-control recommendations every minute.
- The frontend is also packaged as a lightweight PWA so it can be saved from a phone browser.

## Confirmed Local Tuya Data

- Device id: `bf5bc489b1e5120bdb329z`
- Local protocol version: `3.3`
- Confirmed LAN IP at discovery time: `192.168.50.25`
- Product category: `kt`
- Product name: `Smart Air Conditioner`

## Confirmed DPS Mapping

- `1` -> power
- `2` -> target temperature
- `3` -> current temperature
- `4` -> mode
- `5` -> fan speed enum
- `11` -> UVC
- `25` -> sleep
- `31` -> vertical swing enum
- `33` -> horizontal swing boolean
- `36` -> display
- `108` -> fault code

## Observed Enum Values

### Mode

- Tuya raw values observed or declared by device spec:
  - `auto`
  - `cold`
  - `wet`
  - `wind`
- The generic Tuya product schema also includes `hot`, but this has not been treated as supported for this unit.
- The API translates public values to Tuya values:
  - `cool` -> `cold`
  - `dry` -> `wet`
  - `fan` -> `wind`

### Fan Speed

- App-observed speeds:
  - `auto`
  - `low`
  - `middle`
  - `high`
  - `strong`
  - `mute`
- `strong` appears to be mode-dependent and should be retested later.
- `mute` is implemented through the same Tuya fan-speed datapoint rather than a separate toggle datapoint.

### Vertical Swing

- Observed raw values:
  - `off`
  - `same`
- Public API mapping:
  - `fixed` -> `off`
  - `swing` -> `same`

### Horizontal Swing

- Boolean value:
  - `false` -> fixed/off
  - `true` -> swing/on

## App-Observed Limits Applied Intentionally

These are conservative limits based on current behavior in the `Smart Life` app. They are not guaranteed hardware limits.

- Exposed public modes:
  - `auto`
  - `cool`
  - `dry`
  - `fan`
- Exposed target temperature range:
  - `16..32 C`
- Exposed vertical swing values:
  - `fixed`
  - `swing`

The broader Tuya schema suggests more possible capabilities, but the public API currently hides them on purpose until they are tested and shown to be useful.

## Smart Controller Design

### Stored Data

The SQLite store tracks:

- app settings
- sleep profiles
- weather snapshots
- manual usage events
- comfort feedback events
- smart decision events
- predictor training events with saved environmental context and preferred target labels

Default runtime paths:

- SQLite DB: `smart_controller.db`
- frontend build: `frontend/dist`

### Current Inputs To Automation

The automation logic currently uses:

- local hour of day and timezone
- current indoor temperature reported by the AC
- current AC mode, fan speed, and target temperature
- current outside temperature and apparent temperature
- forecast high and low
- optional quiet-hours settings
- optional sleep profile overrides
- optional LAN presence state
- IANA timezone resolution from saved coordinates

### Current Predictor

- The smart controller now trains a lightweight context-regression model from saved training samples.
- Manual target changes and `too_cold` or `too_hot` feedback create labeled training samples.
- Each sample stores:
  - local hour
  - indoor temperature
  - outside temperature
  - apparent temperature
  - humidity
  - wind speed
  - forecast high and low
  - home presence state
  - preferred target temperature
- A configurable memory lifetime controls how many days of samples are used for training.
- Existing manual and comfort-feedback history can be bootstrapped into predictor samples when the new model starts with an empty training table.
- The predictor intentionally uses weather and time-of-day, but does not yet include season or day-of-week features.
- Once a preferred target is predicted, the mode decision is deterministic:
  - larger positive room-minus-target deltas lead to `cool`
  - smaller positive deltas lead to `auto`
  - near-target or slightly cool conditions lead to `fan`
  - much cooler-than-target conditions lead to `off`

### Current Safeguards

- minimum cycle interval between automatic commands
- maximum target-temperature step per decision
- quiet-hours suppression for very small changes
- no-op protection when the recommendation already matches live AC state
- optional manual-power-only policy so automation will not turn the AC on
- optional presence-away cutoff so automation keeps the AC off when monitored LAN devices are unreachable

### Comfort Feedback Behavior

- `too_hot`
  - lowers the target temperature by `1 C`
  - powers on and forces `cool` if the AC is currently `off` or in `fan`
- `too_cold`
  - raises the target temperature by `1 C`
  - keeps the AC off if it is already off
- every feedback action is stored and contributes to future hourly bias

### Projection Chart Shape

The chart data returned by the backend is split into:

- `past`
  - learned hourly averages
- `current`
  - present recommendation anchor
- `future`
  - projected hourly target temperatures

Each point carries:

- minutes from midnight
- displayed hour label
- target temperature
- AC mode
- segment classification

## Current API Surface

### Core AC Routes

- `GET /health`
- `GET /ac/status`
- `POST /ac/power`
- `POST /ac/mode`
- `POST /ac/temperature`
- `POST /ac/fan`
- `POST /ac/apply`
- `POST /ac/apply-batch`

### AC Extras

- `POST /ac/sleep`
- `POST /ac/uvc`
- `POST /ac/display`
- `POST /ac/swing/horizontal`
- `POST /ac/swing/vertical`

### Smart Web App Routes

- `GET /api/dashboard`
- `POST /api/manual/apply`
- `POST /api/manual/feedback`
- `GET /api/smart-control`
- `POST /api/smart-control`
- `POST /api/smart-control/evaluate`
- `GET /api/projections/day`
- `GET /api/sleep-profiles`
- `POST /api/sleep-profiles`
- `DELETE /api/sleep-profiles/{profile_id}`
- `GET /api/settings`
- `POST /api/settings`
- `POST /api/settings/clear-learning-memory`

### Frontend Routes

- `GET /`
- `GET /insights`
- `GET /settings`

## Current UI Surfaces

### Desktop GUI

The desktop app in `gui_app.py` provides:

- base URL and token configuration
- status refresh
- power on or off buttons
- mode, target temperature, and fan controls
- toggles for sleep, UVC, display, and horizontal swing
- vertical swing selection as `fixed` or `swing`
- an activity log for quick testing feedback

### Web App

The browser app currently provides:

- live status hero and weather snapshot
- grouped manual controls
- smart-control summary and toggle
- predicted preferred target, predictor sample count, and memory window summary
- comfort feedback actions
- projection chart with mode coloring
- recent activity feed
- settings for location, timezone, cycle behavior, quiet hours, learning rate, predictor memory lifetime, presence detection, and manual power policy
- CRUD for sleep profiles
- a tabbed control surface for manual controls vs automation

## Current Deployment Status

- The Orange Pi deployment has been updated and validated at:
  - `http://192.168.50.71:8008/`
  - `http://192.168.50.71:8008/insights`
  - `http://192.168.50.71:8008/settings`
- The board-hosted API responds for:
  - `GET /health`
  - `GET /api/settings`
  - `GET /api/dashboard`

## Pending Work

- Confirm whether the AC accepts every desired combination through one multi-DPS payload or whether some combinations still force TinyTuya fallback writes.
- Retest `strong` fan mode carefully and determine whether mode-aware validation should be added.
- Consider deeper explainability in the UI for why a specific target and mode were chosen.
- Decide whether `mute` should remain only a fan-speed value or also receive a convenience control.
- Check whether timer support exists as local DPS data or is app-cloud scheduling only.
- Revisit whether any additional Tuya-only vane positions are useful enough to expose publicly.
- Add stronger capability metadata if future callers need to discover mode- or fan-dependent option availability.
