'use client';

import { useEffect, useRef } from 'react';

const NAV_ITEMS = [
  { label: 'System', href: '#system' },
  { label: 'Detection', href: '#detection' },
  { label: 'Technology', href: '#tech' },
  { label: 'Cockpit', href: '#cockpit' },
];

export default function Navbar() {
  const navRef  = useRef(null);
  const lineRef = useRef(null);

  useEffect(() => {
    let lastScroll = 0;
    const onScroll = () => {
      const current = window.scrollY;
      if (!navRef.current) return;
      if (current > 80 && current > lastScroll) {
        navRef.current.style.transform = 'translateY(-100%)';
      } else {
        navRef.current.style.transform = 'translateY(0)';
      }
      lastScroll = current;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav
      ref={navRef}
      className="fixed top-0 left-0 right-0 z-50"
      style={{
        transition: 'transform 0.4s cubic-bezier(0.16,1,0.3,1)',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        background: 'rgba(5,5,5,0.7)',
      }}
    >
      <div
        className="flex items-center justify-between px-8"
        style={{ height: '64px', maxWidth: '1600px', margin: '0 auto' }}
      >
        {/* Logo */}
        <a href="#" className="flex items-center gap-3 group" style={{ textDecoration: 'none' }}>
          {/* Inline SVG falcon logo */}
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-label="Falcon logo">
            <polygon points="16,2 28,12 24,30 8,30 4,12" stroke="#D4F000" strokeWidth="1.5" fill="none" />
            <polygon points="16,8 22,14 20,24 12,24 10,14" fill="#D4F000" opacity="0.15" />
            <line x1="16" y1="2" x2="16" y2="30" stroke="#D4F000" strokeWidth="0.75" opacity="0.5" />
          </svg>
          <span
            className="font-display text-falcon-white"
            style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '0.15em' }}
          >
            FALCON
          </span>
        </a>

        {/* Nav links */}
        <ul className="hidden md:flex items-center gap-8" role="list">
          {NAV_ITEMS.map((item) => (
            <li key={item.href}>
              <a
                href={item.href}
                className="section-label hover:text-falcon-neon"
                style={{ transition: 'color 0.2s', textDecoration: 'none', color: 'inherit' }}
              >
                {item.label}
              </a>
            </li>
          ))}
        </ul>

        {/* CTA */}
        <a
          href="#cockpit"
          className="hidden md:flex items-center gap-2 font-mono"
          style={{
            fontSize: '0.7rem',
            letterSpacing: '0.2em',
            color: '#050505',
            background: '#D4F000',
            padding: '8px 20px',
            textDecoration: 'none',
            transition: 'opacity 0.2s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.85')}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
        >
          LAUNCH ▶
        </a>
      </div>
      <div ref={lineRef} style={{ height: '1px', background: 'rgba(212,240,0,0.0)' }} />
    </nav>
  );
}
