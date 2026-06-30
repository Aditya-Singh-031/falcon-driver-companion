'use client';

import { useRef, useEffect, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useGLTF, Environment, ContactShadows, PerspectiveCamera, useAnimations } from '@react-three/drei';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import * as THREE from 'three';
import HudOverlay from './HudOverlay';

gsap.registerPlugin(ScrollTrigger);

// The Cinematic Path: Outside → Approaching Door → Inside Driver's Seat
const CAM_POSITIONS = [
  { pos: [6.0, 2.0, 7.0],    target: [0, 0.5, 0] },        // 0%   - Wide outside shot
  { pos: [2.5, 1.2, 2.5],    target: [0, 0.6, -0.5] },     // 50%  - Approaching the opening door
  { pos: [0.35, 0.9, 0.2],   target: [0.35, 0.7, -1.0] }   // 100% - Settled inside cabin, looking at dashboard
];

function lerp(a, b, t) { return a + (b - a) * t; }
function lerpVec3(from, to, t) {
  return [
    lerp(from[0], to[0], t),
    lerp(from[1], to[1], t),
    lerp(from[2], to[2], t),
  ];
}

function getCamAtProgress(p) {
  // CRITICAL FIX: Clamp progress between 0 and 1.
  // macOS rubber-band scrolling causes p to go negative, which crashed the array index!
  const safeP = Math.max(0, Math.min(1, p));
  const count = CAM_POSITIONS.length - 1;
  const segment = Math.min(safeP * count, count - 0.00001);
  const idx = Math.floor(segment);
  const t = segment - idx;
  const from = CAM_POSITIONS[idx];
  const to   = CAM_POSITIONS[idx + 1];
  return {
    pos:    lerpVec3(from.pos,    to.pos,    t),
    target: lerpVec3(from.target, to.target, t),
  };
}

// Smooth camera rig driven by scroll progress
function CameraRig({ progressRef }) {
  const { camera } = useThree();
  const targetRef = useRef(new THREE.Vector3());

  useFrame(() => {
    const p = progressRef.current || 0;
    const { pos, target } = getCamAtProgress(p);

    camera.position.lerp(new THREE.Vector3(...pos), 0.04);
    targetRef.current.lerp(new THREE.Vector3(...target), 0.04);
    camera.lookAt(targetRef.current);
  });

  return null;
}

// Load the Lambo GLB and scrub its animations
function LamborghiniModel({ progressRef }) {
  const groupRef = useRef();
  const { scene, animations } = useGLTF('/models/lamborghini_centenario_roadster_sdc.glb');
  const { actions } = useAnimations(animations, groupRef);

  useEffect(() => {
    if (!scene) return;
    // Enhance materials for realism
    scene.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
        if (child.material) {
          child.material.envMapIntensity = 1.5;
        }
      }
    });
  }, [scene]);

  useFrame(() => {
    // Scrub the door opening animation based on scroll progress!
    if (actions && Object.keys(actions).length > 0) {
      const actionName = Object.keys(actions)[0]; // Target the built-in animation
      const action = actions[actionName];
      if (action) {
        action.play();
        action.paused = true; // We manually control the timeline via scroll
        
        const p = Math.max(0, Math.min(1, progressRef.current));
        // Calculate door opening: fully opens during the first 60% of the scroll
        const animProgress = Math.min(p / 0.6, 1.0);
        action.time = animProgress * action.getClip().duration;
      }
    }
  });

  return <primitive ref={groupRef} object={scene} scale={1} position={[0, -0.5, 0]} />
}

// Inner canvas scene
function Scene({ progressRef }) {
  return (
    <>
      <PerspectiveCamera makeDefault fov={55} near={0.1} far={200} />
      <CameraRig progressRef={progressRef} />

      {/* Lighting */}
      <ambientLight intensity={0.3} />
      <directionalLight position={[10, 10, 5]} intensity={2.5} castShadow />
      <pointLight position={[-5, 3, -5]} intensity={1.5} color="#00F3FF" />
      <pointLight position={[5,  1, 5]}  intensity={1.0} color="#D4F000" />

      {/* Environment */}
      <Environment preset="night" />

      {/* Car model */}
      <Suspense fallback={null}>
        <LamborghiniModel progressRef={progressRef} />
      </Suspense>

      {/* Ground shadow */}
      <ContactShadows
        position={[0, -0.5, 0]}
        opacity={0.6}
        scale={20}
        blur={2}
        far={10}
      />
    </>
  );
}

export default function HeroScene() {
  const sectionRef  = useRef(null);
  const progressRef = useRef(0);
  const hudRef      = useRef(null);
  const titleRef    = useRef(null);
  const subtitleRef = useRef(null);

  useEffect(() => {
    let ctx;
    async function init() {
      const { gsap } = await import('gsap');
      const { ScrollTrigger } = await import('gsap/ScrollTrigger');
      gsap.registerPlugin(ScrollTrigger);

      ctx = gsap.context(() => {
        // Parallax on FALCON title
        gsap.to(titleRef.current, {
          yPercent: -30,
          ease: 'none',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top top',
            end: 'bottom top',
            scrub: true,
          },
        });

        // Drive camera & animation progress 0→1
        const proxy = { p: 0 };
        gsap.to(proxy, {
          p: 1,
          ease: 'none',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top top',
            end: 'bottom top',
            scrub: 1.5,
            onUpdate: (self) => {
              progressRef.current = self.progress;
            },
          },
        });

        // HUD assembles when camera lands inside the cabin (>75% scroll)
        ScrollTrigger.create({
          trigger: sectionRef.current,
          start: '75% top',
          end: 'bottom top',
          onEnter: () => {
            if (!hudRef.current) return;
            gsap.to(hudRef.current.querySelectorAll('.hud-corner'), {
              opacity: 1, duration: 0.4, stagger: 0.08, ease: 'expo.out',
            });
            gsap.to(hudRef.current.querySelectorAll('.hud-panel'), {
              x: 0, opacity: 1, duration: 0.6, stagger: 0.1, ease: 'expo.out',
            });
            gsap.to(hudRef.current.querySelectorAll('.hud-mesh-line'), {
              scaleX: 1, opacity: 0.6, duration: 0.5, stagger: 0.02, ease: 'expo.out',
            });
          },
          onLeaveBack: () => {
            if (!hudRef.current) return;
            gsap.to(hudRef.current.querySelectorAll('.hud-corner, .hud-panel, .hud-mesh-line'), {
              opacity: 0, duration: 0.3,
            });
          },
        });
      }, sectionRef);
    }
    
    init();
    return () => ctx && ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="system"
      style={{ height: '250vh', position: 'relative' }}
    >
      <div
        style={{
          position: 'sticky',
          top: 0,
          height: '100vh',
          width: '100%',
          overflow: 'hidden',
          background: '#050505',
        }}
      >
        <div
          ref={titleRef}
          aria-hidden="true"
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1,
            pointerEvents: 'none',
          }}
        >
          <span
            className="font-display"
            style={{
              fontSize: 'clamp(6rem, 22vw, 22rem)',
              fontWeight: 700,
              letterSpacing: '-0.02em',
              color: 'transparent',
              WebkitTextStroke: '1px rgba(212,240,0,0.08)',
              userSelect: 'none',
              lineHeight: 1,
            }}
          >
            FALCON
          </span>
        </div>

        <div style={{ position: 'absolute', inset: 0, zIndex: 2 }}>
          <Canvas
            dpr={1}
            gl={{ antialias: true, alpha: false, toneMapping: THREE.ACESFilmicToneMapping, outputColorSpace: THREE.SRGBColorSpace }}
            shadows
          >
            <Scene progressRef={progressRef} />
          </Canvas>
        </div>

        <div
          ref={hudRef}
          style={{ position: 'absolute', inset: 0, zIndex: 3, pointerEvents: 'none' }}
        >
          <HudOverlay />
        </div>

        <div
          ref={subtitleRef}
          style={{
            position: 'absolute',
            bottom: '40px', left: '40px', right: '40px',
            zIndex: 4,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            pointerEvents: 'none',
          }}
        >
          <div>
            <p className="section-label" style={{ marginBottom: '8px' }}>SCROLL TO ENTER</p>
            <div style={{ width: '40px', height: '1px', background: '#D4F000' }} />
          </div>
          <div style={{ textAlign: 'right' }}>
            <p className="section-label">EDGE AI · REAL-TIME · ON-DEVICE</p>
            <p className="font-mono" style={{ fontSize: '0.65rem', color: '#D4F000', marginTop: '4px' }}>v2.1.0 · FALCON ENGINE</p>
          </div>
        </div>

        <div style={{ position: 'absolute', bottom: '40px', left: '50%', transform: 'translateX(-50%)', zIndex: 4 }}>
          <div
            style={{
              width: '1px', height: '60px',
              background: 'linear-gradient(to bottom, transparent, #D4F000)',
              animation: 'scrollIndicator 1.5s ease-in-out infinite',
            }}
          />
        </div>

        <style>{`
          @keyframes scrollIndicator {
            0%, 100% { opacity: 1; transform: scaleY(1); transform-origin: top; }
            50% { opacity: 0.3; transform: scaleY(0.5); transform-origin: top; }
          }
        `}</style>
      </div>
    </section>
  );
}

useGLTF.preload('/models/lamborghini_centenario_roadster_sdc.glb');