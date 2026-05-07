# The Ordinary — Skin Analysis Kiosk

Retail kiosk prototype. Camera scans a face → Skin Vision Agent describes observable characteristics → Regimen Agent recommends an AM/PM routine, pulling live products from The Ordinary's immersive pop-up page alongside the local catalog.

---

## Quick start

### Desktop app (recommended)

```bash
# From the project root — one command, one window
npm start
```

A branded API key entry window appears. Enter your `ANTHROPIC_API_KEY`, optionally tick **Remember for next launch**, and click **Launch Kiosk**. The app starts the Python backend and serves the frontend automatically, then opens the kiosk window.

> **First run:** you must build the frontend once before `npm start` works.
> ```bash
> npm run build:frontend
> npm start
> ```

### Two-terminal dev mode (legacy)

If you prefer hot-reload during active UI development:

**Terminal 1 — Backend:**
```bash
cd backend
source .venv/bin/activate
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload --reload-exclude '.venv' --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## Project structure

```
backend/
  main.py                 FastAPI app — /analyze and /recommend endpoints
  server.py               PyInstaller entry point (starts uvicorn programmatically)
  kiosk_backend.spec      PyInstaller build spec (bundles catalog, SSL certs, hidden imports)
  agents/
    skin_vision.py        Claude Opus 4.7 — multimodal skin analysis
    regimen.py            Claude Sonnet 4.6 — tool-calling routine builder
  catalog_sync.py         Fetches live products from theordinary.com pop-up page
  log_utils.py            Shared logging setup (stdout, timestamped)
  requirements.txt

frontend/
  src/
    screens/
      ConsentScreen.jsx   Step 1 — consent gate before camera activates
      CaptureScreen.jsx   Step 2 — webcam capture + 3-second countdown
      ResultsScreen.jsx   Step 3 — skin profile + AM/PM routine display
    api.js                fetch wrappers for /analyze and /recommend
  vite.config.js          Proxies /api/* → localhost:8000 (dev only)

electron/
  main.js                 Electron main process — spawns backend, serves frontend, manages windows
  preload.js              Secure IPC bridge (contextBridge) between main and renderer
  api-key.html            Branded API key entry screen shown on launch

shared/schemas/           JSON Schema contracts for both agents' outputs
products/catalog.json     10 The Ordinary hero products with targeting metadata
```

---

## Building a distributable .app

```bash
npm run dist
```

This runs three steps in sequence:

1. **`npm run build:frontend`** — Vite builds `frontend/dist/`
2. **`npm run build:backend`** — PyInstaller compiles the FastAPI server into a standalone binary at `backend/dist/kiosk-backend/`
3. **`electron-builder --mac`** — packages everything into `dist-app/mac-arm64/Ordinary Kiosk.app`

The resulting `.app` (~321 MB) is fully self-contained — no Python, Node, or `npm install` required on the target machine.

### Bundle layout

```
Ordinary Kiosk.app/Contents/Resources/
  app.asar                    Electron JS (main.js, preload.js, api-key.html)
  frontend/dist/              Built React app served by the Node static server
  backend/
    kiosk-backend             PyInstaller binary (entry point)
    _internal/                Python 3.14 runtime + all pip dependencies
      products/catalog.json   Bundled catalog (read via sys._MEIPASS at runtime)
      certifi/                SSL certificates for outbound httpx requests
```

> **macOS Gatekeeper:** the build is unsigned (`"identity": null` in `package.json`). macOS may show a "damaged" or "unidentified developer" warning. Right-click → **Open** to bypass, or run once:
> ```bash
> xattr -rd com.apple.quarantine "dist-app/mac-arm64/Ordinary Kiosk.app"
> ```

---

## Building a distributable Windows installer

> **Must be run on a Windows machine.** The Python backend binary must be compiled on the same OS it will run on — cross-compiling from macOS is not supported for the PyInstaller step.

### Prerequisites (Windows build machine)

Same as the dev prerequisites table below, plus:

- **PyInstaller** must be installed inside the venv (`pip install pyinstaller`)
- **Inno Setup / NSIS** is handled automatically by electron-builder — no manual install needed

### Steps

**Step 1 — Build the frontend** (PowerShell or cmd):

```cmd
npm run build:frontend
```

**Step 2 — Build the backend binary** (the `dist:win` script uses a Unix path for PyInstaller, so run this step manually on Windows):

```cmd
cd backend
.venv\Scripts\activate
pyinstaller kiosk_backend.spec --noconfirm
cd ..
```

**Step 3 — Package with electron-builder:**

```cmd
npx electron-builder --win
```

Or run all three steps at once if you patch `build:backend` to use the Windows path:

```cmd
npm run dist:win
```

> **Note:** `npm run dist:win` will fail on an unpatched repo because `build:backend` calls `.venv/bin/pyinstaller` (Unix path). Either run the three steps above manually, or temporarily edit `package.json` → `build:backend` to use `.venv\Scripts\pyinstaller` before running `dist:win`.

### Output

```
dist-app/
  win-unpacked/              Unsigned portable build
  Ordinary Kiosk Setup.exe  NSIS installer — creates Start Menu + Desktop shortcuts
```

Run `Ordinary Kiosk Setup.exe` to install. The installer lets the user choose the installation directory and creates an uninstaller entry in **Add or Remove Programs**.

### Bundle layout (Windows)

```
%LOCALAPPDATA%\Programs\Ordinary Kiosk\
  resources\
    app.asar                    Electron JS (main.js, preload.js, api-key.html)
    frontend\dist\              Built React app
    backend\
      kiosk-backend.exe         PyInstaller binary
      _internal\                Python runtime + pip dependencies
        products\catalog.json
        certifi\
```

### Windows SmartScreen warning

The installer is unsigned. Windows Defender SmartScreen will show **"Windows protected your PC"** on first run. Click **More info → Run anyway** to proceed.

To suppress this for internal distribution, sign the installer with a code-signing certificate:

```cmd
signtool sign /fd SHA256 /t http://timestamp.digicert.com "dist-app\Ordinary Kiosk Setup.exe"
```

---

## Prerequisites (dev only)

| Tool | Minimum version | Check |
|---|---|---|
| Python | 3.11 | `python3 --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| Anthropic API key | — | [console.anthropic.com](https://console.anthropic.com) |

The distributable `.app` bundles its own Python runtime and does not require any of these on the end-user machine.

---

## How the desktop shell works

The Electron main process (`electron/main.js`) orchestrates three things:

1. **API key window** — a minimal branded dialog shown at launch. On submit, the key is passed as `ANTHROPIC_API_KEY` into the backend process environment. Ticking "Remember" writes it to `backend/.env` (dev) or `~/Library/Application Support/Ordinary Kiosk/.env` (packaged), which is read and pre-filled on the next launch.

2. **Backend process** — in dev, spawns `uvicorn` from the `.venv`; in a packaged app, spawns the PyInstaller binary at `Resources/backend/kiosk-backend`. Both expose the FastAPI server on `localhost:8000`.

3. **Frontend server** — a Node.js HTTP server (no extra dependencies) that serves `frontend/dist/` on `localhost:5173` and reverse-proxies `/api/*` requests to the backend, replicating what Vite's dev proxy did at build time.

The kiosk window loads `http://localhost:5173`. Camera permissions are granted automatically via `session.setPermissionRequestHandler`.

---

## Running locally (dev)

### Backend

```bash
cd backend

# Create virtual environment (first time only)
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Set your API key (required for live mode)
export ANTHROPIC_API_KEY=sk-ant-...

# Start the server
uvicorn main:app --reload --reload-exclude '.venv' --port 8000
```

### Frontend (build once for Electron, or run dev server for hot reload)

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Build for Electron / npm start
npm run build

# OR run the hot-reload dev server (two-terminal mode)
npm run dev
```

---

## Windows installation and use

The commands above are written for macOS/Linux. Windows users need a few adjustments depending on whether they use **Command Prompt (cmd)** or **PowerShell**.

### Prerequisites check (Windows)

On Windows, Python is usually invoked as `python` (not `python3`):

```cmd
python --version
node --version
npm --version
```

If `python` is not recognised, download the installer from [python.org](https://www.python.org/downloads/) and check **"Add Python to PATH"** during installation.

### Terminal 1 — Backend (Windows)

**Command Prompt:**

```cmd
cd backend

:: Create and activate virtual environment (first time only)
python -m venv .venv
.venv\Scripts\activate

:: Install dependencies (first time only)
pip install -r requirements.txt

:: Set your API key
set ANTHROPIC_API_KEY=sk-ant-...

:: Start the server
uvicorn main:app --reload --reload-exclude ".venv" --port 8000
```

**PowerShell:**

```powershell
cd backend

# Create and activate virtual environment (first time only)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies (first time only)
pip install -r requirements.txt

# Set your API key
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# Start the server
uvicorn main:app --reload --reload-exclude ".venv" --port 8000
```

> **PowerShell execution policy:** If `.venv\Scripts\Activate.ps1` is blocked, run
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once.

### Terminal 2 — Frontend (Windows)

```cmd
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

### Windows-specific gotchas

| Issue | Fix |
|---|---|
| `python3` not recognised | Use `python` instead. Confirm with `python --version`. |
| `uvicorn` not found after activating venv | Make sure the venv is active — prompt should show `(.venv)`. Re-run `.venv\Scripts\activate`. |
| Camera not accessible | Allow camera access in **Settings → Privacy & Security → Camera** and make sure the browser has permission. |
| Port 8000 or 5173 already in use | Find the process with `netstat -ano \| findstr :8000` and end it in Task Manager, or change the port in the uvicorn / Vite commands. |
| `ANTHROPIC_API_KEY` lost between sessions | `set` and `$env:` only last for the current terminal session. To persist it, add it via **System Properties → Environment Variables**. |

---

## Modes

| Mode | How to activate | What runs |
|---|---|---|
| **Mock** (default) | No `ANTHROPIC_API_KEY` set | Hardcoded skin vision + regimen — zero API cost, instant responses |
| **Live** | `ANTHROPIC_API_KEY` set (via Electron dialog, `.env`, or shell export) | Real Skin Vision Agent (Opus 4.7) + Regimen Agent (Sonnet 4.6) + live site fetch |

---

## Monitoring what's happening in the background

When running in **live mode**, the backend prints structured log lines to the terminal (or to Electron's stdout when launched via `npm start`). Every entry has a timestamp, level, module name, and message.

```
HH:MM:SS  LEVEL     module        message
```

### What each module logs

#### `skin_vision` — what the face scan is doing

```
10:14:32  INFO   skin_vision  [API call] model=claude-opus-4-7  task=skin_analysis  image_size=187,432 bytes
10:14:35  INFO   skin_vision  [API response] stop_reason=end_turn  input_tokens=1842  output_tokens=312
10:14:35  INFO   skin_vision  [skin_vision] image_usable=True  quality_confidence=0.93  issues=[]
10:14:35  INFO   skin_vision  [skin_vision] top_concerns(3): oiliness:moderate, dark_circles:moderate, dehydration:mild
10:14:35  DEBUG  skin_vision  [skin_vision] zone=forehead  concerns=oiliness(moderate,conf=0.82), enlarged_pores(mild,conf=0.75)
```

#### `catalog_sync` — live product fetch from The Ordinary website

```
10:14:35  INFO   catalog_sync  Fetching popup page: https://theordinary.com/en-us/the-ordinary-immersive-pop-up.html
10:14:36  INFO   catalog_sync  Popup page extraction complete — 4 product(s) found via json-ld
10:14:36  WARNING  catalog_sync  HTTP error fetching popup page: ...
```

#### `regimen` — what the routine builder is doing

```
10:14:35  INFO   regimen  [regimen] Starting regimen build  top_concerns=['oiliness', 'dark_circles', 'dehydration']
10:14:35  INFO   regimen  [API call] model=claude-sonnet-4-6  task=regimen_build  iteration=1  messages_in_context=1
10:14:36  INFO   regimen  [API response] stop_reason=tool_use  input_tokens=980  output_tokens=88  tool_calls=1
10:14:36  INFO   regimen  [tool] fetch_popup_products → 4 product(s) from site
10:14:36  INFO   regimen  [tool] get_products_by_concern  concerns=['oiliness', 'dark_circles']  time_of_day=any  → 3 match(es)
10:14:38  INFO   regimen  [API response] stop_reason=end_turn  input_tokens=2340  output_tokens=610  tool_calls=0
10:14:38  INFO   regimen  [regimen] Build complete  am_steps=3  pm_steps=4  layering_notes=2  total_iterations=3
```

---

## Agent summary

| Agent | File | Model | What it does |
|---|---|---|---|
| Skin Vision | `backend/agents/skin_vision.py` | claude-opus-4-7 | Single vision call. Returns per-zone concerns + top 5 concerns. Raises `UnusableImageError` on bad images. |
| Regimen | `backend/agents/regimen.py` | claude-sonnet-4-6 | Tool-calling loop. Calls `fetch_popup_products` (live site) then `get_products_by_concern` (catalog). Enforces layering rules in system prompt. |

### Regimen agent tools

| Tool | Source | Purpose |
|---|---|---|
| `fetch_popup_products` | `catalog_sync.py` → theordinary.com | Live products from The Ordinary's pop-up page — prioritised when relevant |
| `get_products_by_concern` | `products/catalog.json` | Filter local catalog by concern type and AM/PM slot |
| `get_product_details` | `products/catalog.json` | Full details for a single product by ID |

---

## Layering rules

The regimen agent's system prompt encodes these safety rules:

- Retinol + AHAs/BHAs never on the same night
- Vitamin C (L-ascorbic acid) kept separate from niacinamide in the same step
- pH-sensitive actives (AHAs, BHAs, Vitamin C) applied before other serums
- No more than one exfoliant per routine — no AHA+BHA stacking
- Routines capped at 3–4 AM steps and 3–5 PM steps

---

## Constraints

- **Never diagnose** — observational language only. Clinical terms (acne, rosacea, etc.) are banned in both agents.
- **Images not persisted** — frames are captured in-browser and sent as multipart to the backend. No storage layer.
- **Consent required** — `ConsentScreen` must be accepted before the camera activates.

---

## What's next

- Expand `products/catalog.json` beyond the current 10 hero products
- QR code generation for checkout handoff (placeholder already in `ResultsScreen`)
- Skin tone equity testing across diverse subjects
- Code-sign the `.app` for distribution without Gatekeeper warnings
- Add a custom app icon (`build.mac.icon` in `package.json`)
