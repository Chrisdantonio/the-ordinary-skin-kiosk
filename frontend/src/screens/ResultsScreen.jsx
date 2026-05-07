import { useState } from 'react'

const PRODUCT_IMAGE = {
  'hyaluronic-acid-2-b5':                '/products/hyaluronic.jpg',
  'niacinamide-10-zinc-1':               '/products/niacinamide.jpg',
  'retinol-0-5-squalane':                '/products/retinol.jpg',
  'aha-30-bha-2-peeling-solution':       '/products/aha_bha.jpg',
  'caffeine-solution-5-egcg':            '/products/caffeine.jpg',
  'vitamin-c-suspension-23':             '/products/vitamin_c.jpg',
  'squalane-cleanser':                   '/products/squalane_cleanser.jpg',
  'natural-moisturizing-factors-ha':     '/products/nmf.jpg',
  'multi-peptide-ha-serum':              '/products/buffet.jpg',
  'glycolic-acid-7-toning-solution':     '/products/glycolic.jpg',
  'salicylic-acid-2-anhydrous-solution': '/products/salicylic.jpg',
  'multi-peptide-copper-peptides-1':     '/products/multi_peptide.jpg',
}

const SEVERITY_LABEL = { mild: 'Mild', moderate: 'Moderate', pronounced: 'Pronounced' }

const CONCERN_LABEL = {
  dehydration:         'Dehydration',
  oiliness:            'Oiliness',
  redness:             'Redness',
  enlarged_pores:      'Enlarged Pores',
  uneven_tone:         'Uneven Tone',
  hyperpigmentation:   'Hyperpigmentation',
  dark_circles:        'Dark Circles',
  dullness:            'Dullness',
  fine_lines:          'Fine Lines',
  rough_texture:       'Rough Texture',
  occasional_breakout: 'Occasional Breakout',
  congestion:          'Congestion',
  flaking:             'Flaking',
  visible_sensitivity: 'Visible Sensitivity',
}

function ConcernSeverityBar({ severity }) {
  const filled = { mild: 1, moderate: 2, pronounced: 3 }[severity] ?? 0
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3].map(i => (
        <div key={i} className={`h-1 w-8 ${i <= filled ? 'bg-black' : 'bg-zinc-200'}`} />
      ))}
    </div>
  )
}

function ProductCard({ step }) {
  const [open, setOpen] = useState(false)
  const imgSrc = PRODUCT_IMAGE[step.product_id]

  return (
    <>
      <div className="flex flex-col items-center gap-3 animate-fade-up">
        {/* Large product image — only render if image exists */}
        {imgSrc && (
          <div className="w-full aspect-square bg-zinc-50 flex items-center justify-center p-4">
            <img src={imgSrc} alt={step.name} className="w-full h-full object-contain" />
          </div>
        )}

        {/* Product name */}
        <p className="font-[Raleway] text-xs font-medium text-black text-center leading-snug px-1">
          {step.name}
        </p>

        {/* CTA */}
        <button
          onClick={() => setOpen(true)}
          className="font-[Raleway] w-full border border-black text-xs tracking-[0.15em] uppercase text-black py-2.5 hover:bg-black hover:text-white transition-colors duration-200"
        >
          Read More
        </button>
      </div>

      {/* Detail drawer — slides up from bottom */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center px-6"
          onClick={() => setOpen(false)}
        >
          <div
            className="bg-white w-full max-w-lg px-10 py-10 animate-fade-up"
            onClick={e => e.stopPropagation()}
          >
            <p className="font-[Raleway] text-xs tracking-[0.25em] uppercase text-black mb-2">
              How to use
            </p>
            <h3 className="font-[Raleway] text-2xl font-light text-black mb-6">
              {step.name}
            </h3>
            <p className="font-[Raleway] text-sm text-black leading-relaxed mb-3">
              {step.rationale}
            </p>
            <p className="font-[Raleway] text-sm text-black leading-relaxed mb-8">
              {step.application}
            </p>
            <button
              onClick={() => setOpen(false)}
              className="font-[Raleway] bg-black text-white px-10 py-3 text-xs tracking-[0.2em] uppercase hover:bg-zinc-900 transition-colors duration-200"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  )
}

function RoutineSection({ label, steps }) {
  if (!steps?.length) return null
  const visible = steps.filter(s => PRODUCT_IMAGE[s.product_id]).slice(0, 3)
  if (!visible.length) return null
  return (
    <div className="animate-fade-up">
      <p className="font-[Raleway] text-xs tracking-[0.25em] uppercase text-black mb-6">
        {label}
      </p>
      <div className="grid grid-cols-3 gap-5">
        {visible.map(step => (
          <ProductCard key={step.product_id} step={step} />
        ))}
      </div>
    </div>
  )
}

export default function ResultsScreen({ skinVision, regimen, onRestart, onNext }) {
  return (
    <div className="min-h-screen flex flex-col bg-white">

      {/* Header */}
      <header className="relative flex items-center justify-center px-10 py-8 border-b border-zinc-200 shrink-0 animate-fade-in">
        <h1 className="font-[Raleway] text-4xl font-light tracking-[0.4em] uppercase text-black">
          The Ordinary
        </h1>
        <button
          onClick={onRestart}
          className="absolute right-10 font-[Raleway] text-xs tracking-[0.02em] uppercase text-black hover:underline transition-all duration-200"
        >
          New Analysis
        </button>
      </header>

      {/* Skin profile — top, equal columns */}
      <section className="px-10 py-8 border-b border-zinc-200 shrink-0 animate-fade-up">
        <p className="font-[Raleway] text-xs tracking-[0.25em] uppercase text-black mb-6">
          Your Skin Profile
        </p>
        <div className="flex gap-4">
          {skinVision?.top_concerns?.map(concern => (
            <div
              key={concern.type}
              className="flex-1 flex flex-col items-center justify-center gap-3 border border-black py-6 px-3 text-center"
            >
              <span className="font-[Raleway] text-base font-medium text-black leading-tight">
                {CONCERN_LABEL[concern.type] ?? concern.type}
              </span>
              <span className="font-[Raleway] text-sm text-black">
                {SEVERITY_LABEL[concern.severity]}
              </span>
              <ConcernSeverityBar severity={concern.severity} />
            </div>
          ))}
        </div>
        <p className="font-[Raleway] text-xs text-black mt-5 leading-relaxed">
          {skinVision?.disclaimer}
        </p>
      </section>

      {/* Product routines — scrollable */}
      <div className="flex-1 overflow-auto px-10 py-8 flex flex-col gap-12">
        <RoutineSection label="Morning Routine" steps={regimen?.am_routine} />
        <RoutineSection label="Evening Routine" steps={regimen?.pm_routine} />

        {regimen?.layering_notes?.length > 0 && (
          <div className="border border-zinc-200 p-5 animate-fade-up">
            <p className="font-[Raleway] text-xs tracking-[0.2em] uppercase text-black mb-3">
              Layering Notes
            </p>
            <ul className="flex flex-col gap-2">
              {regimen.layering_notes.map((note, i) => (
                <li key={i} className="font-[Raleway] text-xs text-black flex gap-2">
                  <span className="shrink-0">—</span>
                  {note}
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="font-[Raleway] text-xs text-black">{regimen?.disclaimer}</p>
      </div>

      {/* Footer */}
      <footer className="px-10 py-6 border-t border-zinc-200 flex justify-end shrink-0 animate-fade-up">
        <button
          onClick={onNext}
          className="font-[Raleway] bg-black text-white px-14 py-4 text-sm tracking-widest uppercase font-medium hover:bg-zinc-900 active:scale-95 transition-all duration-300"
        >
          Next
        </button>
      </footer>
    </div>
  )
}
