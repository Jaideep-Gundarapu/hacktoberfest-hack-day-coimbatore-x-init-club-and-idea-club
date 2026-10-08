from pathlib import Path

from services.isl_dataset import DATASET_VOCAB, HFISLVideoDataset, normalize


def test_dataset_vocab_contains_demo_words():
    assert "WATER" in DATASET_VOCAB
    assert "HELP" in DATASET_VOCAB
    assert "THANK YOU" in DATASET_VOCAB


def test_normalize_words():
    assert normalize("Thank-you!") == "thank you"
    assert normalize("  Water  ") == "water"


def test_provider_cache_dir(tmp_path: Path):
    provider = HFISLVideoDataset(cache_dir=tmp_path, enabled=False)
    assert provider.labels() == DATASET_VOCAB
