"""Probe Ollama Cloud and return the model names callable on the free tier."""

from typing import List, Optional

import requests


def get_ollama_free_models(
    api_key: str,
    api_base: str = "https://ollama.com",
) -> Optional[List[str]]:
    """Return Ollama Cloud model names callable on the user's free tier.

    Probes every model returned by ``/api/tags`` with a 1-token call to
    ``/api/chat`` and keeps the ones that succeed. Models that respond
    with "subscription required" / "upgrade" are filtered out.

    Args:
        api_key: Ollama Cloud API key.
        api_base: Ollama Cloud base URL (default ``https://ollama.com``).

    Returns:
        Alphabetically sorted list of free-tier model names, or ``None``
        if the ``/api/tags`` endpoint is unreachable. An empty list means
        the endpoint succeeded but no model passed the probe.
    """
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        resp = requests.get(f"{api_base}/api/tags", headers=headers, timeout=10)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return None

    # Probe sequentially: Ollama Cloud's free tier permits only 1
    # concurrent request, so parallel probes get rejected and would
    # cause free models to be misclassified as paid.
    free: List[str] = []
    for name in models:
        try:
            r = requests.post(
                f"{api_base}/api/chat",
                headers=headers,
                json={
                    "model": name,
                    "messages": [{"role": "user", "content": "hi"}],
                    "stream": False,
                    "options": {"num_predict": 1},
                },
                timeout=30,
            )
            if r.status_code == 200:
                free.append(name)
        except Exception:
            continue
    return sorted(free)
