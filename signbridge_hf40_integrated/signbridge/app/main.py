from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import (ASSETS_DIR, STATIC_DIR, SIGN_MANIFEST, OLLAMA_BASE_URL, OLLAMA_MODEL, USE_GEMMA, USE_HF_ISL_DATASET, HF_ISL_DATASET_REPO)
from services.gemma import GemmaClient
from services.sign_library import SignLibrary
from services.isl_dataset import HFISLVideoDataset
from services.translator import Translator

app = FastAPI(title="SignBridge", version="1.0.0")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

dataset = HFISLVideoDataset(repo_id=HF_ISL_DATASET_REPO, cache_dir=ASSETS_DIR / "_hf40", enabled=USE_HF_ISL_DATASET)
library = SignLibrary(SIGN_MANIFEST, ASSETS_DIR, dataset_provider=dataset)
gemma = GemmaClient(OLLAMA_BASE_URL, OLLAMA_MODEL) if USE_GEMMA else None
translator = Translator(library, gemma, USE_GEMMA)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/assets/signs", StaticFiles(directory=ASSETS_DIR), name="sign-assets")


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "gemma_enabled": USE_GEMMA,
        "gemma_model": OLLAMA_MODEL if USE_GEMMA else None,
        "vocabulary_size": len(library.all_labels()),
        "loaded_assets": sum(library.asset_exists(s) for s in library.signs),
        "huggingface_dataset_enabled": USE_HF_ISL_DATASET,
        "huggingface_dataset": HF_ISL_DATASET_REPO if USE_HF_ISL_DATASET else None,
    }


@app.get("/api/signs")
def signs():
    return {
        "vocabulary": [
            {
                "label": s.label,
                "filename": s.filename,
                "local_available": library.asset_exists(s),
                "dataset_available": bool(dataset._pick_row(s.label)) if USE_HF_ISL_DATASET else False,
            }
            for s in library.signs
        ]
    }


@app.post("/api/translate")
def translate(req: TranslateRequest):
    try:
        return translator.translate(req.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
