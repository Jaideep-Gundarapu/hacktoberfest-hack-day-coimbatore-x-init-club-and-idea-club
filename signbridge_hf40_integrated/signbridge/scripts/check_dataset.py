from __future__ import annotations

from pathlib import Path
from services.isl_dataset import DATASET_REPO, HFISLVideoDataset

ROOT = Path(__file__).resolve().parents[1]
provider = HFISLVideoDataset(DATASET_REPO, ROOT / "assets" / "signs" / "_hf40", enabled=True)
print(f"Dataset: {DATASET_REPO}")
print(f"Vocabulary: {len(provider.labels())} glosses")
print(", ".join(provider.labels()))

try:
    # Metadata-only check; no video is downloaded.
    rows = provider._load_rows()
    print(f"Metadata rows: {len(rows)}")
    available = {str(r.get('normalized_word') or r.get('word') or '').strip().lower() for r in rows}
    missing = [x for x in provider.labels() if x.lower() not in available]
    print(f"Glosses found in metadata: {len(provider.labels()) - len(missing)}")
    if missing:
        print("Not found:", ", ".join(missing))
except Exception as exc:
    print("Dataset check failed:", exc)
    raise SystemExit(1)
