# Home Automation Dashboard

A self-hosted dashboard to monitor and control IoT devices at home. Currently supports **Tapo CCTV cameras** with live streaming (video + audio), PTZ controls, continuous recording with Google Drive backup, and recording playback.

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
   go2rtc (Docker)            ← RTSP → MSE/WebRTC gateway + ffmpeg audio transcoding
        │
   FastAPI Backend             ← Camera CRUD, PTZ, continuous recording, Google Drive upload
        │
   React Frontend              ← Dashboard, live player with audio, PTZ d-pad, recording playback
        │
     Browser
```

- **Backend**: Python FastAPI following SOLID design principles
- **Frontend**: React + TypeScript + TailwindCSS following MVC pattern
- **Streaming**: go2rtc converts RTSP to WebRTC/MSE (~0.5s latency)
- **Audio**: ffmpeg transcodes pcm_alaw (G.711) → AAC for browser compatibility
- **PTZ**: ONVIF RelativeMove for discrete micro-movements per click
- **Database**: SQLite via async SQLAlchemy
- **Recording**: Continuous ffmpeg recording → local segments → Google Drive upload
- **Connection pooling**: Cached device sessions (10-min TTL) with suspension detection

## Prerequisites

### macOS (Apple Silicon / M series)

Install [Homebrew](https://brew.sh/) if you don't have it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Install dependencies:

```bash
# Python version manager
brew install pyenv

# Node.js
brew install node

# Docker
brew install --cask docker

# ffmpeg (required for continuous recording)
brew install ffmpeg
```

Configure pyenv in your shell (`~/.zshrc`):

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc
```

Install Python 3.11.5:

```bash
pyenv install 3.11.5
```

### Ubuntu

```bash
# System dependencies for pyenv
sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
  libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils \
  tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev git

# pyenv
curl https://pyenv.run | bash
```

Add to `~/.bashrc`:

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc
```

Install Python, Node.js, Docker, and ffmpeg:

```bash
# Python
pyenv install 3.11.5

# Node.js (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Docker Engine
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to the docker group (log out and back in after)
sudo usermod -aG docker $USER

# ffmpeg
sudo apt install -y ffmpeg
```

### Windows

> **Recommended**: Use [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) with Ubuntu and follow the Ubuntu instructions above. The rest of this section covers native Windows setup.

1. **Python** — Install [pyenv-win](https://github.com/pyenv-win/pyenv-win):

```powershell
# PowerShell (run as Administrator)
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

Then install Python:

```powershell
pyenv install 3.11.5
```

2. **Node.js** — Download the LTS installer from [nodejs.org](https://nodejs.org/) or use winget:

```powershell
winget install OpenJS.NodeJS.LTS
```

3. **Docker** — Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/). Ensure WSL2 backend is enabled in Docker Desktop settings.

4. **ffmpeg** — Install via winget or [chocolatey](https://chocolatey.org/):

```powershell
winget install Gyan.FFmpeg
# or
choco install ffmpeg
```

5. **Git** (if not already installed):

```powershell
winget install Git.Git
```

## Setup

### Clone the repository

```bash
git clone <repository-url>
cd home-automation
```

### Backend

**macOS / Ubuntu:**

```bash
cd backend
pyenv local 3.11.5
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**

```powershell
cd backend
pyenv local 3.11.5
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

### Environment configuration

Create `backend/.env`:

```env
# Core
DATABASE_URL=sqlite+aiosqlite:///./home_automation.db
GO2RTC_URL=http://localhost:1984
CORS_ORIGINS=["http://localhost:5173"]

# Continuous Recording (optional)
RECORDING_ENABLED=false
RECORDINGS_LOCAL_PATH=/tmp/ha-recordings
RECORDING_SEGMENT_SECONDS=300
RECORDING_RETENTION_DAYS=30

# Google Drive Upload (optional, requires RECORDING_ENABLED=true)
GDRIVE_CREDENTIALS_PATH=
GDRIVE_FOLDER_ID=
```

> On Windows, change `RECORDINGS_LOCAL_PATH` to a Windows path like `C:\temp\ha-recordings`.

## Google Drive Setup (Optional)

To enable cloud backup of recordings:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Google Drive API** under APIs & Services
4. Create **OAuth 2.0 Client ID** credentials (Desktop application type)
5. Download the client secrets JSON file and place it in the `backend/` directory
6. Create a folder in Google Drive where recordings will be stored — copy its folder ID from the URL (`https://drive.google.com/drive/folders/<FOLDER_ID>`)
7. Update `backend/.env`:

```env
RECORDING_ENABLED=true
GDRIVE_CREDENTIALS_PATH=./credentials.json
GDRIVE_FOLDER_ID=<your-folder-id>
```

8. On first run, the backend will open a browser window for OAuth consent. Grant access and a `token.json` will be saved automatically for future runs.

## Running

Start all three services:

**macOS / Ubuntu** — open three separate terminals:

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

**Windows (PowerShell)** — open three separate terminals:

```powershell
# Terminal 1 — Streaming gateway (port 1984)
docker compose up go2rtc

# Terminal 2 — Backend (port 8000)
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Terminal 3 — Frontend (port 5173)
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

## Testing

The backend has a comprehensive unit test suite using **pytest** with async support. Tests are fully isolated using in-memory SQLite and mocks — no running services required.

```bash
cd backend
source .venv/bin/activate    # Windows: .venv\Scripts\Activate.ps1
python -m pytest
```

Run with verbose output:

```bash
python -m pytest -v
```

Run a specific test file:

```bash
python -m pytest tests/services/test_camera_service.py -v
```

### Test structure

```
tests/
├── conftest.py                      # Shared fixtures (in-memory DB, camera factory)
├── api/
│   ├── test_cameras_route.py        # Camera endpoints (CRUD, PTZ, error handling)
│   ├── test_streams_route.py        # Stream info and listing endpoints
│   └── test_recordings_route.py     # Recording playback, Range header parsing
├── services/
│   ├── test_camera_service.py       # Camera CRUD operations
│   ├── test_stream_service.py       # go2rtc registration and URL generation
│   ├── test_recording_service.py    # Google Drive recording retrieval
│   ├── test_recording_manager.py    # ffmpeg lifecycle, upload, folder caching
│   ├── test_gdrive_service.py       # Google Drive API wrapper
│   └── test_device_pool.py         # Connection pooling, TTL, suspension
└── devices/
    ├── test_tapo_camera.py          # TapoCamera (all 4 SOLID interfaces)
    ├── test_tapo_client.py          # pytapo wrapper (connect, auth, RTSP URLs)
    └── test_onvif_ptz.py            # ONVIF PTZ (move, stop, direction map)
```

## Usage

1. Click **Add Camera** on the dashboard
2. Enter camera name, IP address, and camera account credentials
3. Optionally set a **location** to group cameras (e.g. "Living Room", "Front Yard")
4. Check **Has PTZ** for pan/tilt cameras (e.g. C220, C520WS)
5. Check **Has Recording** to include the camera in continuous recording
6. Click the camera card to open the live stream view
7. Use the speaker icon to unmute and hear live audio from the camera
8. Use the PTZ d-pad to control the camera (one click = one micro-movement)
9. Use the recordings panel to browse footage by date
10. Click **Review** on a segment to play it back — segments auto-advance through the day
11. Configure cameras via the **Settings** page (IP, credentials, location, PTZ, recording)

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
| GET | `/api/recordings/play/{file_id}` | Stream recording from Google Drive (supports Range) |
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
│   │   │   ├── stream_service.py    # go2rtc stream registration + audio transcoding
│   │   │   ├── recording_service.py # Recording retrieval from Google Drive
│   │   │   ├── recording_manager.py # Continuous recording (ffmpeg + upload + cleanup)
│   │   │   ├── gdrive_service.py    # Google Drive API wrapper
│   │   │   └── device_pool.py       # Connection pooling (DevicePool + PTZPool)
│   │   ├── devices/tapo/
│   │   │   ├── tapo_client.py       # pytapo wrapper
│   │   │   ├── tapo_camera.py       # Full device implementation
│   │   │   └── onvif_ptz.py         # ONVIF PTZ control (RelativeMove)
│   │   └── models/
│   │       ├── camera.py            # SQLAlchemy ORM model
│   │       └── schemas.py           # Pydantic request/response schemas
│   ├── requirements.txt
│   ├── pytest.ini                   # pytest configuration
│   ├── tests/                       # Unit tests (139 tests, pytest + pytest-asyncio)
│   └── .python-version              # pyenv 3.11.5
├── frontend/
│   ├── src/
│   │   ├── models/                  # MVC — TypeScript interfaces
│   │   ├── controllers/             # MVC — React hooks (business logic)
│   │   ├── views/
│   │   │   ├── pages/               # Dashboard, CameraDetail, Settings
│   │   │   ├── components/          # CameraCard, LivePlayer, PTZControls, RecordingPlayer
│   │   │   └── layouts/             # DashboardLayout
│   │   └── services/api.ts          # Axios HTTP client
│   └── vite.config.ts               # Dev proxy to backend
├── docker-compose.yml               # go2rtc container
└── go2rtc.yaml                      # go2rtc stream config (with ffmpeg audio transcoding)
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./home_automation.db` | Database connection string |
| `GO2RTC_URL` | `http://localhost:1984` | go2rtc API URL |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `RECORDING_ENABLED` | `false` | Enable continuous recording |
| `RECORDINGS_LOCAL_PATH` | `/tmp/ha-recordings` | Local directory for ffmpeg segments |
| `RECORDING_SEGMENT_SECONDS` | `300` | Segment duration in seconds (5 min) |
| `RECORDING_RETENTION_DAYS` | `30` | Days to keep recordings on Google Drive |
| `GDRIVE_CREDENTIALS_PATH` | — | Path to Google OAuth client secrets JSON |
| `GDRIVE_FOLDER_ID` | — | Google Drive root folder ID for recordings |

## Notes

- **Camera credentials**: Use the camera's local account (set in the Tapo app under "Camera Account"), not your Tapo cloud account. These credentials are shared for RTSP and ONVIF.
- **PTZ step size**: Each click sends an ONVIF RelativeMove. Adjust `STEP_SIZE` in `backend/app/devices/tapo/onvif_ptz.py` to change sensitivity (default: 0.05).
- **Anti-brute-force**: Tapo cameras suspend access after too many rapid auth attempts (~30 min lockout). The backend pools connections and caches suspension timers to avoid this.
- **go2rtc streams**: Auto-registered when a camera is added via the API. Can also be pre-configured in `go2rtc.yaml`.
- **Audio**: Tapo cameras output pcm_alaw (G.711) which browsers cannot play natively. go2rtc uses ffmpeg to transcode audio to AAC. Click the speaker icon in the live view to unmute.
- **Continuous recording**: When enabled, ffmpeg records each camera's RTSP stream into 5-minute MP4 segments with AAC audio. Completed segments are uploaded to Google Drive and cleaned up locally.
- **Location grouping**: Cameras can be assigned to a location for visual grouping on the dashboard. Cameras without a location appear under "Ungrouped".
