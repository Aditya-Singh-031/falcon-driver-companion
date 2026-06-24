import os
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms, models
from pathlib import Path
import json

# ─── Config ──────────────────────────────────────────────────────────────────
DATA_ROOT   = Path("data/ddd")
MODEL_DIR   = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

IMG_SIZE    = 224
BATCH_SIZE  = 64
EPOCHS      = 15
LR          = 1e-4
NUM_WORKERS = 0
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Using device: {DEVICE}")
if DEVICE.type == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# ─── Transforms ──────────────────────────────────────────────────────────────
train_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

val_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

if __name__ == '__main__':
    # ─── Datasets ────────────────────────────────────────────────────────────────
    full_ds = datasets.ImageFolder(DATA_ROOT)
    classes = full_ds.classes
    print(f"Classes: {classes}")  # ['drowsy', 'non_drowsy']

    n_total = len(full_ds)
    n_val   = int(0.15 * n_total)
    n_test  = int(0.10 * n_total)
    n_train = n_total - n_val - n_test

    train_ds, val_ds, test_ds = torch.utils.data.random_split(
        full_ds, [n_train, n_val, n_test],
        generator=torch.Generator().manual_seed(42)
    )

    # Apply correct transforms per split
    train_ds.dataset.transform = train_tf
    val_ds.dataset.transform   = val_tf
    test_ds.dataset.transform  = val_tf

    print(f"Train: {n_train} | Val: {n_val} | Test: {n_test}")

    # ─── Weighted Sampler (handles class imbalance) ───────────────────────────────
    targets      = [full_ds.targets[i] for i in train_ds.indices]
    class_counts = [targets.count(c) for c in range(len(classes))]
    weights      = [1.0 / class_counts[t] for t in targets]
    sampler      = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler,
                              num_workers=NUM_WORKERS, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=True)

    # ─── Model (EfficientNet-B0 pretrained) ──────────────────────────────────────
    model = models.efficientnet_b0(weights="IMAGENET1K_V1")
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    # ─── Train/Val Loop ───────────────────────────────────────────────────────────
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    best_val_acc = 0.0

    for epoch in range(1, EPOCHS + 1):
        # Train
        model.train()
        t0 = time.time()
        running_loss, correct, total = 0.0, 0, 0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            out  = model(imgs)
            loss = criterion(out, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * imgs.size(0)
            correct      += (out.argmax(1) == labels).sum().item()
            total        += imgs.size(0)
        train_loss = running_loss / total
        train_acc  = correct / total

        # Val
        model.eval()
        v_loss, v_correct, v_total = 0.0, 0, 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
                out  = model(imgs)
                loss = criterion(out, labels)
                v_loss    += loss.item() * imgs.size(0)
                v_correct += (out.argmax(1) == labels).sum().item()
                v_total   += imgs.size(0)
        val_loss = v_loss / v_total
        val_acc  = v_correct / v_total

        scheduler.step()

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        print(f"Epoch [{epoch:02d}/{EPOCHS}] "
              f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} | "
              f"time={time.time()-t0:.1f}s")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), MODEL_DIR / "drowsiness_best.pt")
            print(f"  ✓ Best model saved (val_acc={val_acc:.4f})")

    # ─── Save history ─────────────────────────────────────────────────────────────
    with open(MODEL_DIR / "train_history.json", "w") as f:
        json.dump(history, f)

    print(f"\nTraining complete. Best val_acc: {best_val_acc:.4f}")
    print(f"Model saved to: {MODEL_DIR / 'drowsiness_best.pt'}")