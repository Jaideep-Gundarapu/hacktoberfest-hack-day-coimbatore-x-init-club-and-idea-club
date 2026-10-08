# SignBridge

**AI-assisted English → Indian Sign Language concept-to-animation prototype.**

SignBridge takes English text, uses Gemma 4 (when enabled) to reduce it to a sequence of concepts from an ISL vocabulary, and plays corresponding ISL sign videos sequentially.

## Public ISL video dataset integration

The project now integrates the Hugging Face **`vidit031/isl-isolated-40words`** corpus as an on-demand sign-video source. The corpus contains **642 H.264 MP4 clips covering 40 isolated ISL glosses**, with per-clip provenance in `metadata.csv`.

The application does **not** download the whole dataset at startup. It downloads `metadata.csv` first, and when a requested sign video is missing locally it downloads only one suitable clip and caches it under `assets/signs/_hf40/`.

Dataset page:
https://huggingface.co/datasets/vidit031/isl-isolated-40words

The dataset is a **multi-source aggregate**. Its metadata reports different upstream licenses, so do not blindly redistribute cached clips as if they were all under one license. The app exposes the selected source and license in the API response. Cite and follow the upstream terms for the clips you use.

## Architecture

`User text → Gemma 4 semantic planner → allowed ISL concept sequence → ISL video dataset/local library → sequential player`

## Project structure

- `app/main.py` — FastAPI application
- `services/gemma.py` — local Gemma/Ollama adapter
- `services/translator.py` — semantic planning + playback sequence generation
- `services/sign_library.py` — local manifest + dataset-backed sign resolver
- `services/isl_dataset.py` — lazy Hugging Face ISL video integration
- `data/signs.json` — local sign aliases/manifest
- `assets/signs/` — optional user-supplied licensed sign assets
- `assets/signs/_hf40/` — cached dataset clips (created automatically)
- `static/` — frontend
- `scripts/check_dataset.py` — metadata connectivity/integration check
- `tests/` — unit tests

## Requirements

Python 3.11+ recommended.

### Install

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### Run with the integrated public dataset

The default configuration enables the dataset integration.

```bash
python scripts/check_dataset.py
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

The first translation of a dataset-backed word may take a little longer because the clip is fetched and cached. Later plays use the cached local copy.

### Run offline

Set in `.env`:

```dotenv
USE_GEMMA=false
USE_HF_ISL_DATASET=false
```

Then place your own licensed sign videos in `assets/signs/` and ensure their filenames match `data/signs.json`.

## Gemma 4

Install Ollama and pull a compact Gemma 4 model, for example:

```bash
ollama run gemma4:e2b-it-q4_K_M
```

Set:

```dotenv
USE_GEMMA=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e2b-it-q4_K_M
```

Gemma is used for **semantic concept planning**, not for hallucinating or synthesizing sign motion. The actual motion is retrieved from the sign library/dataset.

## What the MVP can do

Examples supported by the integrated 40-word vocabulary include:

- `Hello`
- `Thank you`
- `I need water` (using the dataset-backed `ME`/`WATER` concepts where available, plus any local assets)
- `I need help`
- `Go to the hospital`
- `Where is the market?`
- `Please help`
- `Mother` / `father` / `friend` / `teacher` / `student`

Because this is a concept-to-retrieval prototype, the result is **not a claim of complete grammatical English→ISL translation**. ISL and English are different languages, and the ISLRTC dictionary documents context-dependent mappings and multiple possible signs for some English terms.

## Why this dataset choice

The selected dataset is practical for a hackathon because it is only about **196 MB** and contains 40 common isolated signs. It is small enough to use for a demo while still being a real video corpus rather than manually fabricated placeholder clips.

For a larger deployment, replace or augment this provider with the official ISLRTC dictionary resources and a proper ISL grammar/concept layer reviewed by Deaf/ISL experts.

## Tests

```bash
pytest -q
```
