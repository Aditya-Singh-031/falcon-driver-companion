'use client';

import { useEffect, useRef } from 'react';

export default function CircuitSignature() {
  const sectionRef = useRef(null);
  const pathsRef   = useRef([]);
  const nodesRef   = useRef([]);

  useEffect(() => {
    async function init() {
      const { gsap }         = await import('gsap');
      const { ScrollTrigger } = await import('gsap/ScrollTrigger');
      gsap.registerPlugin(ScrollTrigger);

      const paths = pathsRef.current.filter(Boolean);
      const nodes = nodesRef.current.filter(Boolean);

      // Measure total path lengths and set up dash arrays
      paths.forEach((path) => {
        const len = path.getTotalLength();
        path.style.strokeDasharray  = len;
        path.style.strokeDashoffset = len;
      });

      gsap.to(paths, {
        strokeDashoffset: 0,
        duration: 2.5,
        ease: 'power2.inOut',
        stagger: 0.15,
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 70%',
          end:   'center center',
          scrub: 1,
        },
      });

      gsap.fromTo(
        nodes,
        { scale: 0, opacity: 0, transformOrigin: 'center center' },
        {
          scale: 1,
          opacity: 1,
          duration: 0.4,
          stagger: 0.12,
          ease: 'back.out(2)',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 60%',
          },
        }
      );
    }
    init();
  }, []);

  const circuitPaths = [
    'M 50 200 L 150 200 L 150 120 L 350 120 L 350 200 L 500 200',
    'M 500 200 L 600 200 L 600 280 L 750 280 L 750 200 L 900 200',
    'M 150 200 L 150 280 L 250 280 L 250 360 L 450 360 L 450 280 L 600 280',
    'M 350 120 L 350 60  L 550 60  L 550 120',
    'M 750 200 L 750 120 L 950 120 L 950 200 L 1050 200',
    'M 250 280 L 250 360 L 450 360',
    'M 900 200 L 1000 200 L 1000 280 L 1150 280',
  ];

  const nodes = [
    [150, 200], [350, 120], [500, 200], [600, 280],
    [750, 200], [750, 120], [250, 360], [950, 200],
    [550,  60], [1050, 200],
  ];

  return (
    <section
      ref={sectionRef}
      id="signature"
      style={{
        minHeight: '80vh',
        background: '#050505',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: 'clamp(40px, 8vw, 120px) clamp(24px, 6vw, 80px)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <p className="section-label" style={{ marginBottom: '48px' }}>/ 04 ARCHITECTURE</p>

      {/* SVG circuit */}
      <div style={{ width: '100%', overflowX: 'hidden', marginBottom: '64px' }}>
        <svg
          viewBox="0 0 1200 420"
          width="100%"
          preserveAspectRatio="xMidYMid meet"
          style={{ overflow: 'visible' }}
          aria-label="Falcon circuit architecture diagram"
        >
          {/* Grid dots */}
          <pattern id="grid" x="0" y="0" width="50" height="50" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="0.8" fill="rgba(255,255,255,0.05)" />
          </pattern>
          <rect width="1200" height="420" fill="url(#grid)" />

          {/* Circuit paths */}
          {circuitPaths.map((d, i) => (
            <path
              key={i}
              ref={(el) => { pathsRef.current[i] = el; }}
              d={d}
              stroke="#00F3FF"
              strokeWidth="1.5"
              fill="none"
              opacity="0.7"
            />
          ))}

          {/* Glow filter */}
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Glowing paths overlay */}
          {circuitPaths.slice(0, 4).map((d, i) => (
            <path
              key={`g${i}`}
              d={d}
              stroke="#00F3FF"
              strokeWidth="1"
              fill="none"
              opacity="0.3"
              filter="url(#glow)"
            />
          ))}

          {/* Nodes */}
          {nodes.map(([cx, cy], i) => (
            <g key={i} ref={(el) => { nodesRef.current[i] = el; }}>
              <circle cx={cx} cy={cy} r="5"  fill="#050505" stroke="#D4F000" strokeWidth="1.5" />
              <circle cx={cx} cy={cy} r="2"  fill="#D4F000" />
              <circle cx={cx} cy={cy} r="10" fill="none"    stroke="rgba(212,240,0,0.2)" strokeWidth="1" />
            </g>
          ))}

          {/* Labels */}
          {[
            [120, 110, 'FACE MESH'],
            [320,  50, 'EAR CALC'],
            [460, 190, 'DROWSY ENGINE'],
            [580, 270, 'DISTRACT ENGINE'],
            [720, 110, 'CONTEXT FUSION'],
            [930, 110, 'ALERT ARBITER'],
            [990, 190, 'FASTAPI'],
          ].map(([x, y, label]) => (
            <text
              key={label}
              x={x} y={y}
              fill="rgba(255,255,255,0.35)"
              style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '9px', letterSpacing: '0.15em' }}
            >
              {label}
            </text>
          ))}
        </svg>
      </div>

      {/* CTA line */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '32px', flexWrap: 'wrap' }}>
        <h2
          className="font-display"
          style={{
            fontSize: 'clamp(2rem, 5vw, 6rem)',
            fontWeight: 700,
            letterSpacing: '-0.02em',
            color: '#F5F5F5',
            lineHeight: 1,
          }}
        >
          ZERO CLOUD.
          <span className="neon neon-glow"> PURE SPEED.</span>
        </h2>
      </div>
    </section>
  );
}
