/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,jsx}',
    './src/components/**/*.{js,jsx}',
    './src/app/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        'neon-yellow':  '#D4F000',
        'neon-cyan':    '#00F3FF',
        'pitch-black':  '#050505',
        'dark-charcoal':'#111111',
        'ash':          '#AAAAAA',
        'stark-white':  '#F0F0F0',
      },
      fontFamily: {
        display: ['var(--font-display)', 'Impact', 'Arial Black', 'sans-serif'],
        body:    ['var(--font-body)',    'Inter',  'system-ui',   'sans-serif'],
        mono:    ['var(--font-mono)',    'JetBrains Mono', 'monospace'],
      },
      animation: {
        'hud-pulse':    'hudPulse 2s ease-in-out infinite',
        'scanline':     'scanline 3s linear infinite',
        'blink-dot':    'blinkDot 1.2s step-start infinite',
      },
      keyframes: {
        hudPulse: {
          '0%,100%': { opacity: '0.6' },
          '50%':     { opacity: '1' },
        },
        scanline: {
          '0%':   { top: '-4px' },
          '100%': { top: '100%' },
        },
        blinkDot: {
          '0%,100%': { opacity: '1' },
          '50%':     { opacity: '0' },
        },
      },
    },
  },
  plugins: [],
};
