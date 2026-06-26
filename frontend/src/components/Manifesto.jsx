'use client';

import { useEffect, useRef } from 'react';

const LINES = [
  { words: ['REDEFINING', 'IN-CABIN', 'SAFETY.'] },
  { words: ['REAL-TIME', 'EDGE', 'AI.'] },
  { words: ['ZERO', 'CLOUD', 'LATENCY.'] },
];

export default function Manifesto() {
  const sectionRef = useRef(null);
  const wordsRef   = useRef([]);

  useEffect(() => {
    async function init() {
      const { gsap } = await import('gsap');
      const { ScrollTrigger } = await import('gsap/ScrollTrigger');
      gsap.registerPlugin(ScrollTrigger);

      const words = wordsRef.current;
      // Set all words to dark grey initially
      gsap.set(words, { color: '#2a2a2a' });

      // Each word lights up based on scroll position
      words.forEach((word, i) => {
        gsap.to(word, {
          color: i % 3 === 2 ? '#D4F000' : '#F5F5F5',
          duration: 0.01,
          scrollTrigger: {
            trigger: sectionRef.current,
            start: `${10 + (i / words.length) * 70}% center`,
            end:   `${15 + (i / words.length) * 70}% center`,
            scrub: 0.5,
          },
        });
      });
    }
    init();
  }, []);

  let wordIndex = 0;

  return (
    <section
      ref={sectionRef}
      id="system-text"
      style={{
        minHeight: '100vh',
        background: '#050505',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: 'clamp(40px, 8vw, 120px) clamp(24px, 6vw, 80px)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Section label */}
      <p className="section-label" style={{ marginBottom: '48px' }}>/ 01 MISSION</p>

      {LINES.map((line, li) => (
        <div
          key={li}
          className="font-display"
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.2em',
            lineHeight: 0.95,
            marginBottom: '0.05em',
          }}
        >
          {line.words.map((word) => {
            const idx = wordIndex++;
            return (
              <span
                key={word}
                ref={(el) => { wordsRef.current[idx] = el; }}
                style={{
                  fontSize: 'clamp(3rem, 8vw, 10rem)',
                  fontWeight: 700,
                  letterSpacing: '-0.02em',
                  color: '#2a2a2a',
                  willChange: 'color',
                  display: 'inline-block',
                }}
              >
                {word}
              </span>
            );
          })}
        </div>
      ))}

      {/* Decorative neon line */}
      <div
        style={{
          position: 'absolute',
          right: 'clamp(24px, 6vw, 80px)',
          top: '50%',
          transform: 'translateY(-50%)',
          width: '1px',
          height: '40%',
          background: 'linear-gradient(to bottom, transparent, #D4F000, transparent)',
          opacity: 0.4,
        }}
      />
    </section>
  );
}
