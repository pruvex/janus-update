# Janus Backlog Dashboard - Fully Standalone Desktop App

A completely standalone desktop application for viewing the Janus Backlog with local data storage.

## Architecture

**FULLY OFFLINE**: This dashboard is 100% standalone with NO external dependencies.

- **Location**: `C:\KI\Janus-Projekt\janus-dashboard\`
- **Data Flow**: Electron → Local API (Fastify) → Local JSON Snapshot
- **No Integration**: Does NOT touch backend/, frontend/, electron/, or any Janus configuration files
- **No Network**: Does NOT require Janus backend or any external server

## Tech Stack

- **Desktop Shell**: Electron (window management only)
- **Local API**: Fastify (reads from local JSON snapshot)
- **Frontend**: React + TypeScript + Vite
- **Styling**: TailwindCSS v3 + shadcn/ui
- **Icons**: Lucide React

## Project Structure

```
janus-dashboard/
├── apps/
│   ├── desktop/        # Electron Shell
│   ├── api/            # Local API (Fastify)
│   └── ui/             # React Frontend (Vite)
├── data/
│   └── backlog.snapshot.json   # Single source of truth
├── shared/
│   ├── types/          # Shared TypeScript types
│   └── utils/
├── scripts/
│   └── start-all.ts    # Orchestrator
└── start-dashboard.bat # Double-click start
```

## How to Start

### Double-Click Start (Recommended)

Simply double-click `start-dashboard.bat` to start the entire application.

### Manual Start

**Terminal 1 - Start Local API**:
```bash
cd apps/api
npm run dev
```

**Terminal 2 - Start UI**:
```bash
cd apps/ui
npm run dev
```

**Terminal 3 - Start Electron**:
```bash
cd apps/desktop
npm start
```

### Using Orchestrator

```bash
npm run dev
```

This starts all three components in parallel.

## Data Source

The dashboard uses a local JSON file as the single source of truth:

```
data/backlog.snapshot.json
```

The local API reads directly from this file - NO external dependencies.

## API Contract

The local API runs on `http://127.0.0.1:3001` and serves data from the local snapshot:

```
GET /api/backlog/items
```

Response:
```json
{
  "source": "local",
  "items": [...],
  "counts": {...}
}
```

## Views

1. **Active View**: Items with status != DONE
2. **History View**: Items with status == DONE
3. **KPI View**: Metrics and statistics
4. **Routing Health**: Items requiring routing attention

## Validation Checklist

- ✅ Dashboard is completely standalone in `janus-dashboard/` folder
- ✅ No changes to existing Janus files (backend/, frontend/, electron/)
- ✅ Uses TailwindCSS v3 (not v4)
- ✅ Uses postcss.config.cjs (not .js) for ESM compatibility
- ✅ Local API layer (Fastify) reads from local JSON snapshot
- ✅ Electron shell for desktop window
- ✅ React UI with modern styling
- ✅ Double-click start capability
- ✅ Strict separation: Electron → Local API → Local JSON
- ✅ NO external dependencies or network requirements
- ✅ Fully offline-capable

## Important Notes

- **The dashboard is fully offline and requires NO external dependencies**
- The local API reads directly from the local JSON snapshot
- The dashboard is READ-ONLY and does not modify any data
- To update the dashboard data, edit `data/backlog.snapshot.json` manually
