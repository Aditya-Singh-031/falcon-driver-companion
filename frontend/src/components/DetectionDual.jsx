'use client';

import { useRef, useState } from 'react';

const PANELS = [
  {
    id: 'drowsiness',
    label: 'DROWSINESS',
    accent: '#00F3FF',
    accentAlpha: 'rgba(0,243,255,',
    tagline: 'Microsleep & eye-closure detection via Eye Aspect Ratio + PERCLOS analysis.',
    tags: ['MEDIAPIPE FACEMESH', 'EAR THRESHOLD', 'PERCLOS'],
    json: `{
  "ear": 0.21,
  "perclos": 0.18,
  "microsleep_ms": 0,
  "alert_level": "NOMINAL",
  "confidence": 0.97
}`,
    stats: [
      { label: 'EAR THRESHOLD', value: '< 0.25' },
      { label: 'PERCLOS',       value: '< 15%' },
      { label: 'LATENCY',       value: '11ms' },
    ],
  },
  {
    id: 'distraction',
    label: 'DISTRACTION',
    accent: '#D4F000',
    accentAlpha: 'rgba(212,240,0,',
    tagline: 'Head pose estimation + gaze deviation via EfficientNet-B0 & MediaPipe.',
    tags: ['EFFICIENTNET-B0', 'HEAD POSE', 'GAZE VECTOR'],
    json: `{
  "head_pitch": -3.2,
  "head_yaw": 1.8,
  "gaze_deviation": 0.08,
  "distracted": false,
  "confidence": 0.94
}`,
    stats: [
      { label: 'MODEL',   value: 'EffNet-B0' },
      { label: 'CLASSES', value: '5' },
      { label: 'LATENCY', value: '14ms' },
    ],
  },
];

function Panel({ data, isActive, onHover, onLeave }) {
  return (
    <div
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      style={{
        flex: isActive ? 1.6 : 1,
        position: 'relative',
        padding: 'clamp(32px, 4vw, 64px)',
        transition: 'flex 0.6s cubic-bezier(0.16,1,0.3,1)',
        borderRight: `1px solid rgba(255,255,255,0.05)`,
        overflow: 'hidden',
        cursor: 'default',
        minWidth: 0,
      }}
    >
      {/* Accent bg flash on hover */}
      <div
        style={{
          position: 'absolute', inset: 0,
          background: `${data.accentAlpha}0.04)`,
          opacity: isActive ? 1 : 0,
          transition: 'opacity 0.4s',
          pointerEvents: 'none',
        }}
      />

      {/* Vertical accent line */}
      <div
        style={{
          position: 'absolute', left: 0, top: 0, bottom: 0,
          width: '2px',
          background: data.accent,
          transform: isActive ? 'scaleY(1)' : 'scaleY(0)',
          transformOrigin: 'bottom',
          transition: 'transform 0.5s cubic-bezier(0.16,1,0.3,1)',
          boxShadow: isActive ? `0 0 12px ${data.accent}` : 'none',
        }}
      />

      {/* Label */}
      <h2
        className="font-display"
        style={{
          fontSize: 'clamp(2.5rem, 6vw, 8rem)',
          fontWeight: 700,
          letterSpacing: '-0.02em',
          lineHeight: 0.95,
          color: isActive ? data.accent : 'rgba(245,245,245,0.15)',
          transition: 'color 0.4s',
          marginBottom: '24px',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'clip',
        }}
      >
        {data.label}
      </h2>

      {/* Tagline */}
      <p
        className="font-body"
        style={{
          fontSize: '0.9rem',
          color: '#888',
          maxWidth: '40ch',
          lineHeight: 1.6,
          marginBottom: '32px',
          opacity: isActive ? 1 : 0.4,
          transition: 'opacity 0.4s',
        }}
      >
        {data.tagline}
      </p>

      {/* Tech tags */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '32px' }}>
        {data.tags.map((tag) => (
          <span
            key={tag}
            className="font-mono"
            style={{
              fontSize: '0.6rem',
              letterSpacing: '0.2em',
              padding: '4px 10px',
              border: `1px solid ${data.accentAlpha}0.3)`,
              color: data.accent,
              opacity: isActive ? 1 : 0.3,
              transition: 'opacity 0.4s',
            }}
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Stats row */}
      <div
        style={{
          display: 'flex', gap: '24px', marginBottom: '32px',
          opacity: isActive ? 1 : 0,
          transform: isActive ? 'translateY(0)' : 'translateY(12px)',
          transition: 'opacity 0.4s, transform 0.4s',
        }}
      >
        {data.stats.map((s) => (
          <div key={s.label}>
            <p className="section-label" style={{ marginBottom: '4px' }}>{s.label}</p>
            <p className="font-display" style={{ fontSize: '1.5rem', color: '#F5F5F5' }}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* JSON snippet */}
      <pre
        className="font-mono glass"
        style={{
          fontSize: '0.65rem',
          color: data.accent,
          padding: '16px',
          borderRadius: '4px',
          whiteSpace: 'pre',
          opacity: isActive ? 0.85 : 0,
          transform: isActive ? 'translateY(0)' : 'translateY(16px)',
          transition: 'opacity 0.5s 0.1s, transform 0.5s 0.1s',
          lineHeight: 1.7,
          overflowX: 'auto',
        }}
      >
        {data.json}
      </pre>
    </div>
  );
}

export default function DetectionDual() {
  const [active, setActive] = useState(null);

  return (
    <section
      id="detection"
      style={{
        minHeight: '100vh',
        background: '#0a0a0a',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: 'clamp(40px, 8vw, 120px) 0',
        position: 'relative',
      }}
    >
      {/* Section label */}
      <p className="section-label" style={{ padding: '0 clamp(24px, 6vw, 80px)', marginBottom: '48px' }}>/ 02 DETECTION SYSTEMS</p>

      {/* Two panels */}
      <div style={{ display: 'flex', flex: 1, minHeight: '60vh' }}>
        {PANELS.map((panel) => (
          <Panel
            key={panel.id}
            data={panel}
            isActive={active === panel.id}
            onHover={() => setActive(panel.id)}
            onLeave={() => setActive(null)}
          />
        ))}
      </div>

      {/* Bottom hint */}
      <p
        className="section-label"
        style={{ padding: '24px clamp(24px, 6vw, 80px) 0', opacity: 0.4 }}
      >
        HOVER TO INSPECT
      </p>
    </section>
  );
}
