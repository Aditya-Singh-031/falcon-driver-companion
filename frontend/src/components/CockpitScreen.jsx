'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

const BACKEND_URL   = process.env.NEXT_PUBLIC_BACKEND_URL  || 'http://localhost:8000';
const DASHBOARD_URL = process.env.NEXT_PUBLIC_DASHBOARD_URL || 'http://localhost:8501';

const POLL_INTERVAL = 1500; // ms between inference polls

// ─── helpers ──────────────────────────────────────────────────────────────────

function StatusDot({ ok }) {
  const color  = ok === null ? '#555' : ok ? '#D4F000' : '#ff4444';
  const shadow = ok ? '0 0 8px #D4F000, 0 0 16px rgba(212,240,0,0.4)' : 'none';
  return (
    <span
      style={{
        display: 'inline-block',
        width: 8, height: 8,
        borderRadius: '50%',
        background: color,
        boxShadow: shadow,
        flexShrink: 0,
        transition: 'background 0.4s, box-shadow 0.4s',
      }}
    />
  );
}

function MetricCard({ label, value, unit = '', accent = false, alert = false }) {
  return (
    <div
      style={{
        flex: '1 1 140px',
        background: alert
          ? 'rgba(255,68,68,0.06)'
          : accent
          ? 'rgba(212,240,0,0.04)'
          : 'rgba(255,255,255,0.03)',
        border: `1px solid ${alert ? 'rgba(255,68,68,0.2)' : accent ? 'rgba(212,240,0,0.15)' : 'rgba(255,255,255,0.06)'}`,
        borderRadius: 4,
        padding: '14px 18px',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        transition: 'border-color 0.3s, background 0.3s',
      }}
    >
      <span
        style={{
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: '0.58rem',
          letterSpacing: '0.16em',
          color: alert ? '#ff6666' : accent ? '#D4F000' : '#555',
          textTransform: 'uppercase',
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontFamily: 'var(--font-display, Impact, sans-serif)',
          fontSize: 'clamp(1.2rem, 2.5vw, 2rem)',
          fontWeight: 700,
          color: alert ? '#ff4444' : accent ? '#D4F000' : '#F5F5F5',
          lineHeight: 1,
          letterSpacing: '-0.01em',
          transition: 'color 0.3s',
        }}
      >
        {value ?? '—'}
        {unit && (
          <span style={{ fontSize: '0.6em', marginLeft: 4, opacity: 0.6 }}>{unit}</span>
        )}
      </span>
    </div>
  );
}

function AlertBanner({ level, message }) {
  if (!level || level === 'OK') return null;
  const isCritical = level === 'CRITICAL';
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '10px 16px',
        background: isCritical ? 'rgba(255,68,68,0.12)' : 'rgba(255,180,0,0.08)',
        border: `1px solid ${isCritical ? 'rgba(255,68,68,0.35)' : 'rgba(255,180,0,0.3)'}`,
        borderRadius: 4,
        marginBottom: 16,
        animation: isCritical ? 'alertPulse 1s ease-in-out infinite alternate' : 'none',
      }}
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 1L15 14H1L8 1Z" stroke={isCritical ? '#ff4444' : '#ffb400'} strokeWidth="1.2" />
        <line x1="8" y1="6" x2="8" y2="10" stroke={isCritical ? '#ff4444' : '#ffb400'} strokeWidth="1.2" />
        <circle cx="8" cy="12" r="0.6" fill={isCritical ? '#ff4444' : '#ffb400'} />
      </svg>
      <span
        style={{
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: '0.65rem',
          letterSpacing: '0.14em',
          color: isCritical ? '#ff6666' : '#ffb400',
        }}
      >
        {level} · {message}
      </span>
    </div>
  );
}

function BezelCorners({ active }) {
  const color = active ? '#00F3FF' : 'rgba(0,243,255,0.2)';
  const size  = 18;
  const corners = [
    { top: 0,    left:  0, borderTop:    `1.5px solid ${color}`, borderLeft:  `1.5px solid ${color}` },
    { top: 0,    right: 0, borderTop:    `1.5px solid ${color}`, borderRight: `1.5px solid ${color}` },
    { bottom: 0, left:  0, borderBottom: `1.5px solid ${color}`, borderLeft:  `1.5px solid ${color}` },
    { bottom: 0, right: 0, borderBottom: `1.5px solid ${color}`, borderRight: `1.5px solid ${color}` },
  ];
  return (
    <>
      {corners.map((style, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            width: size, height: size,
            transition: 'border-color 0.5s',
            ...style,
          }}
        />
      ))}
    </>
  );
}

// ─── capture a frame from the webcam as a base64 JPEG ─────────────────────────
async function captureFrame(videoEl) {
  if (!videoEl || videoEl.readyState < 2) return null;
  const canvas = document.createElement('canvas');
  canvas.width  = videoEl.videoWidth  || 320;
  canvas.height = videoEl.videoHeight || 240;
  canvas.getContext('2d').drawImage(videoEl, 0, 0);
  // strip the "data:image/jpeg;base64," prefix — backend does its own split
  return canvas.toDataURL('image/jpeg', 0.7);
}

// ─── main component ───────────────────────────────────────────────────────────
export default function CockpitScreen() {
  const sectionRef   = useRef(null);
  const videoRef     = useRef(null);   // hidden <video> for webcam
  const streamRef    = useRef(null);   // MediaStream handle
  const pollRef      = useRef(null);   // setInterval handle

  const [backendOk,   setBackendOk]   = useState(null);
  const [cameraOk,    setCameraOk]    = useState(null);  // null | true | false
  const [inferring,   setInferring]   = useState(false);
  const [metrics,     setMetrics]     = useState(null);
  const [latency,     setLatency]     = useState(null);
  const [alertState,  setAlertState]  = useState({ level: null, message: '' });
  const [frameCount,  setFrameCount]  = useState(0);
  const [fps,         setFps]         = useState(0);
  const [camError,    setCamError]    = useState('');

  // ── backend health ─────────────────────────────────────────────────────────
  const ping = useCallback(async () => {
    try {
      const r = await fetch(`${BACKEND_URL}/health`, {
        signal: AbortSignal.timeout(3000),
        cache:  'no-store',
      });
      setBackendOk(r.ok);
      return r.ok;
    } catch {
      setBackendOk(false);
      return false;
    }
  }, []);

  useEffect(() => {
    ping();
    const id = setInterval(ping, 10_000);
    return () => clearInterval(id);
  }, [ping]);

  // ── webcam ─────────────────────────────────────────────────────────────────
  const startCamera = useCallback(async () => {
    if (streamRef.current) return true; // already running
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraOk(true);
      setCamError('');
      return true;
    } catch (err) {
      setCameraOk(false);
      setCamError(err?.message || 'Camera permission denied');
      return false;
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOk(null);
  }, []);

  // ── inference — POST /infer with base64 frame ─────────────────────────────
  const runInference = useCallback(async () => {
    const frame = await captureFrame(videoRef.current);
    if (!frame) return; // camera not ready yet

    const t0 = performance.now();
    try {
      const r = await fetch(`${BACKEND_URL}/infer`, {
        method:  'POST',                        // ← was wrongly called as GET before
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ frame }),     // matches InferenceRequest schema
        signal:  AbortSignal.timeout(4000),
        cache:   'no-store',
      });

      if (!r.ok) {
        console.warn(`[Falcon] /infer returned ${r.status}`);
        return;
      }

      const data    = await r.json();
      const elapsed = Math.round(performance.now() - t0);

      setLatency(elapsed);
      setMetrics(data);
      setFrameCount(c => c + 1);

      // alert logic
      const drowsy   = typeof data?.drowsiness_confidence === 'number' ? data.drowsiness_confidence : 0;
      const distract = typeof data?.distraction_confidence === 'number' ? data.distraction_confidence : 0;
      const state    = data?.driver_state ?? '';

      if (state === 'critical' || drowsy > 0.85 || distract > 0.85) {
        setAlertState({ level: 'CRITICAL', message: state || 'Driver impairment detected' });
      } else if (state === 'drowsy' || state === 'distracted' || drowsy > 0.55 || distract > 0.55) {
        setAlertState({ level: 'WARNING', message: state || 'Elevated risk detected' });
      } else {
        setAlertState({ level: 'OK', message: '' });
      }
    } catch (err) {
      // timeout or network error — log once, stay quiet in UI
      console.warn('[Falcon] inference error:', err?.message);
    }
  }, []);

  // ── FPS counter ────────────────────────────────────────────────────────────
  useEffect(() => {
    const id = setInterval(() => {
      setFps(frameCount);
      setFrameCount(0);
    }, 1000);
    return () => clearInterval(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [frameCount]);

  // ── start / stop polling ───────────────────────────────────────────────────
  const startPolling = useCallback(async () => {
    if (pollRef.current) return;
    const camReady = await startCamera();
    if (!camReady) return;
    setInferring(true);
    runInference();
    pollRef.current = setInterval(runInference, POLL_INTERVAL);
  }, [runInference, startCamera]);

  const stopPolling = useCallback(() => {
    clearInterval(pollRef.current);
    pollRef.current = null;
    setInferring(false);
    stopCamera();
    setAlertState({ level: null, message: '' });
    setMetrics(null);
    setLatency(null);
  }, [stopCamera]);

  useEffect(() => () => {
    clearInterval(pollRef.current);
    stopCamera();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── GSAP section reveal ────────────────────────────────────────────────────
  useEffect(() => {
    let ctx;
    (async () => {
      const { gsap }          = await import('gsap');
      const { ScrollTrigger } = await import('gsap/ScrollTrigger');
      gsap.registerPlugin(ScrollTrigger);
      ctx = gsap.context(() => {
        gsap.fromTo(
          sectionRef.current,
          { opacity: 0, y: 60 },
          {
            opacity: 1, y: 0, duration: 1.2, ease: 'expo.out',
            scrollTrigger: { trigger: sectionRef.current, start: 'top 82%', once: true },
          }
        );
      });
    })();
    return () => ctx?.revert();
  }, []);

  // ── derived display values ─────────────────────────────────────────────────
  const drowsinessLabel  = metrics?.drowsiness ?? '—';
  const distractionLabel = metrics?.distraction ?? '—';
  const drowsinessConf   = metrics?.drowsiness_confidence;
  const distractionConf  = metrics?.distraction_confidence;
  const driverState      = metrics?.driver_state ?? (inferring ? 'ACTIVE' : '—');
  const alertLevel       = metrics?.alert_level;

  const fmtConf = (v) =>
    typeof v === 'number' ? `${(v * 100).toFixed(1)}%` : '—';

  return (
    <>
      <style>{`
        @keyframes alertPulse {
          from { opacity: 1; }
          to   { opacity: 0.65; }
        }
        @keyframes scanline {
          0%   { transform: translateY(0); }
          100% { transform: translateY(700px); }
        }
        @keyframes bezelBlink {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.4; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* hidden webcam video element — not shown to user, only used for frame capture */}
      <video
        ref={videoRef}
        muted
        playsInline
        autoPlay
        aria-hidden="true"
        style={{ position: 'absolute', width: 1, height: 1, opacity: 0, pointerEvents: 'none' }}
      />

      <section
        ref={sectionRef}
        id="cockpit"
        style={{
          minHeight: '100vh',
          background: '#080808',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: 'clamp(40px, 8vw, 120px) clamp(24px, 6vw, 80px)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* section label + heading */}
        <p className="section-label" style={{ marginBottom: 16 }}>/ 05 LIVE COCKPIT</p>
        <h2
          className="font-display"
          style={{
            fontSize: 'clamp(2.5rem, 6vw, 7rem)',
            fontWeight: 700,
            letterSpacing: '-0.02em',
            color: '#F5F5F5',
            lineHeight: 0.95,
            marginBottom: 48,
          }}
        >
          IN-CABIN
          <br />
          <span className="cyan cyan-glow">MONITOR</span>
        </h2>

        {/* status row */}
        <div
          style={{
            display: 'flex',
            gap: 12,
            marginBottom: 32,
            flexWrap: 'wrap',
            alignItems: 'center',
          }}
        >
          {/* backend pill */}
          <div
            className="glass"
            style={{
              padding: '10px 18px',
              display: 'flex', alignItems: 'center', gap: 10,
              border: `1px solid ${backendOk ? 'rgba(212,240,0,0.15)' : 'rgba(255,68,68,0.15)'}`,
              transition: 'border-color 0.4s',
            }}
          >
            <StatusDot ok={backendOk} />
            <span
              className="font-mono"
              style={{ fontSize: '0.62rem', letterSpacing: '0.16em', color: '#666' }}
            >
              BACKEND {backendOk === null ? 'CHECKING…' : backendOk ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>

          {/* camera pill */}
          {cameraOk !== null && (
            <div
              className="glass"
              style={{
                padding: '10px 18px',
                display: 'flex', alignItems: 'center', gap: 10,
                border: `1px solid ${cameraOk ? 'rgba(0,243,255,0.15)' : 'rgba(255,68,68,0.15)'}`,
              }}
            >
              <StatusDot ok={cameraOk} />
              <span
                className="font-mono"
                style={{ fontSize: '0.62rem', letterSpacing: '0.16em', color: '#666' }}
              >
                CAMERA {cameraOk ? 'ACTIVE' : 'ERROR'}
              </span>
            </div>
          )}

          {/* inference toggle */}
          <button
            onClick={inferring ? stopPolling : startPolling}
            disabled={!backendOk}
            style={{
              padding: '10px 20px',
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: '0.62rem',
              letterSpacing: '0.16em',
              cursor: backendOk ? 'pointer' : 'not-allowed',
              background: inferring ? 'rgba(255,68,68,0.08)' : 'rgba(212,240,0,0.08)',
              border: `1px solid ${inferring ? 'rgba(255,68,68,0.3)' : 'rgba(212,240,0,0.3)'}`,
              color: inferring ? '#ff6666' : '#D4F000',
              opacity: backendOk ? 1 : 0.4,
              transition: 'all 0.3s',
              display: 'flex', alignItems: 'center', gap: 8,
            }}
          >
            {inferring ? (
              <>
                <span
                  style={{
                    width: 6, height: 6, borderRadius: '50%',
                    background: '#ff4444',
                    animation: 'bezelBlink 0.8s ease-in-out infinite',
                  }}
                />
                STOP INFERENCE
              </>
            ) : (
              <>
                <svg width="8" height="10" viewBox="0 0 8 10" fill="#D4F000">
                  <path d="M0 0L8 5L0 10V0Z" />
                </svg>
                START INFERENCE
              </>
            )}
          </button>

          {/* links */}
          <a
            href={`${BACKEND_URL}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="glass font-mono"
            style={{
              padding: '10px 18px', fontSize: '0.62rem',
              letterSpacing: '0.16em', color: '#00F3FF',
              textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 8,
              border: '1px solid rgba(0,243,255,0.15)',
            }}
          >
            API DOCS ↗
          </a>
          <a
            href={DASHBOARD_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono"
            style={{
              padding: '10px 22px', fontSize: '0.62rem',
              letterSpacing: '0.16em',
              background: '#D4F000', color: '#050505',
              textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 8,
              fontWeight: 700,
            }}
          >
            OPEN DASHBOARD ↗
          </a>
        </div>

        {/* camera error banner */}
        {camError && (
          <div
            style={{
              padding: '10px 16px',
              marginBottom: 16,
              background: 'rgba(255,68,68,0.06)',
              border: '1px solid rgba(255,68,68,0.2)',
              borderRadius: 4,
              fontFamily: 'var(--font-mono, monospace)',
              fontSize: '0.65rem',
              color: '#ff6666',
              letterSpacing: '0.12em',
            }}
          >
            CAMERA ERROR · {camError}
          </div>
        )}

        {/* alert banner */}
        <AlertBanner level={alertState.level} message={alertState.message} />

        {/* metrics row — only when inferring */}
        {inferring && (
          <div
            style={{
              display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24,
              animation: 'fadeIn 0.4s ease forwards',
            }}
          >
            <MetricCard
              label="DRIVER STATE"
              value={driverState?.toUpperCase()}
              accent={!alertState.level || alertState.level === 'OK'}
              alert={alertState.level === 'CRITICAL'}
            />
            <MetricCard
              label="DROWSINESS"
              value={`${drowsinessLabel?.toUpperCase()} ${fmtConf(drowsinessConf)}`}
              alert={drowsinessConf > 0.55}
            />
            <MetricCard
              label="DISTRACTION"
              value={`${distractionLabel?.toUpperCase()} ${fmtConf(distractionConf)}`}
              alert={distractionConf > 0.55}
            />
            <MetricCard label="LATENCY" value={latency} unit="ms" accent />
            <MetricCard label="FPS" value={fps} accent />
            {alertLevel != null && (
              <MetricCard
                label="ALERT LEVEL"
                value={alertLevel}
                alert={alertLevel >= 2}
                accent={alertLevel === 0}
              />
            )}
          </div>
        )}

        {/* cockpit frame */}
        <div
          style={{
            position: 'relative',
            width: '100%',
            maxWidth: 1100,
            borderRadius: 4,
            overflow: 'hidden',
            border: `1px solid ${inferring ? 'rgba(0,243,255,0.2)' : 'rgba(0,243,255,0.08)'}`,
            boxShadow: inferring
              ? '0 0 60px rgba(0,243,255,0.08), 0 0 120px rgba(0,243,255,0.03)'
              : '0 0 40px rgba(0,0,0,0.5)',
            transition: 'border-color 0.5s, box-shadow 0.5s',
          }}
        >
          <BezelCorners active={inferring} />

          {/* top bar */}
          <div
            style={{
              background: '#0d0d0d',
              borderBottom: '1px solid rgba(255,255,255,0.05)',
              padding: '10px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ff5f57' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#febc2e' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#28c840' }} />
            <span
              className="font-mono"
              style={{ fontSize: '0.58rem', color: '#3a3a3a', marginLeft: 12, letterSpacing: '0.16em' }}
            >
              FALCON COCKPIT · {DASHBOARD_URL}
            </span>
            {inferring && (
              <span
                style={{
                  marginLeft: 'auto',
                  display: 'flex', alignItems: 'center', gap: 6,
                  fontFamily: 'var(--font-mono, monospace)',
                  fontSize: '0.55rem', letterSpacing: '0.16em', color: '#D4F000',
                }}
              >
                <span
                  style={{
                    width: 6, height: 6, borderRadius: '50%', background: '#D4F000',
                    animation: 'bezelBlink 1s ease-in-out infinite',
                  }}
                />
                LIVE
              </span>
            )}
          </div>

          {/* content */}
          {backendOk === false ? (
            <div
              style={{
                height: 600,
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center',
                background: '#0a0a0a', gap: 16,
              }}
            >
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                <circle cx="20" cy="20" r="18" stroke="#ff4444" strokeWidth="1.5" />
                <line x1="13" y1="13" x2="27" y2="27" stroke="#ff4444" strokeWidth="1.5" />
                <line x1="27" y1="13" x2="13" y2="27" stroke="#ff4444" strokeWidth="1.5" />
              </svg>
              <p className="font-display" style={{ fontSize: '1.5rem', color: '#F5F5F5' }}>
                BACKEND OFFLINE
              </p>
              <p
                className="font-body"
                style={{ fontSize: '0.85rem', color: '#555', textAlign: 'center', maxWidth: '36ch' }}
              >
                Start the FastAPI backend on port 8000, then this panel will reconnect automatically.
              </p>
              <code
                className="font-mono"
                style={{
                  fontSize: '0.7rem', color: '#D4F000',
                  background: 'rgba(212,240,0,0.06)',
                  padding: '8px 16px',
                  border: '1px solid rgba(212,240,0,0.12)',
                }}
              >
                cd backend && uvicorn main:app --reload
              </code>
            </div>
          ) : (
            <div style={{ position: 'relative' }}>
              {inferring && (
                <div
                  aria-hidden="true"
                  style={{
                    position: 'absolute',
                    top: 0, left: 0, right: 0,
                    height: 2,
                    background: 'linear-gradient(90deg, transparent, rgba(0,243,255,0.15), transparent)',
                    animation: 'scanline 3s linear infinite',
                    zIndex: 10,
                    pointerEvents: 'none',
                  }}
                />
              )}
              <iframe
                src={DASHBOARD_URL}
                title="Falcon Cockpit Dashboard"
                width="100%"
                height="700"
                style={{ display: 'block', border: 'none', background: '#050505' }}
                allow="camera; microphone"
              />
            </div>
          )}
        </div>

        {/* ghost bg text */}
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            bottom: -40, right: -20,
            fontSize: 'clamp(6rem, 18vw, 18rem)',
            fontFamily: 'var(--font-display, Impact, sans-serif)',
            fontWeight: 700,
            color: 'rgba(255,255,255,0.012)',
            letterSpacing: '-0.02em',
            lineHeight: 1,
            userSelect: 'none',
            pointerEvents: 'none',
          }}
        >
          LIVE
        </div>
      </section>
    </>
  );
}
