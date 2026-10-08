from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b-it-q4_K_M")
USE_GEMMA = os.getenv("USE_GEMMA", "true").lower() in {"1", "true", "yes", "on"}
USE_HF_ISL_DATASET = os.getenv("USE_HF_ISL_DATASET", "true").lower() in {"1", "true", "yes", "on"}
HF_ISL_DATASET_REPO = os.getenv("HF_ISL_DATASET_REPO", "vidit031/isl-isolated-40words")

DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets" / "signs"
STATIC_DIR = ROOT / "static"
SIGN_MANIFEST = DATA_DIR / "signs.json"
