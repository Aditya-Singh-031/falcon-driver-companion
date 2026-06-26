/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        falcon: {
          black: '#050505',
          charcoal: '#111111',
          surface: '#1a1a1a',
          border: 'rgba(255,255,255,0.08)',
          neon: '#D4F000',
          cyan: '#00F3FF',
          white: '#F5F5F5',
          muted: '#888888',
          faint: '#444444',
        },
      },
      fontFamily: {
        display: ['var(--font-display)', 'Impact', 'sans-serif'],
        body: ['var(--font-body)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      fontSize: {
        '10vw': '10vw',
        '12vw': '12vw',
        '15vw': '15vw',
        '18vw': '18vw',
        '22vw': '22vw',
      },
      letterSpacing: {
        tightest: '-0.05em',
        widest: '0.3em',
      },
      transitionTimingFunction: {
        expo: 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
};
