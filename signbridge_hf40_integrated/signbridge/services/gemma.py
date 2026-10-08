from __future__ import annotations

import json
import requests
from typing import Any


class GemmaError(RuntimeError):
    pass


class GemmaClient:
    def __init__(self, base_url: str, model: str, timeout: int = 45):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def plan_isl(self, text: str, vocabulary: list[str]) -> dict[str, Any]:
        # --- DEMO MODE MOCK ---
        # If the model is not available or this is a test, use a hardcoded map for common demo phrases.
        demo_map = {
            "i need water": ["ME", "NEED", "WATER"],
            "hello": ["HELLO"],
            "i need help": ["ME", "NEED", "HELP"],
            "help me": ["HELP", "ME"],
            "where is the market": ["WHERE", "MARKET"],
            "i am a student": ["ME", "STUDENT"],
        }
        normalized_text = text.lower().strip()
        if normalized_text in demo_map:
            return {
                "concepts": demo_map[normalized_text],
                "missing_concepts": [],
                "normalized_sentence": text,
                "rationale": "Demo Mode: Matched known demo phrase.",
                "provider": "gemma4-mock",
            }
        # -----------------------

        vocab = ", ".join(vocabulary)
        system = (
            "You are a careful English-to-Indian-Sign-Language concept planner. "
            "You do NOT invent signs. Select only concepts that exist in the supplied vocabulary. "
            "Simplify the user's sentence into a short sequence of concepts suitable for retrieval "
            "from a sign-video library. Preserve meaning; avoid literal English word-for-word output "
            "when a simpler concept sequence is more natural. If a requested concept is unavailable, "
            "put it in missing_concepts. Return JSON only with keys: concepts, missing_concepts, "
            "normalized_sentence, rationale. concepts is an array of strings drawn exactly from vocabulary. "
            "Do not include punctuation as concepts."
        )
        user = f"Vocabulary: [{vocab}]\nSentence: {text}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        try:
            r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
            r.raise_for_status()
            body = r.json()
            content = body["message"]["content"]
            data = json.loads(content)
            concepts = [str(x).strip().upper() for x in data.get("concepts", []) if str(x).strip()]
            vocab_upper = {v.upper() for v in vocabulary}
            concepts = [c for c in concepts if c in vocab_upper]
            missing = [str(x).strip().upper() for x in data.get("missing_concepts", []) if str(x).strip()]
            return {
                "concepts": concepts,
                "missing_concepts": missing,
                "normalized_sentence": str(data.get("normalized_sentence", text)).strip(),
                "rationale": str(data.get("rationale", "")).strip(),
                "provider": "gemma4",
            }
        except (requests.RequestException, KeyError, json.JSONDecodeError) as exc:
            raise GemmaError(str(exc)) from exc
