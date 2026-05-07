const { app, BrowserWindow, ipcMain, session } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const http = require('http')
const fs = require('fs')

// ── Path resolution ───────────────────────────────────────────────────────────
// app.isPackaged is true when running from an electron-builder .app bundle.
// In dev (electron .) all paths are relative to the repo root; in the bundle
// they come from process.resourcesPath (Contents/Resources/).

const IS_PACKAGED = app.isPackaged

// Root of the repo in dev, Contents/Resources in the bundle
const RES = IS_PACKAGED ? process.resourcesPath : path.join(__dirname, '..')

// Writable location for the saved API key (.env)
const ENV_FILE = IS_PACKAGED
  ? path.join(app.getPath('userData'), '.env')
  : path.join(RES, 'backend', '.env')

const BACKEND_PORT = 8000
const FRONTEND_PORT = 5173

let keyWindow = null
let mainWindow = null
let backendProc = null
let frontendServer = null

// ── Saved key helpers ─────────────────────────────────────────────────────────

function readSavedKey() {
  try {
    const content = fs.readFileSync(ENV_FILE, 'utf8')
    const match = content.match(/^ANTHROPIC_API_KEY=(.+)$/m)
    return match ? match[1].trim() : null
  } catch {
    return null
  }
}

function saveKey(apiKey) {
  fs.mkdirSync(path.dirname(ENV_FILE), { recursive: true })
  fs.writeFileSync(ENV_FILE, `ANTHROPIC_API_KEY=${apiKey}\n`)
}

// ── Static file server (replaces Vite dev proxy in packaged/built mode) ───────
// Serves frontend/dist on FRONTEND_PORT and reverse-proxies /api/* → backend.

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript',
  '.css':  'text/css',
  '.json': 'application/json',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.woff': 'font/woff',
  '.woff2':'font/woff2',
}

function startFrontendServer(distPath) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      const parsedUrl = new URL(req.url, `http://localhost:${FRONTEND_PORT}`)
      const pathname = parsedUrl.pathname

      if (pathname.startsWith('/api/')) {
        // Strip /api prefix and proxy to FastAPI backend
        const backendPath = pathname.slice(4) + (parsedUrl.search || '')
        const opts = {
          hostname: '127.0.0.1',
          port: BACKEND_PORT,
          path: backendPath,
          method: req.method,
          headers: { ...req.headers, host: `localhost:${BACKEND_PORT}` },
        }
        const proxy = http.request(opts, (upstream) => {
          res.writeHead(upstream.statusCode, upstream.headers)
          upstream.pipe(res)
        })
        proxy.on('error', () => res.writeHead(502).end('Backend unavailable'))
        req.pipe(proxy)
        return
      }

      // Serve static file, falling back to index.html for SPA client-side routes
      let filePath = path.join(distPath, pathname === '/' ? 'index.html' : pathname)
      if (!fs.existsSync(filePath)) filePath = path.join(distPath, 'index.html')

      fs.readFile(filePath, (err, data) => {
        if (err) {
          res.writeHead(404).end('Not Found')
        } else {
          const mime = MIME[path.extname(filePath).toLowerCase()] || 'application/octet-stream'
          res.writeHead(200, { 'Content-Type': mime })
          res.end(data)
        }
      })
    })

    server.listen(FRONTEND_PORT, '127.0.0.1', () => resolve(server))
    server.on('error', reject)
  })
}

// ── Backend process ───────────────────────────────────────────────────────────

function spawnBackend(apiKey) {
  // Packaged: run the PyInstaller binary (no args needed — port is hardcoded in server.py)
  // Dev: use uvicorn from the venv directly
  const IS_WIN = process.platform === 'win32'
  const bin = IS_PACKAGED
    ? path.join(RES, 'backend', IS_WIN ? 'kiosk-backend.exe' : 'kiosk-backend')
    : path.join(RES, 'backend', '.venv', IS_WIN ? 'Scripts/uvicorn.exe' : 'bin/uvicorn')

  const args = IS_PACKAGED
    ? []
    : ['main:app', '--port', String(BACKEND_PORT)]

  const cwd = IS_PACKAGED
    ? path.join(RES, 'backend')
    : path.join(RES, 'backend')

  backendProc = spawn(bin, args, {
    cwd,
    env: { ...process.env, ANTHROPIC_API_KEY: apiKey },
  })
  backendProc.stdout.on('data', (d) => process.stdout.write('[backend] ' + d))
  backendProc.stderr.on('data', (d) => process.stderr.write('[backend] ' + d))
}

// ── Poll a URL until it responds ──────────────────────────────────────────────

function pollUrl(url, intervalMs, timeoutMs) {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + timeoutMs
    const attempt = () => {
      const req = http.get(url, (res) => { res.resume(); resolve() })
      req.setTimeout(1000, () => req.destroy())
      req.on('error', () => {
        if (Date.now() >= deadline) reject(new Error(`Timed out waiting for ${url}`))
        else setTimeout(attempt, intervalMs)
      })
    }
    attempt()
  })
}

// ── Key entry window ──────────────────────────────────────────────────────────

function createKeyWindow() {
  keyWindow = new BrowserWindow({
    width: 460,
    height: 400,
    resizable: false,
    center: true,
    titleBarStyle: 'hiddenInset',
    title: 'The Ordinary — Skin Kiosk',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })
  keyWindow.loadFile(path.join(__dirname, 'api-key.html'))
}

// ── Main kiosk window ─────────────────────────────────────────────────────────

function createMainWindow() {
  session.defaultSession.setPermissionRequestHandler((_, permission, callback) => {
    callback(permission === 'media')
  })

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 900,
    center: true,
    title: 'The Ordinary — Skin Kiosk',
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  })
  mainWindow.loadURL(`http://127.0.0.1:${FRONTEND_PORT}`)
}

// ── IPC ───────────────────────────────────────────────────────────────────────

ipcMain.handle('get-saved-key', () => readSavedKey())

ipcMain.on('launch', async (event, { apiKey, save }) => {
  if (save) saveKey(apiKey)

  const status = (msg) => {
    if (keyWindow && !keyWindow.isDestroyed()) keyWindow.webContents.send('status', msg)
  }

  const distPath = path.join(RES, 'frontend', 'dist')

  status('Starting servers…')

  try {
    // Start both in parallel; the Node server resolves immediately, backend takes a moment.
    const [server] = await Promise.all([
      startFrontendServer(distPath),
      (spawnBackend(apiKey), Promise.resolve()),
    ])
    frontendServer = server

    status('Waiting for backend…')
    await pollUrl(`http://127.0.0.1:${BACKEND_PORT}/health`, 500, 30_000)

    status('Launching kiosk…')
    createMainWindow()
    keyWindow.close()
  } catch (err) {
    status(`Failed to start: ${err.message}`)
  }
})

// ── App lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(createKeyWindow)

app.on('will-quit', () => {
  backendProc?.kill()
  frontendServer?.close()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
