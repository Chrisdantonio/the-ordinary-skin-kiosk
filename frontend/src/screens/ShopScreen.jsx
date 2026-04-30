import { QRCodeSVG } from 'qrcode.react'

const SHOP_URL = 'https://theordinary.com/en-us/category/best-sellers'

export default function ShopScreen({ onBack }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-10">
      <div className="flex flex-col items-center gap-6 max-w-xs text-center">
        <p className="font-[Raleway] text-xs tracking-[0.3em] uppercase text-brand-muted animate-fade-up">
          Your Routine Is Ready
        </p>

        <h1
          className="font-[Raleway] text-4xl font-bold animate-fade-up"
          style={{ animationDelay: '60ms' }}
        >
          Shop Your Routine
        </h1>

        <p
          className="font-[Raleway] text-sm text-zinc-400 leading-relaxed animate-fade-up"
          style={{ animationDelay: '120ms' }}
        >
          Scan to find your recommended products at The Ordinary.
        </p>

        <div
          className="bg-white p-4 animate-fade-up"
          style={{ animationDelay: '200ms' }}
        >
          <QRCodeSVG value={SHOP_URL} size={200} bgColor="#ffffff" fgColor="#000000" />
        </div>

        <div
          className="flex flex-col items-center gap-3 w-full animate-fade-up"
          style={{ animationDelay: '280ms' }}
        >
          <a
            href={SHOP_URL}
            target="_blank"
            rel="noreferrer"
            className="font-[Raleway] bg-brand-offwhite text-brand-black px-14 py-4 text-sm tracking-widest uppercase font-medium hover:bg-white active:scale-95 transition-all duration-300 inline-block"
          >
            Shop Now
          </a>
          <button
            onClick={onBack}
            className="font-[Raleway] border border-zinc-700 px-10 py-3 text-sm tracking-widest uppercase text-brand-offwhite hover:border-zinc-400 transition-colors duration-300"
          >
            ← Back to Results
          </button>
        </div>
      </div>
    </div>
  )
}
