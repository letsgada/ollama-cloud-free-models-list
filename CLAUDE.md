# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

A scheduled job (GitHub Action, runs daily at 09:00 UTC) probes Ollama Cloud and produces `models.json` listing the model names callable on the **free tier**. Detection works by issuing a 1-token `/api/chat` call against every model returned by `/api/tags` and keeping the ones that respond `200`. The action commits `models.json` back to `main` and also publishes it via GitHub Pages.

## Key behaviors of `get_ollama_free_models` (utils.py)

These are load-bearing — preserve when refactoring:

- **Sequential probing only.** Ollama Cloud's free tier allows 1 concurrent request; parallel probes get rejected and would misclassify free models as paid. Do not switch to `asyncio.gather` / threading. There is a unit test (`test_probes_run_sequentially_in_tags_order`) that pins this.
- **Bearer auth** against `https://ollama.com` by default.
- **Three return states** — callers must distinguish all three:
  - `None` → `/api/tags` was unreachable (network error, 5xx, etc.). Caller should treat this as a transient failure and *not* overwrite previously-good output.
  - `[]` → `/api/tags` succeeded but no model passed the 1-token probe.
  - `[...names...]` → free-tier names, sorted **alphabetically** (plain `sorted()`).

## Layout

- `utils.py` — `get_ollama_free_models()` + sort logic.
- `main.py` — entry point. Calls `load_dotenv()`, reads `OLLAMA_API_KEY`, writes `models.json` as `{"updated_at": ..., "models": [...]}`. Exits non-zero (without overwriting `models.json`) if the key is missing or `get_ollama_free_models` returns `None`.
- `tests/test_utils.py` — unit tests, fully mocked (no network).
- `tests/test_integration.py` — live test against ollama.com. **Fails loudly** (does not skip) when `OLLAMA_API_KEY` is absent — by design.
- `.github/workflows/update-models.yml` — daily cron + `workflow_dispatch`. Probes, commits `models.json` if changed, then deploys a `_site/` containing `models.json` + minimal `index.html` to GitHub Pages.

## Environment

- Python `>=3.10` (`.python-version` pins 3.10).
- `OLLAMA_API_KEY` lives in `.env` for local runs (gitignored) and as a repo secret for the action.
- Pages source must be set to "GitHub Actions" in repo Settings → Pages. One-time setup.

## Commands

```
uv sync                                      # install deps
uv run pytest tests/test_utils.py -v         # unit tests, no network
uv run pytest tests/test_integration.py -v   # live test, needs OLLAMA_API_KEY
uv run python main.py                        # generate models.json locally
```
