# Smart AC Controller Frontend

React, TypeScript, Tailwind, Zustand, and Recharts frontend for the LAN-hosted smart AC controller.

## Purpose

- Provides the main dashboard for live AC status and manual controls.
- Exposes the smart-control summary, automation toggle, and comfort feedback actions.
- Visualizes learned hourly averages and future projections.
- Lets the user configure location, timezone, quiet hours, learning rate, and sleep profiles.

## Routes

- `/`
  - Dashboard
- `/insights`
  - Projection and learning view
- `/settings`
  - Configuration and sleep profiles

## Local Development

From `E:\OrangePi project\ac-control-service\frontend`:

```powershell
npm install
npm run dev
```

The Vite dev server proxies backend calls to `http://127.0.0.1:8008` for:

- `/api`
- `/ac`
- `/health`

## Build

Create the production build served by FastAPI:

```powershell
npm run build
```

The backend expects the built assets in `frontend/dist` unless `FRONTEND_DIST_PATH` overrides it.

## Useful Scripts

- `npm run dev`
- `npm run build`
- `npm run check`
- `npm run lint`
- `npm run test`

## Key Frontend Areas

- `src/pages`
  - page-level routes for dashboard, insights, and settings
- `src/components`
  - status hero, manual controls, smart controls, activity feed, chart card, and sleep profile editor
- `src/store/useSmartAcStore.ts`
  - Zustand store for dashboard loading and user actions
- `src/utils/api.ts`
  - API client for smart-controller backend routes
- `src/utils/projections.ts`
  - chart-series transformation helpers
