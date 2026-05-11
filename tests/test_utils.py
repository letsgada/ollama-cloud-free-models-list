from unittest.mock import MagicMock, patch

from utils import get_ollama_free_models


def _tags_response(names):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"models": [{"name": n} for n in names]}
    return resp


def _chat_response(status_code):
    resp = MagicMock()
    resp.status_code = status_code
    return resp


class TestGetOllamaFreeModels:
    def test_returns_none_when_tags_endpoint_fails(self):
        with patch("utils.requests.get", side_effect=Exception("boom")):
            assert get_ollama_free_models("k") is None

    def test_returns_empty_list_when_no_probe_succeeds(self):
        with patch(
            "utils.requests.get",
            return_value=_tags_response(["gpt-oss:120b", "glm-4.7"]),
        ), patch("utils.requests.post", return_value=_chat_response(403)):
            assert get_ollama_free_models("k") == []

    def test_returns_empty_list_when_tags_returns_no_models(self):
        with patch("utils.requests.get", return_value=_tags_response([])):
            assert get_ollama_free_models("k") == []

    def test_paid_models_filtered_out(self):
        # glm-4.7 returns 200 (free), paid-model:1t returns 402 (paid).
        def post_side_effect(url, **kwargs):
            return _chat_response(200 if kwargs["json"]["model"] == "glm-4.7" else 402)

        with patch(
            "utils.requests.get",
            return_value=_tags_response(["paid-model:1t", "glm-4.7"]),
        ), patch("utils.requests.post", side_effect=post_side_effect):
            assert get_ollama_free_models("k") == ["glm-4.7"]

    def test_result_sorted_alphabetically(self):
        # Tags returns models in arbitrary order; the result is plain
        # alphabetical (sorted() with no key).
        with patch(
            "utils.requests.get",
            return_value=_tags_response(["zephyr:7b", "gpt-oss:120b", "glm-4.7"]),
        ), patch("utils.requests.post", return_value=_chat_response(200)):
            assert get_ollama_free_models("k") == [
                "glm-4.7",
                "gpt-oss:120b",
                "zephyr:7b",
            ]

    def test_probes_run_sequentially_in_tags_order(self):
        # Invariant: free tier permits 1 concurrent request, so probes
        # MUST be sequential. This test pins that — if a future refactor
        # parallelizes via asyncio/threads, this breaks.
        names = ["gpt-oss:120b", "glm-4.7", "zephyr:7b"]
        post_mock = MagicMock(return_value=_chat_response(200))
        with patch(
            "utils.requests.get", return_value=_tags_response(names)
        ), patch("utils.requests.post", post_mock):
            get_ollama_free_models("k")
        called_models = [c.kwargs["json"]["model"] for c in post_mock.call_args_list]
        assert called_models == names

    def test_probe_exception_is_swallowed_and_skipped(self):
        # If a single model raises (timeout, connection error), it is
        # treated as "not free" and the loop continues.
        def post_side_effect(url, **kwargs):
            if kwargs["json"]["model"] == "flaky:1b":
                raise Exception("timeout")
            return _chat_response(200)

        with patch(
            "utils.requests.get",
            return_value=_tags_response(["gpt-oss:120b", "flaky:1b"]),
        ), patch("utils.requests.post", side_effect=post_side_effect):
            assert get_ollama_free_models("k") == ["gpt-oss:120b"]

    def test_uses_bearer_auth_against_default_base(self):
        get_mock = MagicMock(return_value=_tags_response([]))
        with patch("utils.requests.get", get_mock):
            get_ollama_free_models("secret-key")
        args, kwargs = get_mock.call_args
        assert args[0] == "https://ollama.com/api/tags"
        assert kwargs["headers"] == {"Authorization": "Bearer secret-key"}
