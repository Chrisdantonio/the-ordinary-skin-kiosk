import { useEffect, useRef, useState } from 'react'
import { analyzeImage, getRecommendations } from '../api'

const PHASES = {
  READY: 'ready',
  COUNTDOWN: 'countdown',
  ANALYZING: 'analyzing',
  ERROR: 'error',
}

export default function CaptureScreen({ onComplete }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const [phase, setPhase] = useState(PHASES.READY)
  const [countdown, setCountdown] = useState(null)
  const [error, setError] = useState(null)

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
    <div className="flex flex-col items-center justify-center min-h-screen relative">
      <canvas ref={canvasRef} className="hidden" width={1280} height={720} />

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
            <div className="w-48 h-64 border border-brand-offwhite/30 rounded-full" />
          </div>
        )}

        {/* Countdown overlay */}
        {phase === PHASES.COUNTDOWN && countdown !== null && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40">
            <span className="font-[Raleway] text-8xl font-light text-brand-offwhite tabular-nums">
              {countdown}
            </span>
          </div>
        )}

        {/* Analysing overlay — scan-line pattern, no spinning ring */}
        {phase === PHASES.ANALYZING && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/70 gap-6 overflow-hidden">
            {/* Horizontal hairline scan */}
            <div className="absolute inset-x-0 top-0 h-full pointer-events-none">
              <div className="h-px w-full bg-brand-offwhite/40 animate-scan-line" />
            </div>
            <p className="font-[Raleway] text-xs tracking-[0.02em] uppercase text-brand-muted animate-pulse-muted relative z-10">
              Analysing
            </p>
          </div>
        )}
      </div>

      {/* Instruction / action row */}
      <div className="mt-10 flex flex-col items-center gap-3">
        {phase === PHASES.READY && (
          <>
            <p className="font-[Raleway] text-sm text-brand-muted tracking-[0.02em]">
              Centre your face in the guide, then tap to capture.
            </p>
            <button
              onClick={handleCapture}
              className="mt-2 w-16 h-16 rounded-full border border-brand-offwhite bg-transparent hover:bg-brand-offwhite/10 active:scale-95 transition-all duration-300 ease-[cubic-bezier(.645,.045,.355,1)] flex items-center justify-center"
              aria-label="Capture"
            >
              <span className="w-10 h-10 rounded-full bg-brand-offwhite block" />
            </button>
          </>
        )}

        {phase === PHASES.ERROR && (
          <>
            <p className="font-[Raleway] text-sm text-brand-muted">{error}</p>
            <button
              onClick={() => { setError(null); setPhase(PHASES.READY) }}
              className="font-[Raleway] mt-2 px-8 py-3 border border-zinc-700 text-sm tracking-[0.02em] uppercase hover:border-zinc-400 transition-colors duration-300 ease-[cubic-bezier(.645,.045,.355,1)]"
            >
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  )
}
