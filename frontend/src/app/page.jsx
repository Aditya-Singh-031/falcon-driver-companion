'use client';

import { useEffect } from 'react';
import dynamic from 'next/dynamic';
import Preloader from '@/components/Preloader';
import Navbar from '@/components/Navbar';
import Manifesto from '@/components/Manifesto';
import DetectionDual from '@/components/DetectionDual';
import TechCarousel from '@/components/TechCarousel';
import CircuitSignature from '@/components/CircuitSignature';
import CockpitScreen from '@/components/CockpitScreen';
import Cursor from '@/components/Cursor';

// Hero with R3F must be client-only (no SSR)
const HeroScene = dynamic(() => import('@/components/HeroScene'), { ssr: false });

export default function Home() {
  // Lenis smooth scroll — uses new lenis package (not @studio-freight/lenis)
  useEffect(() => {
    let lenis;
    let rafId;

    async function initLenis() {
      const { default: Lenis } = await import('lenis');
      lenis = new Lenis({
        duration: 1.4,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        smoothWheel: true,
        smoothTouch: false,
        touchMultiplier: 2,
      });

      // GSAP ticker integration
      const { gsap } = await import('gsap');
      const { ScrollTrigger } = await import('gsap/ScrollTrigger');
      gsap.registerPlugin(ScrollTrigger);
      gsap.ticker.add((time) => lenis.raf(time * 1000));
      gsap.ticker.lagSmoothing(0);
      lenis.on('scroll', ScrollTrigger.update);
    }

    initLenis();
    return () => {
      if (lenis) lenis.destroy();
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <>
      <Cursor />
      <Preloader />
      <Navbar />
      <main id="main-content">
        {/* A — Hero: Lamborghini + AR HUD overlay */}
        <HeroScene />
        {/* B — Kinetic Manifesto */}
        <Manifesto />
        {/* C — Drowsiness vs Distraction */}
        <DetectionDual />
        {/* D — Horizontal Tech Showcase */}
        <TechCarousel />
        {/* E — Circuit Signature + Footer */}
        <CircuitSignature />
        {/* Live Cockpit Screen */}
        <CockpitScreen />
      </main>
    </>
  );
}
