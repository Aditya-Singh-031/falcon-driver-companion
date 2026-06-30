'use client';

import { useEffect, useRef } from 'react';

const CARDS = [
  {
    id: 'facemesh', num: '01', title: 'MediaPipe FaceMesh', sub: 'LANDMARK DETECTION', accent: '#00F3FF',
    body: '468 3D facial landmarks at 30+ fps on CPU. Drives EAR computation and PERCLOS analysis for drowsiness state.',
    metrics: [['LANDMARKS', '468'], ['FPS', '35+'], ['LATENCY', '8ms']], logo: 'MEDIAPIPE',
  },
  {
    id: 'efficientnet', num: '02', title: 'EfficientNet-B0', sub: 'DISTRACTION CLASSIFIER', accent: '#D4F000',
    body: 'Lightweight CNN fine-tuned on in-cabin datasets. Classifies 5 distraction states with 94% top-1 accuracy.',
    metrics: [['ACCURACY', '94%'], ['PARAMS', '5.3M'], ['LATENCY', '14ms']], logo: 'PYTORCH',
  },
  {
    id: 'context', num: '03', title: 'Context Engine', sub: 'ALERT ARBITRATION', accent: '#FF6B35',
    body: 'Multi-signal fusion layer. Combines drowsiness score + distraction class + temporal context to minimise false alerts.',
    metrics: [['FALSE POS', '< 2%'], ['WINDOW', '3s'], ['SIGNALS', '4']], logo: 'FALCON',
  },
  {
    id: 'fastapi', num: '04', title: 'FastAPI Backend', sub: 'INFERENCE SERVER', accent: '#00C896',
    body: 'Async REST API serving inference results at sub-20ms p99. WebSocket stream for live frame delivery to dashboard.',
    metrics: [['P99', '< 20ms'], ['ENDPOINT', '/infer'], ['WS', 'LIVE']], logo: 'FASTAPI',
  },
  {
    id: 'streamlit', num: '05', title: 'Streamlit Cockpit', sub: 'MONITORING DASHBOARD', accent: '#FF4B4B',
    body: 'Live webcam inference, session telemetry, alert timeline and log export. Full cockpit embedded below.',
    metrics: [['PORT', '8501'], ['FPS', 'LIVE'], ['CHARTS', 'REALTIME']], logo: 'STREAMLIT',
  },
];

function Card({ data }) {
  return (
    <div style={{ flexShrink: 0, width: 'clamp(280px, 28vw, 380px)', marginRight: '24px' }}>
      <div style={{
        height: '480px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)',
        padding: '36px 32px', position: 'relative', overflow: 'hidden'
      }}>
        <p className="font-display" style={{ fontSize: '4rem', fontWeight: 700, color: 'rgba(255,255,255,0.04)', lineHeight: 1, marginBottom: '16px' }}>{data.num}</p>
        <span className="font-mono" style={{ fontSize: '0.6rem', letterSpacing: '0.2em', color: data.accent, border: `1px solid ${data.accent}44`, padding: '3px 8px', display: 'inline-block', marginBottom: '20px' }}>{data.logo}</span>
        <h3 className="font-display" style={{ fontSize: 'clamp(1.4rem, 2vw, 2rem)', fontWeight: 700, color: '#F5F5F5', marginBottom: '6px', lineHeight: 1.1 }}>{data.title}</h3>
        <p className="section-label" style={{ marginBottom: '20px', color: data.accent }}>{data.sub}</p>
        <p className="font-body" style={{ fontSize: '0.85rem', color: '#777', lineHeight: 1.7, marginBottom: '32px' }}>{data.body}</p>
        <div style={{ display: 'flex', gap: '20px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '20px' }}>
          {data.metrics.map(([k, v]) => (
            <div key={k}>
              <p className="section-label" style={{ fontSize: '0.55rem', marginBottom: '4px' }}>{k}</p>
              <p className="font-display" style={{ fontSize: '1.1rem', color: data.accent }}>{v}</p>
            </div>
          ))}
        </div>
        <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: '2px', background: `linear-gradient(90deg, transparent, ${data.accent}, transparent)`, opacity: 0.5 }} />
      </div>
    </div>
  );
}

export default function TechCarousel() {
  const sectionRef = useRef(null);
  const trackRef = useRef(null);

  useEffect(() => {
    let ctx; 

    async function init() {
      const { gsap } = await import('gsap');
      const { ScrollTrigger } = await import('gsap/ScrollTrigger');
      gsap.registerPlugin(ScrollTrigger);

      const track = trackRef.current;
      const section = sectionRef.current;
      if (!track || !section) return;

      ctx = gsap.context(() => {
        // Dynamically calculate the exact width we need to move
        const getScrollAmount = () => {
          let trackWidth = track.scrollWidth;
          return -(trackWidth - window.innerWidth + 80); // 80px buffer
        };

        gsap.to(track, {
          x: getScrollAmount,
          ease: 'none',
          scrollTrigger: {
            trigger: section,
            start: 'top top',
            end: () => `+=${track.scrollWidth - window.innerWidth + 80}`, // Exact end point removes the black void
            pin: true,
            scrub: 1,
            invalidateOnRefresh: true, // Recalculates sizes instantly if window resizes
          },
        });
      }, sectionRef);
    }
    
    init();
    return () => ctx && ctx.revert(); 
  }, []);

  return (
    // Removed 300vh and sticky. GSAP pin handles it dynamically now.
    <section ref={sectionRef} id="tech" style={{ background: '#050505', position: 'relative', overflow: 'hidden' }}>
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', padding: '0 clamp(24px, 6vw, 80px)', marginBottom: '48px', flexShrink: 0 }}>
          <div>
            <p className="section-label" style={{ marginBottom: '8px' }}>/ 03 TECHNOLOGY</p>
            <h2 className="font-display" style={{ fontSize: 'clamp(2rem, 5vw, 5rem)', fontWeight: 700, letterSpacing: '-0.02em', color: '#F5F5F5', lineHeight: 1 }}>THE STACK</h2>
          </div>
          <p className="section-label" style={{ opacity: 0.5 }}>SCROLL →</p>
        </div>

        <div style={{ paddingLeft: 'clamp(24px, 6vw, 80px)', flexShrink: 0 }}>
          {/* CRITICAL FIX: Added width: 'max-content' here so Cards 1 & 2 don't get squished off-screen */}
          <div ref={trackRef} style={{ display: 'flex', alignItems: 'flex-start', width: 'max-content', willChange: 'transform' }}>
            {CARDS.map((card) => <Card key={card.id} data={card} />)}
            {/* Reduced spacer width to stop empty scrolling at the end */}
            <div style={{ flexShrink: 0, width: '10vw' }} /> 
          </div>
        </div>

      </div>
    </section>
  );
}