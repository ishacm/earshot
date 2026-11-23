"""One LLM client with a switchable provider.

EARSHOT_LLM=mock   deterministic local handlers (earshot/mock_llm.py) for tests, CI and the demo.
                   Mock output is never a source of real findings.
EARSHOT_LLM=live   the provider in config.yaml (override with EARSHOT_PROVIDER). Free mode = Groq.

Zero-cost guard: providers marked paid are refused unless EARSHOT_ALLOW_PAID=true.
"""
import json
import os
import re
import time

from earshot.config import CONFIG

LLM = CONFIG["llm"]
USAGE = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "failed": 0}


class PaidProviderError(RuntimeError):
    pass


class RateLimited(RuntimeError):
    def __init__(self, wait: float):
        super().__init__(f"rate limited, retry after {wait}s")
        self.wait = min(wait, 60.0)


def mode() -> str:
    return os.environ.get("EARSHOT_LLM", "live")


def provider() -> dict:
    pid = os.environ.get("EARSHOT_PROVIDER", LLM["provider"])
    if pid not in LLM["providers"]:
        raise KeyError(f"unknown provider '{pid}'; options: {', '.join(LLM['providers'])}")
    return {"id": pid, **LLM["providers"][pid]}


def check_cost(prov: dict) -> None:
    if prov.get("paid") and os.environ.get("EARSHOT_ALLOW_PAID", "").lower() != "true":
        raise PaidProviderError(f"provider '{prov['id']}' costs money; set EARSHOT_ALLOW_PAID=true deliberately "
                                f"or use the free provider (groq).")


def parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", (text or "").strip(), re.S)
    if not m:
        raise ValueError(f"no JSON object in model output: {(text or '')[:200]}")
    return json.loads(m.group(0))


def _call(prov: dict, model: str, prompt: str, max_tokens: int) -> tuple[str, int, int]:
    if prov["kind"] == "anthropic":
        import anthropic
        msg = anthropic.Anthropic().messages.create(model=model, max_tokens=max_tokens,
                                                    messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text, msg.usage.input_tokens, msg.usage.output_tokens
    import httpx
    key = os.environ.get(prov.get("key_env") or "", "")
    if prov.get("key_env") and not key:
        raise RuntimeError(f"{prov['key_env']} is not set (see .env.example), or run with EARSHOT_LLM=mock")
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max(max_tokens, prov.get("min_max_tokens", 0))}
    extra = prov.get("extra") or {}
    url = f"{prov['base_url'].rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    r = httpx.post(url, timeout=90, headers=headers, json={**body, **extra})
    if r.status_code == 400 and extra:
        r = httpx.post(url, timeout=90, headers=headers, json=body)
    if r.status_code == 429:
        raise RateLimited(float(r.headers.get("retry-after", "5") or 5))
    r.raise_for_status()
    data = r.json()
    u = data.get("usage") or {}
    return data["choices"][0]["message"].get("content") or "", u.get("prompt_tokens", 0), u.get("completion_tokens", 0)


def complete_json(prompt: str, purpose: str, *, context: dict | None = None, max_tokens: int = 1500,
                  retries: int = 2) -> dict:
    if mode() == "mock":
        from earshot.mock_llm import handle
        USAGE["calls"] += 1
        return handle(purpose, prompt, context or {})
    prov = provider()
    check_cost(prov)
    model = os.environ.get("EARSHOT_MODEL") or prov.get("model")
    if not model:
        raise RuntimeError(f"no model set for provider '{prov['id']}' in config.yaml")
    err = None
    for attempt in range(retries + 1):
        try:
            text, tin, tout = _call(prov, model, prompt, max_tokens)
            out = parse_json(text)
            USAGE["calls"] += 1
            USAGE["input_tokens"] += tin
            USAGE["output_tokens"] += tout
            return out
        except RateLimited as e:
            err = e
            time.sleep(e.wait)
        except Exception as e:  # malformed JSON, timeout, server error
            err = e
            time.sleep(1.5 * (attempt + 1))
    USAGE["failed"] += 1
    raise RuntimeError(f"LLM call failed after {retries + 1} attempts ({purpose}): {err}")
