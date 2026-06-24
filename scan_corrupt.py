# run_once: scan_corrupt.py
from pathlib import Path
from PIL import Image

data_root = Path("data/ddd")
bad = []

for img_path in data_root.rglob("*"):
    if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        continue
    try:
        with Image.open(img_path) as img:
            img.verify()        # catches truncated/broken headers
    except Exception as e:
        bad.append((img_path, str(e)))

print(f"Found {len(bad)} corrupt images:")
for p, err in bad:
    print(f"  {p}  —  {err}")


# add this after printing to actually remove them
for p, _ in bad:
    p.unlink()
    print(f"Deleted: {p}")