# Falcon Frontend — Next.js Cinematic UI

Awwwards-level interactive landing for **Falcon Driver Companion** — Edge AI in-cabin safety system.

## Tech Stack

- **Next.js 14** App Router
- **React Three Fiber** — Lamborghini Centenario GLB scene, camera dolly into cabin
- **GSAP + ScrollTrigger** — Scroll-bound HUD assembly, manifesto word-by-word reveal, horizontal tech showcase
- **lenis** — Buttery-smooth scrolling (replaces deprecated `@studio-freight/lenis`)
- **Framer Motion** — Micro-interactions, hover effects
- **Tailwind CSS** — Utility-first layout

## Quick Start

```bash
# From repo root
cd frontend

# 1. Install dependencies (lenis is now the correct package name)
npm install

# 2. Copy your Lamborghini GLB into public/models/
mkdir -p public/models
cp ../lamborghini_centenario_roadster_sdc.glb public/models/lamborghini_centenario_roadster_sdc.glb

# 3. Copy env file
cp .env.local.example .env.local

# 4. Start dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## GLB File

The Lamborghini GLB is **not committed to git** (large binary). You must copy it manually:

```bash
cp ../lamborghini_centenario_roadster_sdc.glb public/models/lamborghini_centenario_roadster_sdc.glb
```

If the file isn't available, the Three.js scene will show an empty environment with lighting — all scroll and HUD animations still work.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | FastAPI backend URL |

## Architecture

```
src/
  app/
    layout.jsx        Root layout with font loading
    page.jsx          Entry point, Lenis init, section assembly
    globals.css       Design tokens, keyframes, base styles
  components/
    HeroScene.jsx     R3F canvas + camera rig + scroll progress driver
    HudOverlay.jsx    AR wireframe, bounding box corners, data panels
    Preloader.jsx     Cinematic entry animation
    Navbar.jsx        Sticky nav with scroll-aware opacity
    Manifesto.jsx     Word-by-word scroll-highlight text
    DetectionDual.jsx DROWSINESS vs DISTRACTION interactive blocks
    TechCarousel.jsx  Horizontal scroll — GSAP pinned tech cards
    CockpitScreen.jsx Live inference view (connects to FastAPI /infer)
    CircuitSignature.jsx SVG draw-on circuit + footer
    Cursor.jsx        Custom magnetic cursor
```

## Running Full Stack

```bash
# Terminal 1 — FastAPI backend
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Streamlit dashboard (optional)
streamlit run dashboard/app.py

# Terminal 3 — Next.js frontend
cd frontend && npm run dev
```

The frontend hits `http://127.0.0.1:8000` for live inference and health checks.
