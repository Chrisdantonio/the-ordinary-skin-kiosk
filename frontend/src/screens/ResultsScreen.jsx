function ConcernSeverityBar({ severity }) {
  const filled = { mild: 1, moderate: 2, pronounced: 3 }[severity] ?? 0
  return (
    <div className="flex gap-1">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className={`h-px flex-1 transition-colors duration-300 ${
            i <= filled ? 'bg-brand-offwhite' : 'bg-zinc-700'
          }`}
        />
      ))}
    </div>
  )
}

const SEVERITY_LABEL = {
  mild: 'Mild',
  moderate: 'Moderate',
  pronounced: 'Pronounced',
}

const CONCERN_LABEL = {
  dehydration: 'Dehydration',
  oiliness: 'Oiliness',
  redness: 'Redness',
  enlarged_pores: 'Enlarged Pores',
  uneven_tone: 'Uneven Tone',
  hyperpigmentation: 'Hyperpigmentation',
  dark_circles: 'Dark Circles',
  dullness: 'Dullness',
  fine_lines: 'Fine Lines',
  rough_texture: 'Rough Texture',
  occasional_breakout: 'Occasional Breakout',
  congestion: 'Congestion',
  flaking: 'Flaking',
  visible_sensitivity: 'Visible Sensitivity',
}

function ConcernBadge({ concern, index }) {
  return (
    <div
      className="flex flex-col gap-1.5 py-3 border-b border-zinc-800 last:border-0 animate-fade-up"
      style={{ animationDelay: `${index * 70}ms` }}
    >
      <div className="flex items-center justify-between">
        <span className="font-[Geologica] text-sm font-medium">
          {CONCERN_LABEL[concern.type] ?? concern.type}
        </span>
        <span className="font-[Geologica] text-xs text-brand-muted tracking-[0.02em]">
          {SEVERITY_LABEL[concern.severity]}
        </span>
      </div>
      <ConcernSeverityBar severity={concern.severity} />
    </div>
  )
}

function RoutineStep({ step, index }) {
  return (
    <div
      className="flex gap-4 py-4 border-b border-zinc-800 last:border-0 animate-fade-up"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <span className="font-mono text-xs text-brand-muted mt-0.5 w-4 shrink-0">
        {step.step}
      </span>
      <div className="flex flex-col gap-1">
        <p className="font-[Geologica] text-sm font-medium">{step.name}</p>
        <p className="font-[Geologica] text-xs text-zinc-400 leading-relaxed">{step.rationale}</p>
        <p className="font-[Geologica] text-xs text-brand-accent mt-0.5">{step.application}</p>
      </div>
    </div>
  )
}

export default function ResultsScreen({ skinVision, regimen, onRestart }) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-10 py-6 border-b border-zinc-800 animate-fade-in">
        <p className="font-[Geologica] text-xs tracking-[0.02em] uppercase text-brand-muted">
          The Ordinary
        </p>
        <button
          onClick={onRestart}
          className="font-[Geologica] text-xs tracking-[0.02em] uppercase text-brand-muted hover:text-brand-offwhite transition-colors duration-300 ease-[cubic-bezier(.645,.045,.355,1)]"
        >
          New Analysis
        </button>
      </header>

      <div className="flex flex-1 divide-x divide-zinc-800 overflow-auto">
        {/* Left: Skin Profile */}
        <section className="w-1/3 px-10 py-8 flex flex-col gap-6 shrink-0">
          <div className="animate-fade-up">
            <p className="font-[Geologica] text-xs tracking-[0.02em] uppercase text-brand-muted mb-1">
              Skin Profile
            </p>
            <h2 className="font-[Raleway] text-2xl font-light tracking-[-0.012em]">
              Your Observations
            </h2>
          </div>

          <div className="flex flex-col">
            {skinVision?.top_concerns?.map((concern, i) => (
              <ConcernBadge key={concern.type} concern={concern} index={i} />
            ))}
          </div>

          <p className="font-[Geologica] text-xs text-zinc-600 leading-relaxed mt-auto">
            {skinVision?.disclaimer}
          </p>
        </section>

        {/* Right: Regimen */}
        <section className="flex-1 px-10 py-8 flex flex-col gap-10 overflow-auto">
          {/* AM */}
          <div>
            <p className="font-[Geologica] text-xs tracking-[0.02em] uppercase text-brand-muted mb-4 animate-fade-up">
              Morning Routine
            </p>
            <div>
              {regimen?.am_routine?.map((step, i) => (
                <RoutineStep key={step.product_id} step={step} index={i} />
              ))}
            </div>
          </div>

          {/* PM */}
          <div>
            <p className="font-[Geologica] text-xs tracking-[0.02em] uppercase text-brand-muted mb-4 animate-fade-up">
              Evening Routine
            </p>
            <div>
              {regimen?.pm_routine?.map((step, i) => (
                <RoutineStep key={step.product_id + '-pm'} step={step} index={i} />
              ))}
            </div>
          </div>

          {/* Layering notes */}
          {regimen?.layering_notes?.length > 0 && (
            <div className="border border-zinc-800 p-5 animate-fade-up">
              <p className="font-[Geologica] text-xs tracking-[0.02em] uppercase text-brand-muted mb-3">
                Layering Notes
              </p>
              <ul className="flex flex-col gap-2">
                {regimen.layering_notes.map((note, i) => (
                  <li key={i} className="font-[Geologica] text-xs text-zinc-400 flex gap-2">
                    <span className="text-brand-accent shrink-0">—</span>
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* QR checkout */}
          <div className="border border-zinc-800 p-6 flex gap-6 items-center mt-auto animate-fade-up">
            <div className="w-20 h-20 bg-brand-warm-dark flex items-center justify-center shrink-0">
              <span className="font-mono text-xs text-zinc-600 text-center leading-tight">
                QR<br />code
              </span>
            </div>
            <div>
              <p className="font-[Geologica] text-sm font-medium mb-1">Shop Your Routine</p>
              <p className="font-[Geologica] text-xs text-zinc-400 leading-relaxed">
                Scan with your phone to add these products to your basket at
                theordinary.com
              </p>
            </div>
          </div>

          <p className="font-[Geologica] text-xs text-zinc-600">{regimen?.disclaimer}</p>
        </section>
      </div>
    </div>
  )
}
