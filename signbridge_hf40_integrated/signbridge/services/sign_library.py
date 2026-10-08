from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .isl_dataset import DATASET_VOCAB, DatasetAsset, DatasetError, HFISLVideoDataset


@dataclass(frozen=True)
class Sign:
    id: str
    label: str
    filename: str
    aliases: tuple[str, ...]


class SignLibrary:
    def __init__(self, manifest_path: Path, asset_dir: Path, dataset_provider: HFISLVideoDataset | None = None):
        self.manifest_path = manifest_path
        self.asset_dir = asset_dir
        self.dataset = dataset_provider
        self.signs = self._load()
        self._index: dict[str, Sign] = {}
        for sign in self.signs:
            for key in {sign.id, sign.label.lower(), *[a.lower() for a in sign.aliases]}:
                self._index[key] = sign

    def _load(self) -> list[Sign]:
        raw = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        seen: set[str] = set()
        out: list[Sign] = []
        for item in raw.get("signs", []):
            sid = item["id"].strip().lower()
            if sid in seen:
                continue
            seen.add(sid)
            out.append(Sign(
                id=sid,
                label=item["label"],
                filename=item["filename"],
                aliases=tuple(item.get("aliases", [])),
            ))

        # Make every dataset gloss resolvable even if it is not hand-entered in signs.json.
        existing_labels = {s.label.strip().lower() for s in out}
        for label in DATASET_VOCAB:
            key = label.strip().lower()
            if key in existing_labels:
                continue
            sid = key.replace(" ", "-")
            out.append(Sign(id=sid, label=label, filename=f"{sid}.mp4", aliases=tuple()))
        return out

    def all_labels(self) -> list[str]:
        labels = {s.label for s in self.signs}
        if self.dataset:
            labels.update(self.dataset.labels())
        return sorted(labels)

    def resolve(self, concept: str) -> Sign | None:
        return self._index.get(concept.strip().lower())

    def resolve_many(self, concepts: Iterable[str]) -> list[Sign]:
        out = []
        for c in concepts:
            sign = self.resolve(c)
            if sign:
                out.append(sign)
        return out

    def local_asset_path(self, sign: Sign) -> Path:
        return self.asset_dir / sign.filename

    def asset_exists(self, sign: Sign) -> bool:
        return self.local_asset_path(sign).exists()

    def resolve_playback(self, sign: Sign) -> dict:
        local = self.local_asset_path(sign)
        if local.exists():
            return {
                "available": True,
                "asset_url": f"/assets/signs/{sign.filename}",
                "source": "local",
                "license": "user-supplied",
            }
        if self.dataset:
            try:
                asset = self.dataset.ensure_asset(sign.label)
                if asset:
                    return {
                        "available": True,
                        "asset_url": asset.relative_url,
                        "source": "huggingface",
                        "source_dataset": asset.source_dataset,
                        "license": asset.license,
                        "original_filename": asset.original_filename,
                        "dataset_path": asset.dataset_path,
                        "quality_score": asset.quality_score,
                        "review_status": asset.review_status,
                    }
            except DatasetError as exc:
                return {
                    "available": False,
                    "asset_url": None,
                    "source": "huggingface",
                    "dataset_error": str(exc),
                }
        return {"available": False, "asset_url": None, "source": None}
