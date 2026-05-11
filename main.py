import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from utils import get_ollama_free_models

OUTPUT = Path(__file__).parent / "models.json"


def main() -> int:
    load_dotenv()
    api_key = os.environ.get("OLLAMA_API_KEY")
    if not api_key:
        print("OLLAMA_API_KEY not set", file=sys.stderr)
        return 1

    models = get_ollama_free_models(api_key)
    if models is None:
        # Tags endpoint unreachable. Don't overwrite models.json — leave
        # yesterday's good data in place and fail the job loudly.
        print("Failed to fetch models from Ollama Cloud /api/tags", file=sys.stderr)
        return 1

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "models": models,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {len(models)} models to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
