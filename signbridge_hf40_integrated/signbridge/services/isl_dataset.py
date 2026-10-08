from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# Small, hackathon-friendly public ISL video corpus on Hugging Face.
# It contains 642 H.264 clips covering 40 isolated ISL glosses.
DATASET_REPO = "vidit031/isl-isolated-40words"
DATASET_VOCAB = [
    "HELLO", "GOODBYE", "THANK YOU", "SORRY", "PLEASE", "YES", "NO", "HELP",
    "STOP", "OKAY", "ME", "YOU", "HE", "SHE", "MOTHER", "FATHER", "BROTHER",
    "SISTER", "FRIEND", "TEACHER", "STUDENT", "HOME", "SCHOOL", "HOSPITAL",
    "MARKET", "EAT", "DRINK", "WATER", "FOOD", "TEA", "COME", "GO", "SIT",
    "STAND", "READ", "WRITE", "WHAT", "WHERE", "WHEN", "TODAY",
]


@dataclass(frozen=True)
class DatasetAsset:
    label: str
    local_path: Path
    source_dataset: str
    license: str
    original_filename: str
    dataset_path: str
    quality_score: float
    review_status: str

    @property
    def relative_url(self) -> str:
        # The application serves assets/signs at /assets/signs.
        rel = self.local_path.as_posix().split("assets/signs/", 1)[-1]
        return f"/assets/signs/{rel}"


class DatasetError(RuntimeError):
    pass


def normalize(value: str) -> str:
    value = value.strip().lower().replace("_", " ")
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _license_rank(value: str) -> int:
    text = (value or "").lower()
    # Prefer rows whose metadata names a redistributable/open license explicitly.
    if "cc-by-4.0" in text or "cc by 4.0" in text:
        return 4
    if "mit" in text:
        return 3
    if "afl-3.0" in text or "afl 3.0" in text:
        return 2
    if "research" in text:
        return 0
    return 1


class HFISLVideoDataset:
    """Lazy loader for the 40-word ISL video dataset.

    Only metadata is downloaded first. A video clip is fetched when a requested
    concept actually needs playback, so the first run does not pull the whole corpus.
    """

    def __init__(self, repo_id: str = DATASET_REPO, cache_dir: Path | None = None, enabled: bool = True):
        self.repo_id = repo_id
        self.cache_dir = cache_dir or Path("assets/signs/_hf40")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.enabled = enabled
        self._rows: list[dict[str, Any]] | None = None
        self._selected: dict[str, dict[str, Any] | None] = {}

    def labels(self) -> list[str]:
        return DATASET_VOCAB.copy()

    def _client(self):
        if not self.enabled:
            raise DatasetError("Hugging Face ISL dataset integration is disabled")
        try:
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise DatasetError("Install huggingface-hub to enable the ISL video dataset") from exc
        return hf_hub_download

    def _load_rows(self) -> list[dict[str, Any]]:
        if self._rows is not None:
            return self._rows
        downloader = self._client()
        try:
            metadata_path = Path(
                downloader(
                    repo_id=self.repo_id,
                    repo_type="dataset",
                    filename="metadata.csv",
                    local_dir=str(self.cache_dir / "metadata"),
                )
            )
            with metadata_path.open("r", encoding="utf-8", newline="") as fh:
                self._rows = list(csv.DictReader(fh))
        except Exception as exc:  # network/auth/file errors should not crash the app
            raise DatasetError(f"Could not load ISL dataset metadata: {exc}") from exc
        return self._rows

    def _pick_row(self, label: str) -> dict[str, Any] | None:
        key = normalize(label)
        if key in self._selected:
            return self._selected[key]
        try:
            rows = self._load_rows()
        except DatasetError:
            self._selected[key] = None
            return None

        candidates = [
            r for r in rows
            if normalize(str(r.get("normalized_word") or r.get("word") or "")) == key
            or normalize(str(r.get("word") or "")) == key
        ]
        if not candidates:
            self._selected[key] = None
            return None

        accepted = [r for r in candidates if str(r.get("review_status", "")).lower() == "accepted"]
        if accepted:
            candidates = accepted
        candidates.sort(
            key=lambda r: (
                _license_rank(str(r.get("license", ""))),
                float(r.get("quality_score") or 0),
                -float(r.get("duration") or 9999),
            ),
            reverse=True,
        )
        self._selected[key] = candidates[0]
        return candidates[0]

    def ensure_asset(self, label: str) -> DatasetAsset | None:
        row = self._pick_row(label)
        if not row:
            return None

        dataset_path = str(row.get("video_path") or "").replace("\\", "/").strip()
        if not dataset_path or dataset_path.startswith("/") or ".." in Path(dataset_path).parts:
            raise DatasetError(f"Unsafe dataset path for {label!r}")

        source_dataset = str(row.get("dataset") or "unknown")
        original_filename = str(row.get("original_filename") or Path(dataset_path).name)
        output_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(dataset_path).name)
        output_dir = self.cache_dir / "videos" / normalize(label).replace(" ", "_")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_name

        if not output_path.exists():
            downloader = self._client()
            try:
                downloaded = Path(
                    downloader(
                        repo_id=self.repo_id,
                        repo_type="dataset",
                        filename=dataset_path,
                        local_dir=str(self.cache_dir / "download"),
                    )
                )
                output_path.write_bytes(downloaded.read_bytes())
            except Exception as exc:
                raise DatasetError(f"Could not download sign video for {label!r}: {exc}") from exc

        return DatasetAsset(
            label=str(row.get("word") or label).strip().upper(),
            local_path=output_path,
            source_dataset=source_dataset,
            license=str(row.get("license") or "unknown"),
            original_filename=original_filename,
            dataset_path=dataset_path,
            quality_score=float(row.get("quality_score") or 0),
            review_status=str(row.get("review_status") or ""),
        )
