# Implementation Notes

This document captures the project state after the first local-control pass for the ADINA Onix AC unit paired through `Smart Life`.

## Current Architecture

- The service exposes a lightweight `FastAPI` HTTP API for scripts, apps, and future assistant integrations.
- The service supports two backends:
  - `mock` for safe local development
  - `tinytuya` for local LAN control against the real AC
- A desktop test harness now exists as `gui_app.py` so the API can be exercised manually without using Swagger or raw PowerShell commands.

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
- The API translates the public values to Tuya values:
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

## Current API Surface

### Core

- `GET /health`
- `GET /ac/status`
- `POST /ac/power`
- `POST /ac/mode`
- `POST /ac/temperature`
- `POST /ac/fan`
- `POST /ac/apply`

### Extras

- `POST /ac/sleep`
- `POST /ac/uvc`
- `POST /ac/display`
- `POST /ac/swing/horizontal`
- `POST /ac/swing/vertical`

## Current GUI Surface

The desktop app in `gui_app.py` provides:

- base URL and token configuration
- status refresh
- power on/off buttons
- mode, target temperature, and fan controls
- toggles for sleep, UVC, display, and horizontal swing
- vertical swing selection as `fixed` or `swing`
- an activity log for quick testing feedback

## Pending Work

- Retest `strong` fan mode carefully and determine whether mode-aware validation should be added.
- Decide whether `mute` should remain only a fan-speed value or also receive a convenience control.
- Check whether timer support exists as local DPS data or is app/cloud-side scheduling only.
- Revisit whether any additional Tuya-only vane positions are useful enough to expose publicly.
- Add stronger capability metadata if future callers need to discover mode- or fan-dependent option availability.
