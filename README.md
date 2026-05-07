# The Ordinary — Skin Analysis Kiosk

Retail kiosk prototype. Camera scans a face → Skin Vision Agent describes observable characteristics → Regimen Agent recommends an AM/PM routine, pulling live products from The Ordinary's immersive pop-up page alongside the local catalog.

---

## Quick start (TL;DR)

You need **two separate terminals open at the same time.**

**Terminal 1 — Python backend:**
```bash
cd backend
pip install -r requirements.txt   # first time only
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Node frontend:**
```bash
cd frontend
npm install                        # first time only
npm run dev
```

Then open **http://localhost:5173** in your browser.

> **Important:** `npm install` and `npm run dev` must be run from the `frontend/` folder — **not** `backend/`. The backend is Python, not Node.

---

## Project structure

```
backend/
  main.py                 FastAPI app — /analyze and /recommend endpoints
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
  vite.config.js          Proxies /api/* → localhost:8000

shared/schemas/           JSON Schema contracts for both agents' outputs
products/catalog.json     10 The Ordinary hero products with targeting metadata
```

---

## Prerequisites

| Tool | Minimum version | Check |
|---|---|---|
| Python | 3.11 | `python3 --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| Anthropic API key | — | [console.anthropic.com](https://console.anthropic.com) |

---

## Running locally

You need **two terminal windows** — one for the backend, one for the frontend.

### Terminal 1 — Backend

```bash
cd backend

# Create and activate a virtual environment (first time only)
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Set your API key (required for live mode)
export ANTHROPIC_API_KEY=sk-ant-...

# Start the server
uvicorn main:app --reload --reload-exclude '.venv' --port 8000
```

The backend starts at **http://localhost:8000**.
Interactive API docs (Swagger UI) at **http://localhost:8000/docs**.

> **Mock mode:** If you omit `ANTHROPIC_API_KEY`, the server runs with hardcoded
> responses — no API calls are made. Useful for UI work. Confirm which mode is
> active with `curl http://localhost:8000/health`.

### Terminal 2 — Frontend

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start the dev server
npm run dev
```

The frontend starts at **http://localhost:5173**.
Vite automatically proxies every `/api/*` request to the backend.

Open **http://localhost:5173** in your browser to use the kiosk.

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

---

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
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once,
> then retry activation.

---

### Terminal 2 — Frontend (Windows)

Same commands as macOS — Node.js and npm work identically on Windows:

```cmd
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

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
| **Live** | `export ANTHROPIC_API_KEY=sk-ant-...` | Real Skin Vision Agent (Opus 4.7) + Regimen Agent (Sonnet 4.6) + live site fetch |

---

## Monitoring what's happening in the background

When running in **live mode**, the backend prints structured log lines to the
terminal. Every entry has a timestamp, level, module name, and message.

```
HH:MM:SS  LEVEL     module        message
```

### What each module logs

#### `skin_vision` — what the face scan is doing

```
10:14:32  INFO   skin_vision  [API call] model=claude-opus-4-7  task=skin_analysis  image_size=187,432 bytes
```
→ About to send the webcam frame to Claude Opus. Shows the exact model and image payload size.

```
10:14:35  INFO   skin_vision  [API response] stop_reason=end_turn  input_tokens=1842  output_tokens=312
```
→ Claude responded. `input_tokens` includes the base64 image. `stop_reason=end_turn` means a clean finish.

```
10:14:35  INFO   skin_vision  [skin_vision] image_usable=True  quality_confidence=0.93  issues=[]
```
→ Image quality gate passed. If `image_usable=False` you'll see the specific issues (e.g. `blurry`, `face_not_detected`).

```
10:14:35  INFO   skin_vision  [skin_vision] top_concerns(3): oiliness:moderate, dark_circles:moderate, dehydration:mild
```
→ The concerns that will be handed to the regimen agent. These drive every product choice downstream.

```
10:14:35  DEBUG  skin_vision  [skin_vision] zone=forehead  concerns=oiliness(moderate,conf=0.82), enlarged_pores(mild,conf=0.75)
```
→ Per-zone detail (DEBUG level). One line per zone that has at least one concern.

---

#### `catalog_sync` — live product fetch from The Ordinary website

```
10:14:35  INFO   catalog_sync  Fetching popup page: https://theordinary.com/en-us/the-ordinary-immersive-pop-up.html
```
→ Outbound request to The Ordinary's immersive pop-up page. Triggered by the regimen agent's `fetch_popup_products` tool call.

```
10:14:36  INFO   catalog_sync  Popup page extraction complete — 4 product(s) found via json-ld
```
→ How many products were extracted and which strategy worked (`json-ld`, `shopify-embedded`, or `title-scrape`).

```
10:14:36  WARNING  catalog_sync  HTTP error fetching popup page: ...
```
→ Network or HTTP error. The regimen agent will fall back to the local catalog automatically.

---

#### `regimen` — what the routine builder is doing

```
10:14:35  INFO   regimen  [regimen] Starting regimen build  top_concerns=['oiliness', 'dark_circles', 'dehydration']
```
→ Regimen agent started. The concern list comes directly from skin_vision's `top_concerns`.

```
10:14:35  INFO   regimen  [API call] model=claude-sonnet-4-6  task=regimen_build  iteration=1  messages_in_context=1
```
→ First call in the tool-use loop. `iteration` increments each time Claude responds and asks for more tool results.

```
10:14:36  INFO   regimen  [API response] stop_reason=tool_use  input_tokens=980  output_tokens=88  tool_calls=1
```
→ Claude wants to call a tool before finishing. `stop_reason=tool_use` means the loop continues.

```
10:14:36  INFO   regimen  [tool] fetch_popup_products → 4 product(s) from site
10:14:36  INFO   regimen  [tool] get_products_by_concern  concerns=['oiliness', 'dark_circles']  time_of_day=any  → 3 match(es)
```
→ Tool dispatch results. Shows exactly what the agent asked for and what came back.

```
10:14:38  INFO   regimen  [API response] stop_reason=end_turn  input_tokens=2340  output_tokens=610  tool_calls=0
```
→ Claude finished — no more tool calls, generating the final JSON routine.

```
10:14:38  INFO   regimen  [regimen] Build complete  am_steps=3  pm_steps=4  layering_notes=2  total_iterations=3
```
→ Summary: routine shape and how many API round-trips the tool loop took.

---

### Typical full-session log flow

```
skin_vision  [API call] ...
skin_vision  [API response] stop_reason=end_turn ...
skin_vision  [skin_vision] image_usable=True ...
skin_vision  [skin_vision] top_concerns(3): ...

regimen      [regimen] Starting regimen build ...
catalog_sync Fetching popup page ...
regimen      [API call] ... iteration=1
regimen      [API response] stop_reason=tool_use ... tool_calls=1
catalog_sync Popup page extraction complete ...
regimen      [tool] fetch_popup_products → N product(s)
regimen      [API call] ... iteration=2
regimen      [API response] stop_reason=tool_use ... tool_calls=1
regimen      [tool] get_products_by_concern ...
regimen      [API call] ... iteration=3
regimen      [API response] stop_reason=end_turn ...
regimen      [regimen] Build complete ...
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
- Add `ANTHROPIC_API_KEY` to a `.env` file and load it with `python-dotenv`
