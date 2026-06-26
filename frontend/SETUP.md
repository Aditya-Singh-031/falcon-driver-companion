# Falcon Frontend — Setup

## Prerequisites
- Node.js 18+
- The Lamborghini GLB file already committed at the repo root

## 1. Copy the 3D model
```bash
# From repo root
cp lamborghini_centenario_roadster_sdc.glb frontend/public/models/
```

## 2. Install dependencies
```bash
cd frontend
npm install
```

## 3. Configure environment (optional)
```bash
cp .env.local.example .env.local
# Edit if backend/dashboard run on non-default ports
```

## 4. Run all three services

**Terminal 1 — Backend (FastAPI)**
```bash
cd backend
pip install -r requirements-backend.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Dashboard (Streamlit)**
```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

**Terminal 3 — Frontend (Next.js)**
```bash
cd frontend
npm run dev
```

Open **http://localhost:3000** — the full cinematic Falcon experience.

## What you'll see
1. **Preloader** — FAL/CON crash-in, neon progress bar
2. **Hero** — Lamborghini Centenario loads; camera dollies from outside → inside cabin on scroll
3. **HUD** — AR wireframe assembles when camera is inside
4. **Manifesto** — words light up word-by-word on scroll
5. **Detection Dual** — DROWSINESS / DISTRACTION hover panels with JSON snippets
6. **Tech Carousel** — horizontal GSAP pin, 3D mouse-tilt cards
7. **Circuit Signature** — SVG self-draws on scroll
8. **Cockpit Screen** — embedded Streamlit dashboard inside a bezel frame
