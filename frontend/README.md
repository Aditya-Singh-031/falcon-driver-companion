# Falcon — Cinematic Frontend

Next.js 14 + React Three Fiber + GSAP + Lenis + Framer Motion + Tailwind CSS

## Stack
- **Next.js 14** App Router
- **React Three Fiber** — Lamborghini Centenario GLB scene, door animation, camera dolly
- **GSAP + ScrollTrigger** — Scroll-bound HUD assembly, manifesto word-by-word reveal, horizontal tech showcase
- **@studio-freight/lenis** — Buttery-smooth scrolling (non-negotiable)
- **Framer Motion** — Micro-interactions, hover effects
- **Tailwind CSS** — Utility-first layout

## Setup

```bash
cd frontend
npm install

# Copy the GLB model from repo root into public/models
mkdir -p public/models
cp ../lamborghini_centenario_roadster_sdc.glb public/models/lambo.glb

npm run dev
```

Then open: http://localhost:3000

Backend must be running at http://localhost:8000 for the live cockpit feed to work.

## Architecture

```
src/
  app/
    layout.jsx       ← Lenis smooth scroll + font loading
    page.jsx         ← Assembles all sections
    globals.css      ← Base styles + CSS variables
  components/
    Navbar.jsx           ← Fixed HUD-style nav
    HeroSection.jsx      ← GSAP parallax + AR HUD overlay on scroll
    CarScene.jsx         ← R3F: Lambo scene, door open, camera into cabin
    CockpitView.jsx      ← Live Falcon dashboard (webcam → /infer API)
    ManifestoSection.jsx ← Word-by-word scroll-reveal text
    DetectionSection.jsx ← Drowsiness vs Distraction split
    TechShowcase.jsx     ← GSAP horizontal scroll pin
    CircuitSignature.jsx ← SVG self-drawing circuit on scroll
  hooks/
    useFalconAPI.js  ← /health, /infer, /state/history
```
