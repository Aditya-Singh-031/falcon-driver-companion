'use client';

import { useEffect, useRef, useState } from 'react';

const BACKEND_URL  = process.env.NEXT_PUBLIC_BACKEND_URL  || 'http://localhost:8000';
const DASHBOARD_URL = process.env.NEXT_PUBLIC_DASHBOARD_URL || 'http://localhost:8501';

export default function CockpitScreen() {
  const sectionRef = useRef(null);
  const [backendOk, setBackendOk] = useState(null);

  // Ping backend health
  useEffect(() => {
    async function ping() {
      try {
        const r = await fetch(`${BACKEND_URL}/health`, { signal: AbortSignal.timeout(3000) });
        setBackendOk(r.ok);
      } catch {
        setBackendOk(false);
      }
    }
    ping();
    const id = setInterval(ping, 10000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    async function init() {
      const { gsap }         = await import('gsap');
      const { ScrollTrigger } = await import('gsap/ScrollTrigger');
      gsap.registerPlugin(ScrollTrigger);
      gsap.fromTo(
        sectionRef.current,
        { opacity: 0, y: 60 },
        {
          opacity: 1, y: 0, duration: 1, ease: 'expo.out',
          scrollTrigger: { trigger: sectionRef.current, start: 'top 80%' },
        }
      );
    }
    init();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="cockpit"
      style={{
        minHeight: '100vh',
        background: '#080808',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: 'clamp(40px, 8vw, 120px) clamp(24px, 6vw, 80px)',
        position: 'relative',
      }}
    >
      <p className="section-label" style={{ marginBottom: '16px' }}>/ 05 LIVE COCKPIT</p>
      <h2
        className="font-display"
        style={{
          fontSize: 'clamp(2.5rem, 6vw, 7rem)',
          fontWeight: 700,
          letterSpacing: '-0.02em',
          color: '#F5F5F5',
          lineHeight: 0.95,
          marginBottom: '48px',
        }}
      >
        IN-CABIN
        <br />
        <span className="cyan cyan-glow">MONITOR</span>
      </h2>

      {/* System status row */}
      <div style={{ display: 'flex', gap: '24px', marginBottom: '32px', flexWrap: 'wrap' }}>
        <div className="glass" style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span
            style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: backendOk === null ? '#888' : backendOk ? '#D4F000' : '#ff4444',
              boxShadow: backendOk ? '0 0 8px #D4F000' : 'none',
              flexShrink: 0,
            }}
          />
          <span className="font-mono" style={{ fontSize: '0.65rem', letterSpacing: '0.15em', color: '#888' }}>
            BACKEND {backendOk === null ? 'CHECKING…' : backendOk ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>
        <a
          href={`${BACKEND_URL}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="glass font-mono"
          style={{
            padding: '12px 20px', fontSize: '0.65rem',
            letterSpacing: '0.15em', color: '#00F3FF',
            textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px',
          }}
        >
          API DOCS ↗
        </a>
        <a
          href={DASHBOARD_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="font-mono"
          style={{
            padding: '12px 24px', fontSize: '0.65rem',
            letterSpacing: '0.15em',
            background: '#D4F000', color: '#050505',
            textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px',
          }}
        >
          OPEN DASHBOARD ↗
        </a>
      </div>

      {/* Dashboard iframe — the real Streamlit cockpit */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          maxWidth: '1100px',
          borderRadius: '4px',
          overflow: 'hidden',
          border: '1px solid rgba(0,243,255,0.15)',
          boxShadow: '0 0 60px rgba(0,243,255,0.06)',
        }}
      >
        {/* Dashboard screen bezel top bar */}
        <div
          style={{
            background: '#0d0d0d',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ff5f57' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#febc2e' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#28c840' }} />
          <span className="font-mono" style={{ fontSize: '0.6rem', color: '#444', marginLeft: '12px', letterSpacing: '0.15em' }}>
            FALCON COCKPIT · {DASHBOARD_URL}
          </span>
        </div>

        {backendOk === false ? (
          <div
            style={{
              height: '600px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#0a0a0a',
              gap: '16px',
            }}
          >
            <div style={{ width: '40px', height: '40px' }}>
              <svg viewBox="0 0 40 40" fill="none">
                <circle cx="20" cy="20" r="18" stroke="#ff4444" strokeWidth="1.5" />
                <line x1="13" y1="13" x2="27" y2="27" stroke="#ff4444" strokeWidth="1.5" />
                <line x1="27" y1="13" x2="13" y2="27" stroke="#ff4444" strokeWidth="1.5" />
              </svg>
            </div>
            <p className="font-display" style={{ fontSize: '1.5rem', color: '#F5F5F5' }}>BACKEND OFFLINE</p>
            <p className="font-body" style={{ fontSize: '0.85rem', color: '#666', textAlign: 'center', maxWidth: '36ch' }}>
              Start the FastAPI backend on port 8000, then reload.
            </p>
            <code className="font-mono" style={{ fontSize: '0.7rem', color: '#D4F000', background: 'rgba(212,240,0,0.06)', padding: '8px 16px' }}>
              cd backend && uvicorn main:app --reload
            </code>
          </div>
        ) : (
          <iframe
            src={DASHBOARD_URL}
            title="Falcon Cockpit Dashboard"
            width="100%"
            height="700"
            style={{ display: 'block', border: 'none', background: '#050505' }}
            allow="camera; microphone"
          />
        )}
      </div>

      {/* Decorative background text */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          bottom: '-40px',
          right: '-20px',
          fontSize: 'clamp(6rem, 18vw, 18rem)',
          fontFamily: 'var(--font-display), Impact, sans-serif',
          fontWeight: 700,
          color: 'rgba(255,255,255,0.015)',
          letterSpacing: '-0.02em',
          lineHeight: 1,
          userSelect: 'none',
          pointerEvents: 'none',
        }}
      >
        LIVE
      </div>
    </section>
  );
}
