/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          // Verified against theordinary.com production CSS (2025-04)
          black:      '#171616', // primary kiosk background
          'warm-dark':'#212020', // elevated surface / card panels
          offwhite:   '#f3f2f0', // primary text, primary button fill
          'warm-white':'#e1ded9',// warm dividers, inactive states
          muted:      '#8e8e8e', // labels, captions, secondary text
          mid:        '#cfcbc7', // metadata, pricing
          accent:     '#e1ded9', // application notes, subtle highlights
        },
      },
      fontFamily: {
        // Geologica is The Ordinary's actual brand typeface (variable font)
        sans:    ['Geologica', 'system-ui', 'sans-serif'],
        display: ['Raleway', 'system-ui', 'sans-serif'],
        mono:    ['ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      keyframes: {
        'fade-up': {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'scan-line': {
          '0%':   { transform: 'translateY(0%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        'pulse-muted': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.3' },
        },
      },
      animation: {
        // cubic-bezier(.645,.045,.355,1) = brand easing from production CSS
        'fade-up':     'fade-up 0.5s cubic-bezier(.645,.045,.355,1) both',
        'fade-in':     'fade-in 0.3s cubic-bezier(.645,.045,.355,1) both',
        'scan-line':   'scan-line 2s ease-in-out infinite alternate',
        'pulse-muted': 'pulse-muted 1.5s ease-in-out infinite',
      },
      transitionTimingFunction: {
        brand: 'cubic-bezier(.645,.045,.355,1)',
      },
    },
  },
  plugins: [],
}
