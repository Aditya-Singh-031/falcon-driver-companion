import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from sklearn.metrics import classification_report, confusion_matrix
from pathlib import Path
import json
import numpy as np

# ─── Config (must match train_drowsiness.py exactly) ─────────────────────────
DATA_ROOT  = Path("data/ddd")
MODEL_PATH = Path("models/drowsiness_best.pt")
IMG_SIZE   = 224
BATCH_SIZE = 64
SEED       = 42
DEVICE     = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ─── Transforms ───────────────────────────────────────────────────────────────
val_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

# ─── Recreate the same split with the same seed ───────────────────────────────
full_ds = datasets.ImageFolder(DATA_ROOT)
class_names = full_ds.classes

n_total = len(full_ds)
n_val   = int(0.15 * n_total)
n_test  = int(0.10 * n_total)
n_train = n_total - n_val - n_test

_, _, test_ds = torch.utils.data.random_split(
    full_ds, [n_train, n_val, n_test],
    generator=torch.Generator().manual_seed(SEED)
)
test_ds.dataset.transform = val_tf

test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

# ─── Load model ───────────────────────────────────────────────────────────────
model = models.efficientnet_b0(weights=None)
model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
# line 46 in evaluate_drowsiness.py
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
model = model.to(DEVICE)
model.eval()

print(f"Model loaded from: {MODEL_PATH}")
print(f"Test samples: {len(test_ds)}")

# ─── Inference ────────────────────────────────────────────────────────────────
all_preds, all_labels = [], []
with torch.no_grad():
    for imgs, labels in test_loader:
        imgs = imgs.to(DEVICE)
        preds = model(imgs).argmax(1).cpu()
        all_preds.extend(preds.numpy())
        all_labels.extend(labels.numpy())

# ─── Results ──────────────────────────────────────────────────────────────────
print("\n── Classification Report ──────────────────────────")
print(classification_report(all_labels, all_preds, target_names=class_names))

cm = confusion_matrix(all_labels, all_preds)
print("── Confusion Matrix ───────────────────────────────")
print(f"               Predicted")
print(f"               {class_names[0]:12s} {class_names[1]:12s}")
for i, row in enumerate(cm):
    print(f"Actual {class_names[i]:12s} {row[0]:<12d} {row[1]:<12d}")

# Save results
results = {
    "test_samples": len(test_ds),
    "classification_report": classification_report(all_labels, all_preds,
                                                    target_names=class_names,
                                                    output_dict=True),
    "confusion_matrix": cm.tolist()
}
with open("models/test_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved to models/test_results.json")