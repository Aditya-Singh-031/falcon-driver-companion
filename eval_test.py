# eval_test.py
import torch, json
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from pathlib import Path

DATA_ROOT = Path("data/ddd")
MODEL_PATH = Path("models/drowsiness_best.pt")
DEVICE = torch.device("cuda")

val_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

full_ds = datasets.ImageFolder(DATA_ROOT, transform=val_tf)
n_total = len(full_ds)
n_val   = int(0.15 * n_total)
n_test  = int(0.10 * n_total)
n_train = n_total - n_val - n_test

_, _, test_ds = torch.utils.data.random_split(
    full_ds, [n_train, n_val, n_test],
    generator=torch.Generator().manual_seed(42)   # same seed → same split
)

test_loader = DataLoader(test_ds, batch_size=64, shuffle=False, num_workers=0)

model = models.efficientnet_b0()
model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 2)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))
model = model.to(DEVICE).eval()

correct, total = 0, 0
with torch.no_grad():
    for imgs, labels in test_loader:
        imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
        correct += (model(imgs).argmax(1) == labels).sum().item()
        total   += labels.size(0)

print(f"Test accuracy: {correct/total:.4f}  ({correct}/{total})")