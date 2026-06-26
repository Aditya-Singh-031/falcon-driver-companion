# Falcon Frontend — Setup Guide

## Prerequisites

- Node.js 18+ (check with `node --version`)
- npm 9+ (check with `npm --version`)

## Installation

```bash
cd frontend
npm install
```

This installs:
- `lenis` (buttery-smooth scrolling) — **not** `@studio-freight/lenis` which is deprecated and has no v1.0.45
- `gsap` with ScrollTrigger
- `@react-three/fiber` + `@react-three/drei` for the 3D car scene
- `framer-motion` for micro-interactions

## GLB Model Setup

The Lamborghini GLB must be copied manually (not in git — large binary):

```bash
mkdir -p public/models
cp ../lamborghini_centenario_roadster_sdc.glb public/models/lamborghini_centenario_roadster_sdc.glb
```

> **Note:** If you skip this step, the hero section shows an empty lit scene. All scroll animations, HUD overlays, and other sections still work.

## Environment

```bash
cp .env.local.example .env.local
# Edit .env.local if your backend runs on a different port
```

Default `.env.local`:
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Run Dev Server

```bash
npm run dev
# Opens at http://localhost:3000
```

## Production Build

```bash
npm run build
npm start
```

## Common Errors

### `npm error notarget No matching version found for @studio-freight/lenis`
Fixed — `package.json` now uses `lenis` (the current package name). Pull latest main and re-run `npm install`.

### `sh: next: command not found`
This happens when `npm install` aborts mid-way due to an ETARGET error. Fix the lenis error above first, then `npm install` will complete and `next` will be available.

### GLB not loading / blank hero
The GLB file is not in git. Copy it manually as described above. This is expected behaviour — the rest of the site still works.

### CORS errors on `/infer` or `/health`
Make sure your FastAPI backend is running:
```bash
cd ../backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
