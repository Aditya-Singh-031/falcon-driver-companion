# Falcon – Dataset & Model Pipeline Plan

## 1. Datasets

### 1.1 Primary dataset – D3S (Driver Drowsiness Dataset)

- Source: public GitHub dataset for driver drowsiness detection.[web:202]
- Contents (from authors):
  - Videos and extracted frames of drivers in a car‑like setup.
  - Labels for eye‑closed, yawning, happy, neutral states.
- Why use it first:
  - Small and quick to download and inspect.
  - Focused on visual signs of drowsiness (eyes + mouth), which map directly to Falcon’s `drowsiness_level`.
  - Easy to train a simple baseline model before moving to heavier datasets.

### 1.2 Optional future dataset – DMD (Driver Monitoring Dataset)

- Source: Vicomtech open Driver Monitoring Dataset (DMD).[web:196][web:199]
- Contents:
  - 41+ hours of multi‑camera (face, body, hands) driver monitoring videos with annotations for distraction, fatigue, gaze, etc.[web:196][web:199]
- Why later:
  - Much larger and richer, good for scaling Falcon to multi‑modal distraction detection.
  - Too heavy to be the first thing we download/train on, but perfect for a “Phase 2” improvement once the POC works.

## 2. First-model scope

For the InnoVent POC, the **first model** will:

- Input: single RGB frame (cropped to driver face region), resized to a fixed size (e.g., 128×128).
- Output: probability of `drowsy` vs `awake` / `normal`.
- Use cases in Falcon:
  - Estimate `drowsiness_level` as a smoothed probability over a time window.
  - Derive `attention_level` heuristically from drowsiness and (later) head pose / gaze cues.
- This is enough to drive a simple live Falcon demo and fill the backend `DriverState` fields.

## 3. Planned processing pipeline (vision only)

End‑to‑end vision pipeline:

1. **Frame acquisition**
   - Source A: offline dataset (D3S). Read labeled frames from disk for training/validation.
   - Source B: webcam / sample in‑car video for demo.

2. **Face detection & alignment**
   - Use a lightweight face detector (e.g., OpenCV Haar cascade or a small DNN) to locate the driver’s face.
   - Crop and optionally align the face region to reduce background noise.

3. **Pre‑processing**
   - Convert to RGB if needed.
   - Resize to a fixed resolution (e.g., 128×128 or 160×160).
   - Normalize pixel values to [0, 1] or standard mean/std.

4. **Model architecture (baseline)**
   - Option 1: Small custom CNN (3–4 conv blocks + global pooling + dense layers).
   - Option 2: Transfer learning with a lightweight backbone (e.g., MobileNetV2) fine‑tuned for drowsiness classification.
   - Loss: binary cross‑entropy (drowsy vs non‑drowsy).
   - Metrics: accuracy, F1, ROC‑AUC on a held‑out validation set.

5. **Temporal smoothing for real‑time use**
   - Even though training is frame‑level, the runtime pipeline will:
     - Maintain a sliding window of last N frame predictions (e.g., 3–5 seconds).
     - Compute a smoothed `drowsiness_level` (e.g., average probability).
   - This avoids flicker from single misclassified frames.

6. **Mapping to Falcon signals**
   - `drowsiness_level` ∈ [0, 1] = smoothed probability of drowsiness.
   - `attention_level`:
     - Start as `1.0 - drowsiness_level` for the first POC.
     - Later refine with head pose / gaze and distraction features.
   - `cognitive_load`:
     - Initial heuristic based on `drowsiness_level` + driving context (e.g., speed, time of day – to be added later).

7. **Backend integration**
   - A Python service (inside `backend` or `models`) will:
     - Read frames from webcam / video.
     - Run the model to get `drowsiness_level`.
     - Compute `attention_level`, `cognitive_load`, and `notifications_mode`.
     - Expose these values via a FastAPI endpoint that replaces `/driver-state/mock`.

## 4. Phase 2 ideas (post‑POC)

- Add head pose and gaze estimation on top of face crops to detect distraction even when drowsiness is low.
- Integrate DMD dataset for richer distraction and fatigue labels.[web:196][web:199]
- Move from frame‑based to short‑sequence modeling (3D CNNs or temporal models) if time allows.