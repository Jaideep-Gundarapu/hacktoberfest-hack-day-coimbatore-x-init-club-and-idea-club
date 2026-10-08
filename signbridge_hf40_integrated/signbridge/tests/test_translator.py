from pathlib import Path
from services.isl_dataset import DATASET_VOCAB
from services.sign_library import SignLibrary
from services.translator import simple_plan
from app.config import SIGN_MANIFEST, ASSETS_DIR


def test_fallback_basic_sentence():
    lib = SignLibrary(SIGN_MANIFEST, ASSETS_DIR)
    result = simple_plan('I need water', lib)
    assert result['concepts'] == ['ME', 'WATER']
    assert 'I' not in DATASET_VOCAB
    assert 'NEED' not in DATASET_VOCAB


def test_aliases():
    lib = SignLibrary(SIGN_MANIFEST, ASSETS_DIR)
    result = simple_plan('hi thanks', lib)
    assert result['concepts'] == ['HELLO', 'THANK YOU']


def test_ignores_articles_and_common_misspelling():
    lib = SignLibrary(SIGN_MANIFEST, ASSETS_DIR)
    result = simple_plan('I need a doctor', lib)
    assert result['concepts'] == ['ME', 'DOCTOR']
    assert simple_plan('docter', lib)['concepts'] == ['DOCTOR']
