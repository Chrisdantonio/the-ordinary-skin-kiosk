import { useEffect, useRef, useState } from 'react'
import { analyzeImage, getRecommendations } from '../api'

const PHASES = {
  READY: 'ready',
  COUNTDOWN: 'countdown',
  ANALYZING: 'analyzing',
  ERROR: 'error',
}

const ZONES = [
  'Analysing forehead',
  'Analysing cheekbones',
  'Analysing T-zone',
  'Analysing under-eye area',
  'Analysing jawline',
  'Analysing skin texture',
]

export default function CaptureScreen({ onComplete }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const [phase, setPhase] = useState(PHASES.READY)
  const [countdown, setCountdown] = useState(null)
  const [error, setError] = useState(null)
  const [zoneIndex, setZoneIndex] = useState(0)

  useEffect(() => {
    let active = true
    navigator.mediaDevices
      .getUserMedia({ video: { width: 1280, height: 720, facingMode: 'user' } })
      .then((stream) => {
        if (!active) { stream.getTracks().forEach(t => t.stop()); return }
        streamRef.current = stream
        if (videoRef.current) videoRef.current.srcObject = stream
      })
      .catch(() => {
        if (active) setError('Camera access denied. Please allow camera permissions and refresh.')
      })
    return () => {
      active = false
      streamRef.current?.getTracks().forEach(t => t.stop())
    }
  }, [])

  useEffect(() => {
    if (phase !== PHASES.ANALYZING) return
    setZoneIndex(0)
    const id = setInterval(() => {
      setZoneIndex(i => (i + 1) % ZONES.length)
    }, 1500)
    return () => clearInterval(id)
  }, [phase])

  async function handleCapture() {
    setPhase(PHASES.COUNTDOWN)

    for (let i = 3; i >= 1; i--) {
      setCountdown(i)
      await new Promise((resolve) => setTimeout(resolve, 1000))
    }
    setCountdown(null)

    const canvas = canvasRef.current
    const video = videoRef.current
    const ctx = canvas.getContext('2d')
    ctx.save()
    ctx.scale(-1, 1)
    ctx.drawImage(video, -canvas.width, 0, canvas.width, canvas.height)
    ctx.restore()

    canvas.toBlob((blob) => runAnalysis(blob), 'image/jpeg', 0.92)
  }

  async function runAnalysis(blob) {
    setPhase(PHASES.ANALYZING)
    try {
      const skinVision = await analyzeImage(blob)
      const regimen = await getRecommendations(skinVision)
      onComplete(skinVision, regimen)
    } catch (err) {
      setError('Analysis failed. Please try again.')
      setPhase(PHASES.ERROR)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white relative">
      <canvas ref={canvasRef} className="hidden" width={1280} height={720} />

      <h1 className="font-[Raleway] text-4xl font-light tracking-[0.4em] uppercase text-black mb-8 animate-fade-in">
        The Ordinary
      </h1>

      <div className="relative w-full max-w-2xl aspect-video bg-brand-warm-dark overflow-hidden">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover scale-x-[-1]"
        />

        {/* Face-position guide overlay */}
        {phase === PHASES.READY && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-48 h-64 border border-white/30 rounded-full" />
          </div>
        )}

        {/* Countdown overlay */}
        {phase === PHASES.COUNTDOWN && countdown !== null && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40">
            <span className="font-[Raleway] text-8xl font-light text-white tabular-nums">
              {countdown}
            </span>
          </div>
        )}

        {/* Analysing overlay */}
        {phase === PHASES.ANALYZING && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/70 gap-5 overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-full pointer-events-none">
              <div className="h-px w-full bg-white/40 animate-scan-line" />
            </div>

            <p className="font-[Raleway] text-xs tracking-[0.3em] uppercase text-white animate-pulse-muted relative z-10">
              Analysing
            </p>

            <div key={zoneIndex} className="relative z-10 flex flex-col items-center gap-3 animate-fade-up">
              <p className="font-[Raleway] text-xs tracking-[0.3em] uppercase text-white animate-pulse-muted">
                {ZONES[zoneIndex]}
              </p>
              <div className="w-48 h-px bg-white/20 overflow-hidden">
                <div
                  className="h-full bg-white/60 transition-all duration-700 ease-out"
                  style={{ width: `${((zoneIndex + 1) / ZONES.length) * 100}%` }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Instruction / action row */}
      <div className="mt-10 flex flex-col items-center gap-3">
        {phase === PHASES.READY && (
          <>
            <p className="font-[Raleway] text-sm text-black tracking-[0.02em]">
              Centre your face in the guide, then tap to capture.
            </p>
            <button
              onClick={handleCapture}
              className="mt-2 w-16 h-16 rounded-full border border-black bg-transparent hover:bg-black/5 active:scale-95 transition-all duration-300 ease-[cubic-bezier(.645,.045,.355,1)] flex items-center justify-center"
              aria-label="Capture"
            >
              <span className="w-10 h-10 rounded-full bg-black block" />
            </button>
          </>
        )}

        {phase === PHASES.ERROR && (
          <>
            <p className="font-[Raleway] text-sm text-black">{error}</p>
            <button
              onClick={() => { setError(null); setPhase(PHASES.READY) }}
              className="font-[Raleway] mt-2 px-8 py-3 bg-black text-white text-sm tracking-[0.02em] uppercase hover:bg-zinc-900 transition-colors duration-300 ease-[cubic-bezier(.645,.045,.355,1)]"
            >
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  )
}
