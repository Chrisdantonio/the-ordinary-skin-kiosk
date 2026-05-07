/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          black:      '#000000', // pure black — headlines, primary text
          offwhite:   '#f7f5f3', // near-white — subtle hover fills
          white:      '#ffffff', // page background
          'warm-dark':'#1a1a1a', // near-black — dark surfaces (camera bg)
          'warm-white':'#e8e4df',// warm light gray — dividers, borders
          muted:      '#767676', // medium gray — labels, captions
          mid:        '#b0aba6', // light gray — metadata, pricing
          accent:     '#9b9590', // warm gray — application notes
        },
      },
      fontFamily: {
        // Raleway is the official brand typeface (all type — official style guide)
        sans:    ['Raleway', 'system-ui', 'sans-serif'],
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
