import { useEffect, useState } from 'react'

const IMAGES = [
  '/hero/pexels-cottonbro-6559905.jpg',
  '/hero/pexels-cottonbro-7255933.jpg',
  '/hero/pexels-emilianovittoriosi-21792057.jpg',
  '/hero/pexels-maksgelatin-5506146.jpg',
  '/hero/pexels-rada-aslanova-150604297-18620713.jpg',
  '/hero/pexels-shvetsa-4672238.jpg',
  '/hero/pexels-shvetsa-5034454.jpg',
]

export default function ConsentScreen({ onAccept }) {
  const [current, setCurrent] = useState(0)
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const id = setInterval(() => {
      setVisible(false)
      setTimeout(() => {
        setCurrent(i => (i + 1) % IMAGES.length)
        setVisible(true)
      }, 500)
    }, 5000)
    return () => clearInterval(id)
  }, [])

  return (
    // White page — visible as side margins on desktop
    <div className="min-h-screen bg-white flex items-center justify-center">

      {/* 9:16 kiosk frame — fills screen on kiosk, portrait column on desktop */}
      <div
        className="relative overflow-hidden"
        style={{ width: 'min(100vw, calc(100vh * 9 / 16))', height: '100vh' }}
      >
        {/* Sliding background image */}
        <img
          src={IMAGES[current]}
          alt=""
          className="absolute inset-0 w-full h-full object-cover transition-opacity duration-500"
          style={{ opacity: visible ? 1 : 0 }}
        />

        {/* White wash overlay — keeps black text legible over any image */}
        <div className="absolute inset-0 bg-white/50" />

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center justify-center h-full px-12 py-16 text-center">

          <h1 className="font-[Raleway] text-4xl font-light tracking-[0.4em] uppercase text-black mb-14 animate-fade-in">
            The Ordinary
          </h1>

          <p className="font-[Raleway] text-3xl font-light text-black mb-4 animate-fade-up">
            Discover Your Skin
          </p>
          <p className="font-[Raleway] text-sm text-black font-light max-w-sm mb-14 animate-fade-up" style={{ animationDelay: '60ms' }}>
            A 30-second visual analysis. We observe. You decide.
          </p>

          <div className="border border-black px-8 py-6 max-w-sm mb-12 text-left animate-fade-up" style={{ animationDelay: '120ms' }}>
            <p className="font-[Raleway] text-xs tracking-[0.2em] uppercase text-black mb-3">
              Privacy Notice
            </p>
            <p className="font-[Raleway] text-sm text-black leading-relaxed">
              Your image is processed locally and is not stored, transmitted, or
              retained after your session ends. Analysis results are observational
              only — not a medical assessment.
            </p>
          </div>

          <button
            onClick={onAccept}
            className="font-[Raleway] bg-black text-white px-14 py-4 text-sm tracking-[0.2em] uppercase font-medium hover:bg-zinc-900 active:scale-95 transition-all duration-300 ease-[cubic-bezier(.645,.045,.355,1)] animate-fade-up"
            style={{ animationDelay: '180ms' }}
          >
            Begin Analysis
          </button>

          <p className="font-[Raleway] text-xs text-black mt-8 max-w-xs animate-fade-up" style={{ animationDelay: '240ms' }}>
            By continuing, you consent to on-device image processing as described above.
          </p>
        </div>
      </div>
    </div>
  )
}
