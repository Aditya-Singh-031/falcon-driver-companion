import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'neon-yellow': '#D4F000',
        'neon-cyan':   '#00F3FF',
        'bg-void':     '#050505',
        'bg-panel':    '#111111',
        'bg-surface':  '#1a1a1a',
        'text-primary':'#F0F0F0',
        'text-muted':  '#888888',
        'text-faint':  '#444444',
      },
      fontFamily: {
        display: ['var(--font-display)', 'Impact', 'Arial Black', 'sans-serif'],
        body:    ['var(--font-body)',    'Inter',  'system-ui',   'sans-serif'],
        mono:    ['var(--font-mono)',    'JetBrains Mono', 'monospace'],
      },
      animation: {
        'scanline':    'scanline 3s linear infinite',
        'pulse-neon':  'pulse-neon 2s ease-in-out infinite',
        'hud-draw':    'hud-draw 1.2s ease forwards',
        'fade-up':     'fade-up 0.8s cubic-bezier(0.16,1,0.3,1) forwards',
        'glitch':      'glitch 0.4s steps(2) infinite',
      },
      keyframes: {
        scanline: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        'pulse-neon': {
          '0%,100%': { opacity: '1',   filter: 'drop-shadow(0 0 8px #D4F000)' },
          '50%':     { opacity: '0.7', filter: 'drop-shadow(0 0 20px #D4F000)' },
        },
        'hud-draw': {
          from: { strokeDashoffset: '1000' },
          to:   { strokeDashoffset: '0' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(40px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        glitch: {
          '0%':  { clip: 'rect(0,9999px,2px,0)',  transform: 'skew(0.5deg)' },
          '25%': { clip: 'rect(40px,9999px,42px,0)', transform: 'skew(-0.3deg)' },
          '50%': { clip: 'rect(10px,9999px,12px,0)', transform: 'skew(0.1deg)' },
          '75%': { clip: 'rect(60px,9999px,62px,0)', transform: 'skew(0.4deg)' },
          '100%':{ clip: 'rect(0,9999px,2px,0)',  transform: 'skew(0deg)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
