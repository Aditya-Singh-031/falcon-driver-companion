# 🦅 Falcon — Edge AI In-Cabin Driver Companion

![Falcon Banner](falcon_title.png)

> **Tata Technologies InnoVent-27 submission** · Category: *Edge AI for Personalized and Connected Vehicles*

Falcon is an on-device AI system that monitors driver state in real time — detecting drowsiness and distraction, managing notifications intelligently, and keeping the driver safe without relying on cloud inference.

---

## 🚀 Features

| Module | Description | Status |
|---|---|---|
| **Drowsiness Detection** | EfficientNet-B0 fine-tuned on DDD dataset — 100% test accuracy | ✅ Done |
| **Distraction Detection** | Head pose + gaze tracking for off-road attention | 🔧 In Progress |
| **Notification Manager** | Context-aware notification filtering based on driver state | 🔧 In Progress |
| **Edge Inference** | All models run locally — no cloud dependency | 🔧 In Progress |
| **Backend API** | FastAPI service connecting camera feed to inference pipeline | 🔧 In Progress |

---

## 🧠 Model Card — Drowsiness Classifier

| Property | Value |
|---|---|
| Architecture | EfficientNet-B0 (pretrained on ImageNet, fine-tuned) |
| Dataset | Driver Drowsiness Detection (DDD) |
| Input | 224×224 RGB image |
| Classes | `drowsy`, `non_drowsy` |
| Train / Val / Test split | 75% / 15% / 10% |
| Class balancing | WeightedRandomSampler |
| Optimizer | AdamW (lr=1e-4, weight_decay=1e-4) |
| Scheduler | CosineAnnealingLR (T_max=15) |
| Epochs | 15 |
| Test Accuracy | **100%** (4,179 samples) |
| Test F1-Score | **1.00** (macro avg) |

### Test Results

```
              precision    recall  f1-score   support

      drowsy       1.00      1.00      1.00      2249
  non_drowsy       1.00      1.00      1.00      1930

    accuracy                           1.00      4179
```

### Download Weights

Download `drowsiness_best.pt` from the [**Releases page**](https://github.com/Aditya-Singh-031/falcon-driver-companion/releases) and place it in `models/`.

---

## 📁 Project Structure

```
falcon-driver-companion/
├── src/
│   └── models/
│       ├── train_drowsiness.py       # Training script (EfficientNet-B0)
│       └── evaluate_drowsiness.py    # Evaluation script (loads saved weights)
├── models/
│   ├── drowsiness_best.pt            # ⚠️ Not in git — download from Releases
│   ├── train_history.json            # Loss/accuracy curves per epoch
│   └── test_results.json             # Classification report + confusion matrix
├── backend/                          # FastAPI inference server (WIP)
├── notebooks/                        # Exploration & prototyping
├── requirements.txt                  # Full pip freeze (CPU/general)
├── requirements-gpu.txt              # GPU-specific (torch+cu121)
├── falcon_architecture.pdf           # System architecture diagram
└── Falcon - Edge AI In-Cabin Companion - Innovent27.pdf  # Hackathon submission doc
```

---

## ⚙️ Setup

### Prerequisites

- Python 3.10+
- CUDA 12.1 compatible GPU (recommended) or CPU

### 1. Clone the repo

```bash
git clone https://github.com/Aditya-Singh-031/falcon-driver-companion.git
cd falcon-driver-companion
```

### 2. Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 3. Install dependencies

**GPU (recommended):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements-gpu.txt
```

**CPU only:**
```bash
pip install -r requirements.txt
```

### 4. Prepare dataset

Download the [Driver Drowsiness Detection (DDD) dataset](https://www.kaggle.com/datasets/ismailnasri20/driver-drowsiness-dataset-ddd) and place it at:

```
data/ddd/
├── drowsy/
└── non_drowsy/
```

### 5. Train

```bash
python src/models/train_drowsiness.py
```

### 6. Evaluate

Download `drowsiness_best.pt` from [Releases](https://github.com/Aditya-Singh-031/falcon-driver-companion/releases) → place in `models/` → run:

```bash
python src/models/evaluate_drowsiness.py
```

---

## 📊 Training History

Training and validation metrics per epoch are saved to `models/train_history.json`. Full test results including the confusion matrix are in `models/test_results.json`.

---

## 🏆 Hackathon

This project is submitted to **Tata Technologies InnoVent-27** (2026) under the category:

> **Edge AI for Personalized and Connected Vehicles**

See [`Falcon - Edge AI In-Cabin Companion - Innovent27.pdf`](./Falcon%20-%20Edge%20AI%20In-Cabin%20Companion%20-%20Innovent27.pdf) for the full project proposal and [`falcon_architecture.pdf`](./falcon_architecture.pdf) for the system architecture.

---

## 📄 License

This project is for academic and hackathon purposes.

---

*Built by [Aditya Singh](https://github.com/Aditya-Singh-031) · IIT Mandi*
