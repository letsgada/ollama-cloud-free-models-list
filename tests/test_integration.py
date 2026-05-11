"""Live integration test against ollama.com.

Fails loudly (not skips) when OLLAMA_API_KEY is missing — this is
intentional so the test never silently passes in environments where
the secret hasn't been wired up.
"""

import os

from dotenv import load_dotenv

from utils import get_ollama_free_models


def test_returns_real_free_models():
    load_dotenv()
    api_key = os.environ.get("OLLAMA_API_KEY")
    assert api_key, (
        "OLLAMA_API_KEY must be set in .env or the environment to run "
        "the integration test."
    )

    models = get_ollama_free_models(api_key)

    assert isinstance(models, list)
    assert models, "expected at least one free-tier model"
    assert all(isinstance(m, str) and m for m in models)
