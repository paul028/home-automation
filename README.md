# Home Automation Dashboard

A self-hosted dashboard to monitor and control IoT devices at home. Currently supports **Tapo CCTV cameras** with live streaming, PTZ controls, and recording playback.

## Supported Devices

| Device | Status | Features |
|--------|--------|----------|
| Tapo C220 | Supported | Live stream, PTZ, recordings |
| Tapo C520WS | Supported | Live stream, PTZ, recordings |
| LG Air Purifier | Planned | — |
| TCL Aircon | Planned | — |
| TCL TV | Planned | — |

## Architecture

```
Tapo Camera (RTSP/ONVIF)
        │
   go2rtc (Docker)            ← RTSP → MSE/WebRTC gateway (no transcoding)
        │
   FastAPI Backend             ← Camera CRUD, PTZ (ONVIF), recordings (pytapo)
        │
   React Frontend              ← Dashboard, live player, PTZ d-pad
        │
     Browser
```

- **Backend**: Python FastAPI following SOLID design principles
- **Frontend**: React + TypeScript + TailwindCSS following MVC pattern
- **Streaming**: go2rtc converts RTSP to WebRTC/MSE (~0.5s latency, no transcoding)
- **PTZ**: ONVIF RelativeMove for discrete micro-movements per click
- **Database**: SQLite via async SQLAlchemy
- **Connection pooling**: Cached device sessions (10-min TTL) with suspension detection to prevent camera lockouts

## Prerequisites

- [pyenv](https://github.com/pyenv/pyenv) with Python 3.11.5
- [Node.js](https://nodejs.org/) (v18+)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

## Setup

### Backend

```bash
cd backend
pyenv local 3.11.5
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Running

Start all three services in separate terminals:

```bash
# Terminal 1 — Streaming gateway (port 1984)
docker compose up go2rtc

# Terminal 2 — Backend (port 8000)
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload

# Terminal 3 — Frontend (port 5173)
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

## Usage

1. Click **Add Camera** on the dashboard
2. Enter camera name, IP address, and camera account credentials
3. Optionally set a **location** to group cameras (e.g. "Living Room", "Front Yard")
4. Check **Has PTZ** for pan/tilt cameras (e.g. C220, C520WS)
5. Click the camera card to open the live stream view
6. Use the PTZ d-pad to control the camera (one click = one micro-movement)
7. Use the recordings panel to browse SD card footage by date

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cameras` | List all cameras |
| POST | `/api/cameras` | Add a camera |
| GET | `/api/cameras/{id}` | Get camera details |
| PUT | `/api/cameras/{id}` | Update a camera |
| DELETE | `/api/cameras/{id}` | Remove a camera |
| GET | `/api/cameras/locations` | List distinct locations |
| POST | `/api/cameras/{id}/ptz` | PTZ control (`direction`: up/down/left/right) |
| GET | `/api/cameras/{id}/presets` | Get PTZ presets |
| GET | `/api/streams/{id}` | Get stream URLs (registers with go2rtc) |
| GET | `/api/streams` | List active go2rtc streams |
| GET | `/api/recordings/{id}?recording_date=YYYY-MM-DD` | Get recordings for a date |
| GET | `/api/recordings/{id}/days?year=YYYY&month=MM` | Get days with recordings |
| GET | `/health` | Health check |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Settings (pydantic-settings)
│   │   ├── database.py              # SQLite + async SQLAlchemy
│   │   ├── api/
│   │   │   ├── routes/              # REST endpoints (cameras, streams, recordings)
│   │   │   └── dependencies.py      # Dependency injection
│   │   ├── core/
│   │   │   ├── interfaces/          # SOLID ABCs (IDevice, IStreamable, IControllable, IRecordable)
│   │   │   └── exceptions.py        # Custom exceptions
│   │   ├── services/
│   │   │   ├── camera_service.py    # Camera CRUD
│   │   │   ├── stream_service.py    # go2rtc stream registration
│   │   │   ├── recording_service.py # SD card recording retrieval
│   │   │   └── device_pool.py       # Connection pooling (DevicePool + PTZPool)
│   │   ├── devices/tapo/
│   │   │   ├── tapo_client.py       # pytapo wrapper
│   │   │   ├── tapo_camera.py       # Full device implementation
│   │   │   └── onvif_ptz.py         # ONVIF PTZ control (RelativeMove)
│   │   └── models/
│   │       ├── camera.py            # SQLAlchemy ORM model
│   │       └── schemas.py           # Pydantic request/response schemas
│   ├── requirements.txt
│   └── .python-version              # pyenv 3.11.5
├── frontend/
│   ├── src/
│   │   ├── models/                  # MVC — TypeScript interfaces
│   │   ├── controllers/             # MVC — React hooks (business logic)
│   │   ├── views/
│   │   │   ├── pages/               # Dashboard, CameraDetail, Settings
│   │   │   ├── components/          # CameraCard, LivePlayer, PTZControls, etc.
│   │   │   └── layouts/             # DashboardLayout
│   │   └── services/api.ts          # Axios HTTP client
│   └── vite.config.ts               # Dev proxy to backend
├── docker-compose.yml               # go2rtc container
└── go2rtc.yaml                      # go2rtc stream config
```

## Environment Variables

Create `backend/.env` to override defaults:

```env
DATABASE_URL=sqlite+aiosqlite:///./home_automation.db
GO2RTC_URL=http://localhost:1984
CORS_ORIGINS=["http://localhost:5173"]
```

## Notes

- **Camera credentials**: Use the camera's local account (set in the Tapo app under "Camera Account"), not your Tapo cloud account. These credentials are shared for RTSP and ONVIF.
- **PTZ step size**: Each click sends an ONVIF RelativeMove. Adjust `STEP_SIZE` in `backend/app/devices/tapo/onvif_ptz.py` to change sensitivity (default: 0.05).
- **Anti-brute-force**: Tapo cameras suspend access after too many rapid auth attempts (~30 min lockout). The backend pools connections and caches suspension timers to avoid this.
- **go2rtc streams**: Auto-registered when a camera is added via the API. Can also be pre-configured in `go2rtc.yaml`.
- **Location grouping**: Cameras can be assigned to a location for visual grouping on the dashboard. Cameras without a location appear under "Ungrouped".
