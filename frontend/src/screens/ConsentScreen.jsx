export default function ConsentScreen({ onAccept }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-12 py-16 text-center">
      <p className="text-xs tracking-[0.02em] uppercase text-brand-muted mb-10 animate-fade-in">
        The Ordinary
      </p>

      <h1 className="font-[Raleway] text-5xl font-bold tracking-[-0.012em] mb-4 animate-fade-up">
        Discover Your Skin
      </h1>
      <p className="font-[Raleway] text-brand-muted text-lg font-light max-w-md mb-16 animate-fade-up" style={{ animationDelay: '60ms' }}>
        A 30-second visual analysis. We observe. You decide.
      </p>

      <div className="border border-zinc-800 px-8 py-6 max-w-sm mb-12 text-left animate-fade-up" style={{ animationDelay: '120ms' }}>
        <p className="font-[Raleway] text-xs tracking-[0.02em] uppercase text-brand-muted mb-3">
          Privacy Notice
        </p>
        <p className="font-[Raleway] text-sm text-zinc-400 leading-relaxed">
          Your image is processed locally and is not stored, transmitted, or
          retained after your session ends. Analysis results are observational
          only — not a medical assessment.
        </p>
      </div>

      <button
        onClick={onAccept}
        className="font-[Raleway] bg-brand-offwhite text-brand-black px-14 py-4 text-sm tracking-[0.02em] uppercase font-medium hover:brightness-105 active:scale-95 transition-all duration-300 ease-[cubic-bezier(.645,.045,.355,1)] animate-fade-up"
        style={{ animationDelay: '180ms' }}
      >
        Begin Analysis
      </button>

      <p className="font-[Raleway] text-xs text-zinc-600 mt-8 max-w-xs animate-fade-up" style={{ animationDelay: '240ms' }}>
        By continuing, you consent to on-device image processing as described above.
      </p>
    </div>
  )
}
