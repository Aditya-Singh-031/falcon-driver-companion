'use client';

export default function HudOverlay() {
  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>

      {/* Face bounding box — centered */}
      <div
        style={{
          position: 'absolute',
          top: '20%', left: '38%',
          width: '24%', height: '38%',
          pointerEvents: 'none',
        }}
      >
        <div className="hud-corner hud-corner--tl" />
        <div className="hud-corner hud-corner--tr" />
        <div className="hud-corner hud-corner--bl" />
        <div className="hud-corner hud-corner--br" />
        {/* Scanline */}
        <div className="scanline" />
        {/* Center crosshair */}
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%,-50%)',
          width: '12px', height: '12px',
          border: '1px solid rgba(0,243,255,0.5)',
          borderRadius: '50%',
          opacity: 0,
        }} className="hud-corner" />
      </div>

      {/* Face mesh grid lines */}
      <div
        style={{
          position: 'absolute',
          top: '23%', left: '40%',
          width: '20%', height: '32%',
          opacity: 0,
        }}
      >
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className="hud-mesh-line"
            style={{
              position: 'absolute',
              left: 0, right: 0,
              top: `${(i / 7) * 100}%`,
              height: '1px',
              background: `rgba(0,243,255,${0.15 - i * 0.01})`,
              transformOrigin: 'left',
              transform: 'scaleX(0)',
            }}
          />
        ))}
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={`v${i}`}
            className="hud-mesh-line"
            style={{
              position: 'absolute',
              top: 0, bottom: 0,
              left: `${(i / 5) * 100}%`,
              width: '1px',
              background: `rgba(0,243,255,0.12)`,
              transformOrigin: 'top',
              transform: 'scaleX(0)',
            }}
          />
        ))}
      </div>

      {/* Left data panel */}
      <div
        className="hud-panel"
        style={{
          position: 'absolute',
          top: '22%', left: '6%',
          opacity: 0,
          transform: 'translateX(-30px)',
        }}
      >
        <div
          style={{
            background: 'rgba(0,243,255,0.06)',
            border: '1px solid rgba(0,243,255,0.2)',
            padding: '12px 16px',
            minWidth: '160px',
          }}
        >
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', color: '#00F3FF', letterSpacing: '0.2em', marginBottom: '8px' }}>DROWSINESS</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <div style={{ flex: 1, height: '2px', background: 'rgba(0,243,255,0.2)' }}>
              <div style={{ width: '18%', height: '100%', background: '#00F3FF' }} />
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: '#F5F5F5' }}>0.18</span>
          </div>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.55rem', color: '#888' }}>EAR: 0.31 · STATUS: ALERT</p>
        </div>
      </div>

      {/* Right data panel */}
      <div
        className="hud-panel"
        style={{
          position: 'absolute',
          top: '22%', right: '6%',
          opacity: 0,
          transform: 'translateX(30px)',
        }}
      >
        <div
          style={{
            background: 'rgba(212,240,0,0.06)',
            border: '1px solid rgba(212,240,0,0.2)',
            padding: '12px 16px',
            minWidth: '160px',
          }}
        >
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', color: '#D4F000', letterSpacing: '0.2em', marginBottom: '8px' }}>DISTRACTION</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <div style={{ flex: 1, height: '2px', background: 'rgba(212,240,0,0.2)' }}>
              <div style={{ width: '8%', height: '100%', background: '#D4F000' }} />
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: '#F5F5F5' }}>0.08</span>
          </div>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.55rem', color: '#888' }}>HEAD POSE: FORWARD</p>
        </div>
      </div>

      {/* Top status bar */}
      <div
        className="hud-panel"
        style={{
          position: 'absolute',
          top: '10%',
          left: '50%',
          transform: 'translate(-50%, 0) translateX(0px)',
          opacity: 0,
          textAlign: 'center',
        }}
      >
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', color: '#D4F000', letterSpacing: '0.3em' }}>● FALCON ACTIVE · 12ms · 83fps</p>
      </div>
    </div>
  );
}
