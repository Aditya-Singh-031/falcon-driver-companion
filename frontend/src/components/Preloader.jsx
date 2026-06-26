'use client';

import { useEffect, useRef, useState } from 'react';

export default function Preloader() {
  const [done, setDone] = useState(false);
  const containerRef = useRef(null);
  const progressRef  = useRef(null);
  const falRef       = useRef(null);
  const conRef       = useRef(null);
  const pctRef       = useRef(null);

  useEffect(() => {
    if (done) return;
    let progress = 0;
    let gsap, tl;

    async function run() {
      const mod = await import('gsap');
      gsap = mod.gsap;

      // Initial: letters offscreen
      gsap.set(falRef.current, { x: '-120%', opacity: 0 });
      gsap.set(conRef.current, { x:  '120%', opacity: 0 });

      tl = gsap.timeline({
        onComplete: () => {
          gsap.to(containerRef.current, {
            yPercent: -105,
            duration: 1.0,
            ease: 'power4.inOut',
            onComplete: () => setDone(true),
          });
        },
      });

      tl.to(falRef.current, { x: '0%', opacity: 1, duration: 0.7, ease: 'expo.out' }, 0)
        .to(conRef.current, { x: '0%', opacity: 1, duration: 0.7, ease: 'expo.out' }, 0);

      // Progress bar
      const interval = setInterval(() => {
        progress = Math.min(progress + Math.random() * 12, 100);
        if (progressRef.current) progressRef.current.style.width = progress + '%';
        if (pctRef.current)  pctRef.current.textContent = Math.floor(progress) + '%';
        if (progress >= 100) {
          clearInterval(interval);
          setTimeout(() => tl.play(), 200);
        }
      }, 60);

      tl.pause();
    }
    run();
  }, [done]);

  if (done) return null;

  return (
    <div ref={containerRef} className="preloader">
      {/* Main letters */}
      <div className="flex items-center select-none" style={{ gap: '0.04em' }}>
        <span
          ref={falRef}
          className="font-display text-falcon-white"
          style={{ fontSize: 'clamp(5rem, 18vw, 18rem)', fontWeight: 700, lineHeight: 0.9, letterSpacing: '-0.02em' }}
        >
          FAL
        </span>
        <span
          ref={conRef}
          className="font-display neon neon-glow"
          style={{ fontSize: 'clamp(5rem, 18vw, 18rem)', fontWeight: 700, lineHeight: 0.9, letterSpacing: '-0.02em' }}
        >
          CON
        </span>
      </div>

      {/* Tagline */}
      <p
        className="section-label absolute"
        style={{ top: '50%', marginTop: '8rem', left: '50%', transform: 'translateX(-50%)', whiteSpace: 'nowrap' }}
      >
        EDGE AI IN-CABIN COMPANION
      </p>

      {/* Progress */}
      <div className="preloader-progress" ref={progressRef} />
      <span
        ref={pctRef}
        className="font-mono absolute text-falcon-neon"
        style={{ bottom: '48px', right: '40px', fontSize: '0.7rem', letterSpacing: '0.1em' }}
      >
        0%
      </span>
    </div>
  );
}
