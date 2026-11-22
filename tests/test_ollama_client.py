import httpx
import pytest

from challenge.ai.base import LLMError
from challenge.ai.factory import build_llm
from challenge.ai.ollama import OllamaClient
from challenge.config import Settings


def _client(handler, **kw):
    return OllamaClient(
        model="m",
        base_url="http://x",
        timeout_s=5,
        max_retries=3,
        retry_base_delay_s=0,
        transport=httpx.MockTransport(handler),
        **kw,
    )


def test_chama_api_chat_com_json_e_temperatura_zero():
    seen = {}

    def handler(request):
        seen.update(url=str(request.url), body=request.read())
        return httpx.Response(200, json={"message": {"content": '{"tensao": "Alta"}'}})

    assert _client(handler).complete_json("sys", "user") == {"tensao": "Alta"}
    assert seen["url"] == "http://x/api/chat"
    assert b'"format":"json"' in seen["body"].replace(b" ", b"") and b'"temperature":0' in seen[
        "body"
    ].replace(b" ", b"")


def test_retry_em_5xx_e_json_invalido():
    replies = iter(
        [
            httpx.Response(503),
            httpx.Response(200, json={"message": {"content": "sem json"}}),
            httpx.Response(200, json={"message": {"content": '```json\n{"a": 1}\n```'}}),
        ]
    )
    assert _client(lambda r: next(replies)).complete_json("s", "u") == {"a": 1}


def test_erro_4xx_nao_e_retentado():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(404, text="model not found")

    with pytest.raises(LLMError, match="404"):
        _client(handler).complete_json("s", "u")
    assert len(calls) == 1


def test_factory_ollama(tmp_path):
    s = Settings(base_dir=tmp_path, llm_provider="ollama")
    assert isinstance(build_llm(s), OllamaClient)
