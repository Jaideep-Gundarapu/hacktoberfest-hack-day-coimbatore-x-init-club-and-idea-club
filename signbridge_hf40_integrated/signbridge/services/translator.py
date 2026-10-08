from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from .gemma import GemmaClient, GemmaError
from .sign_library import SignLibrary


# Lightweight fallback lexicon for offline/demo operation.
FALLBACK = {
    "i": "ME", "me": "ME", "myself": "ME",
    "you": "YOU", "u": "YOU",
    "hello": "HELLO", "hi": "HELLO", "goodbye": "GOODBYE", "bye": "GOODBYE",
    "thanks": "THANK YOU", "thank": "THANK YOU", "thankyou": "THANK YOU", "please": "PLEASE",
    "sorry": "SORRY", "help": "HELP", "assist": "HELP",
    "water": "WATER", "food": "FOOD", "meal": "FOOD", "drink": "DRINK",
    "doctor": "DOCTOR", "docter": "DOCTOR", "physician": "DOCTOR", "hospital": "HOSPITAL",
    "emergency": "EMERGENCY", "urgent": "EMERGENCY", "home": "HOME",
    "school": "SCHOOL", "market": "MARKET", "today": "TODAY", "tomorrow": "TODAY",
    "where": "WHERE", "what": "WHAT", "when": "WHEN", "yes": "YES", "no": "NO",
    "eat": "EAT", "tea": "TEA", "come": "COME", "go": "GO", "sit": "SIT", "stand": "STAND",
    "read": "READ", "write": "WRITE", "friend": "FRIEND", "teacher": "TEACHER", "student": "STUDENT",
    "mother": "MOTHER", "father": "FATHER", "brother": "BROTHER", "sister": "SISTER",
    "okay": "OKAY", "ok": "OKAY", "stop": "STOP", "he": "HE", "she": "SHE",
}

STOPWORDS = {"a", "an", "the", "and", "or", "to", "of", "for", "with", "in", "on", "at", "is", "am", "are", "was", "were", "be", "been", "need", "require", "want"}


def simple_plan(text: str, library: SignLibrary) -> dict[str, Any]:
    tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text.lower())
    concepts: list[str] = []
    missing: list[str] = []
    for token in tokens:
        if token in STOPWORDS:
            continue
        c = FALLBACK.get(token)
        if c and library.resolve(c):
            if not concepts or concepts[-1] != c:
                concepts.append(c)
        elif library.resolve(token):
            label = library.resolve(token).label
            if not concepts or concepts[-1] != label:
                concepts.append(label)
        elif len(token) > 1:
            missing.append(token.upper())
    return {
        "concepts": concepts,
        "missing_concepts": sorted(set(missing)),
        "normalized_sentence": text.strip(),
        "rationale": "Offline fallback: matched common terms against the local + public ISL video vocabulary.",
        "provider": "fallback",
    }


class Translator:
    def __init__(self, library: SignLibrary, gemma: GemmaClient | None, use_gemma: bool):
        self.library = library
        self.gemma = gemma
        self.use_gemma = use_gemma

    def _sequence_for_concepts(self, concepts: list[str], missing: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
        sequence: list[dict[str, Any]] = []
        unavailable_assets: list[str] = []
        for concept in concepts:
            sign = self.library.resolve(concept)
            if not sign:
                continue
            playback = self.library.resolve_playback(sign)
            item = {
                **asdict(sign),
                "mode": "sign",
                **playback,
            }
            sequence.append(item)
            if not playback.get("available"):
                unavailable_assets.append(sign.label)

        # General-text fallback: fingerspell words for which no curated concept sign is available.
        # This is a utility fallback, not a claim of grammatically correct ISL translation.
        for word in missing:
            letters = [ch for ch in word.lower() if "a" <= ch <= "z"]
            if not letters:
                continue
            for ch in letters:
                sign = self.library.resolve(ch)
                if sign:
                    playback = self.library.resolve_playback(sign)
                    sequence.append({
                        **asdict(sign),
                        "mode": "fingerspell",
                        "word_source": word,
                        **playback,
                    })
                else:
                    unavailable_assets.append(f"{word} (fingerspelling incomplete)")
        return sequence, unavailable_assets

    def translate(self, text: str) -> dict[str, Any]:
        text = text.strip()
        if not text:
            raise ValueError("Text cannot be empty")
        plan = None
        error = None
        if self.use_gemma and self.gemma:
            try:
                plan = self.gemma.plan_isl(text, self.library.all_labels())
            except GemmaError as exc:
                error = f"Gemma unavailable; used offline fallback ({exc})"
        if plan is None:
            plan = simple_plan(text, self.library)
        sequence, unavailable_assets = self._sequence_for_concepts(plan["concepts"], plan.get("missing_concepts", []))
        plan["sequence"] = sequence
        plan["unavailable_assets"] = unavailable_assets
        if error:
            plan["warning"] = error
        return plan
