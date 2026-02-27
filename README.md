# Home Automation Dashboard

A self-hosted dashboard to monitor and control IoT devices at home. Currently supports **Tapo CCTV cameras** with live streaming, PTZ controls, and recording playback.

## Supported Devices

| Device | Status | Features |
|--------|--------|----------|
| Tapo C220 | Supported | Live stream, PTZ, recordings |
| Tapo C520WS | Supported | Live stream, recordings |
| LG Air Purifier | Planned | — |
| TCL Aircon | Planned | — |
| TCL TV | Planned | — |

## Architecture

```
Tapo Camera (RTSP) ──► go2rtc (Docker) ──► Browser (WebRTC/MSE)
                                               ▲
FastAPI Backend ── Camera CRUD ────────────────┘
               ── PTZ Control
               ── Recordings (pytapo)
```

- **Backend**: Python FastAPI following SOLID design principles
- **Frontend**: React + TypeScript + TailwindCSS following MVC pattern
- **Streaming**: go2rtc converts RTSP to WebRTC/MSE (~0.5s latency, no transcoding)
- **Database**: SQLite via async SQLAlchemy

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
# Terminal 1 — Backend (port 8000)
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 — Frontend (port 5173)
cd frontend
npm run dev

# Terminal 3 — Streaming gateway (port 1984)
docker compose up go2rtc
```

Open **http://localhost:5173** in your browser.

## Usage

1. Click **Add Camera** on the dashboard
2. Enter camera name, IP address, and Tapo credentials
3. Check **Has PTZ** for pan/tilt cameras (e.g. C220)
4. Click the camera card to open the live stream view
5. Use the PTZ d-pad to control the camera
6. Use the recordings panel to browse SD card footage by date

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cameras` | List all cameras |
| POST | `/api/cameras` | Add a camera |
| GET | `/api/cameras/{id}` | Get camera details |
| PUT | `/api/cameras/{id}` | Update a camera |
| DELETE | `/api/cameras/{id}` | Remove a camera |
| POST | `/api/cameras/{id}/ptz` | PTZ control (`direction`: up/down/left/right) |
| GET | `/api/cameras/{id}/presets` | Get PTZ presets |
| GET | `/api/streams/{id}` | Get stream URLs (registers with go2rtc) |
| GET | `/api/recordings/{id}?recording_date=YYYY-MM-DD` | Get recordings for a date |
| GET | `/api/recordings/{id}/days?year=YYYY&month=MM` | Get days with recordings |
| GET | `/api/health` | Health check |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Settings (pydantic-settings)
│   │   ├── database.py              # SQLite + async SQLAlchemy
│   │   ├── api/routes/              # REST endpoints
│   │   ├── core/interfaces/         # SOLID ABCs (IDevice, IStreamable, IControllable, IRecordable)
│   │   ├── services/                # Business logic
│   │   ├── devices/tapo/            # Tapo camera implementation
│   │   └── models/                  # ORM models + Pydantic schemas
│   ├── requirements.txt
│   └── .python-version              # pyenv 3.11.5
├── frontend/
│   ├── src/
│   │   ├── models/                  # MVC — TypeScript interfaces
│   │   ├── controllers/             # MVC — React hooks (business logic)
│   │   ├── views/                   # MVC — React components
│   │   └── services/api.ts          # Axios HTTP client
│   └── vite.config.ts               # Dev proxy to backend
├── docker-compose.yml               # go2rtc streaming gateway
└── go2rtc.yaml                      # go2rtc config
```

## Environment Variables

Create `backend/.env` to override defaults:

```env
DATABASE_URL=sqlite+aiosqlite:///./home_automation.db
GO2RTC_URL=http://localhost:1984
CORS_ORIGINS=["http://localhost:5173"]
```
