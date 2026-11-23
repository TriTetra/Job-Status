"""The one LLM gateway: Anthropic (official SDK) or any OpenRouter-compatible API.

    from careeros.shared.llm import get_llm_client
    llm = get_llm_client()                                    # LLMNotConfiguredError without a key
    text = llm.complete("…", task="reasoning", user_id=uid, max_tokens=200)
    facts = llm.complete_model("…", JobFacts, task="job_extract")   # validated pydantic object

Every call names a task. The task picks the model (bulk tasks → the fast model,
LLM_TASK_MODELS overrides) and the budget it draws from. Before a call the usage
guard may refuse it (LLMBudgetExceeded); after it, tokens, cost and latency are
recorded — never the prompt. At most LLM_MAX_CONCURRENCY calls run at once.
On OpenRouter, requests go only to providers that don't collect prompt data
(LLM_DATA_COLLECTION=allow widens that).

Provider: with ANTHROPIC_API_KEY set, calls go straight to Anthropic through the
`anthropic` SDK (interactive tasks on Claude Opus 5.5 with server-side refusal
fallbacks, bulk tasks on Claude Haiku 5.5); otherwise to OpenRouter.

Transient failures (timeouts, connection errors, HTTP 429/5xx) are retried with
exponential backoff; anything else raises immediately. Every LLMError subclass is
a signal for callers with a non-LLM fallback to use it.
"""

import json
import logging
import re
import threading
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional, Protocol, TypeVar

import requests
from pydantic import BaseModel, ValidationError

from careeros.shared.config import get_settings

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$")

# task → budget tier. "bulk" runs unattended over many items (cheap model, capped
# share of the budget); "interactive" is something a user is waiting for.
TASKS = {
    "job_extract": "bulk",
    "hn_extract": "bulk",
    "cv_extract": "interactive",
    "reasoning": "interactive",
    "apply_kit": "interactive",
    "job_add": "interactive",
    "resume": "interactive",
    "general": "interactive",
}

# Cost estimate when the provider doesn't report one (USD per million tokens).
# Deliberately pessimistic so an unreported cost never under-counts the budget.
FALLBACK_PRICE_IN, FALLBACK_PRICE_OUT = 1.0, 4.0

# Anthropic list prices (USD per million input / output tokens); Anthropic doesn't
# return a cost, so it is computed from usage. Unknown models use the fallback above.
ANTHROPIC_PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
}
ANTHROPIC_DEFAULT_MODEL = "claude-opus-5-5"
ANTHROPIC_FAST_MODEL = "claude-haiku-5-5"
# max_tokens is only a ceiling (thinking counts towards it); the prompt sets length
ANTHROPIC_MAX_TOKENS = 16000
# Server-side refusal fallback (Claude Opus 5.5 / Sonnet 5.5 …; Haiku 5.5 has none)
FALLBACK_BETA = "server-side-fallback-2026-07-01"

M = TypeVar("M", bound=BaseModel)


class LLMError(RuntimeError):
    """The LLM call failed or returned something unusable."""


class LLMNotConfiguredError(LLMError):
    """No API key — callers with a non-LLM fallback should catch this."""


class LLMBudgetExceeded(LLMError):
    """Today's budget for this task or user is spent."""


def parse_json(text: str) -> Any:
    """Parse model output as JSON, tolerating ```json fences around it."""
    cleaned = _FENCE_RE.sub("", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMError(f"LLM returned invalid JSON: {e}; head={cleaned[:120]!r}") from e


@dataclass
class CallRecord:
    task: str
    model: str
    user_id: Optional[str]
    status: str                    # ok | error | budget
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    cost_estimated: bool = False
    latency_ms: int = 0
    error: Optional[str] = None


class UsageGuard(Protocol):
    def check(self, task: str, tier: str, user_id: Optional[str]) -> None:
        """Raise LLMBudgetExceeded to refuse the call."""

    def record(self, call: CallRecord) -> None:
        ...


def _cost(usage: dict, model: str = "") -> tuple[float, bool]:
    """(USD, estimated?) — the provider's own figure, a known list price, or a pessimistic guess."""
    if isinstance(usage.get("cost"), (int, float)):
        return float(usage["cost"]), False
    tokens_in, tokens_out = usage.get("prompt_tokens") or 0, usage.get("completion_tokens") or 0
    if model in ANTHROPIC_PRICES:
        price_in, price_out = ANTHROPIC_PRICES[model]
        return (tokens_in * price_in + tokens_out * price_out) / 1_000_000, False
    return (tokens_in * FALLBACK_PRICE_IN + tokens_out * FALLBACK_PRICE_OUT) / 1_000_000, True


class LLMClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1",
        *,
        fast_model: Optional[str] = None,
        task_models: Optional[dict] = None,
        guard: Optional[UsageGuard] = None,
        max_concurrency: int = 4,
        data_collection: str = "deny",
        max_retries: int = 2,
        backoff_seconds: float = 1.0,
        session: Optional[requests.Session] = None,
        provider: str = "openrouter",
        anthropic_client: Any = None,
    ) -> None:
        self.model = model
        self.fast_model = fast_model or model
        self._task_models = task_models or {}
        self._guard = guard
        self._slots = threading.BoundedSemaphore(max(1, max_concurrency))
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._openrouter = "openrouter.ai" in base_url
        self._data_collection = "allow" if data_collection == "allow" else "deny"
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://career-os.local",
            "X-Title": "CareerOS",
        }
        self._max_retries = max_retries
        self._backoff = backoff_seconds
        self._http = session or requests.Session()
        self.provider = provider
        self._anthropic = anthropic_client
        if provider == "anthropic" and anthropic_client is None:
            import anthropic

            self._anthropic = anthropic.Anthropic(api_key=api_key, max_retries=max_retries)

    def model_for(self, task: str) -> str:
        if task in self._task_models:
            return self._task_models[task]
        return self.fast_model if TASKS.get(task) == "bulk" else self.model

    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        task: str = "general",
        user_id: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        json_mode: bool = False,
        timeout: float = 60,
    ) -> str:
        """Return the assistant message text (stripped)."""
        model = self.model_for(task)
        tier = TASKS.get(task, "interactive")
        if self._guard:
            try:
                self._guard.check(task, tier, user_id)
            except LLMBudgetExceeded as e:
                self._record(CallRecord(task, model, user_id, "budget", error=str(e)))
                raise

        started = time.monotonic()
        try:
            with self._slots:
                if self.provider == "anthropic":
                    text, usage, served = self._send_anthropic(
                        model, tier, system, prompt, max_tokens, json_mode, timeout)
                else:
                    text, usage, served = self._send_openai(
                        model, system, prompt, temperature, max_tokens, json_mode, timeout)
        except LLMError as e:
            self._record(CallRecord(task, model, user_id, "error", error=str(e)[:300],
                                    latency_ms=int((time.monotonic() - started) * 1000)))
            raise

        cost, estimated = _cost(usage, served)
        self._record(CallRecord(
            task, served, user_id, "ok",
            prompt_tokens=usage.get("prompt_tokens") or 0,
            completion_tokens=usage.get("completion_tokens") or 0,
            cost_usd=cost, cost_estimated=estimated,
            latency_ms=int((time.monotonic() - started) * 1000),
        ))
        return text

    def _send_openai(self, model, system, prompt, temperature, max_tokens, json_mode, timeout):
        """OpenRouter / OpenAI-compatible chat completions → (text, usage, served model)."""
        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        if self._openrouter:
            payload["usage"] = {"include": True}  # OpenRouter reports the real cost
            # Route only to providers that don't store or train on prompts (CVs, profiles)
            payload["provider"] = {"data_collection": self._data_collection}
        body = self._post(payload, timeout)
        try:
            text = body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as e:
            raise LLMError(f"Unexpected LLM response shape: {str(body)[:200]}") from e
        return text, body.get("usage") or {}, body.get("model") or model

    def _send_anthropic(self, model, tier, system, prompt, max_tokens, json_mode, timeout):
        """Anthropic Messages API via the official SDK → (text, usage, served model).

        Current Claude models think adaptively; effort sets the depth (low for bulk
        extraction, medium for user-facing work). No temperature: these models reject it.
        """
        import anthropic

        if json_mode:
            prompt += "\n\nRespond with a single JSON object and nothing else."
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max(max_tokens, ANTHROPIC_MAX_TOKENS),
            "messages": [{"role": "user", "content": prompt}],
            "output_config": {"effort": "low" if tier == "bulk" else "medium"},
            "timeout": timeout,
        }
        if system:
            kwargs["system"] = system
        try:
            if model.startswith("claude-haiku"):
                response = self._anthropic.messages.create(**kwargs)
            else:
                # On a policy decline the API re-runs the request on a suitable model
                response = self._anthropic.beta.messages.create(
                    betas=[FALLBACK_BETA], fallbacks="default", **kwargs)
        except anthropic.APIStatusError as e:
            raise LLMError(f"Anthropic HTTP {e.status_code}: {str(e.message)[:200]}") from e
        except anthropic.APIConnectionError as e:  # includes timeouts
            raise LLMError(f"Anthropic request failed: {e}") from e

        if response.stop_reason == "refusal":
            raise LLMError("Claude declined this request")
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        if not text:
            raise LLMError(f"Claude returned no text (stop_reason={response.stop_reason})")
        usage = {"prompt_tokens": response.usage.input_tokens, "completion_tokens": response.usage.output_tokens}
        return text, usage, response.model

    def complete_json(self, prompt: str, **kwargs: Any) -> Any:
        """complete() + parse_json(). Pass json_mode=True to force a JSON object."""
        return parse_json(self.complete(prompt, **kwargs))

    def complete_model(self, prompt: str, schema: type[M], *, retries: int = 1, **kwargs: Any) -> M:
        """JSON output validated against a pydantic model. On invalid output the model
        is asked once more, shown the validation error."""
        kwargs.setdefault("json_mode", True)
        attempt_prompt = prompt
        for attempt in range(retries + 1):
            raw = self.complete(attempt_prompt, **kwargs)
            try:
                return schema.model_validate(parse_json(raw))
            except (LLMError, ValidationError) as e:
                if attempt == retries:
                    raise LLMError(f"LLM output failed {schema.__name__} validation: {str(e)[:300]}") from e
                attempt_prompt = (
                    f"{prompt}\n\nYour previous answer was invalid:\n{str(e)[:800]}\n"
                    "Return only a corrected JSON object."
                )
        raise AssertionError("unreachable")

    def _record(self, call: CallRecord) -> None:
        if not self._guard:
            return
        try:
            self._guard.record(call)
        except Exception:  # bookkeeping must never break the feature
            logger.exception("Could not record LLM call")

    def _post(self, payload: dict, timeout: float) -> dict:
        for attempt in range(self._max_retries + 1):
            last = attempt == self._max_retries
            try:
                resp = self._http.post(self._url, json=payload, headers=self._headers, timeout=timeout)
            except (requests.Timeout, requests.ConnectionError) as e:
                if last:
                    raise LLMError(f"LLM request failed: {e}") from e
                self._sleep(attempt, reason=type(e).__name__)
                continue
            if resp.status_code in _RETRYABLE_STATUS and not last:
                self._sleep(attempt, reason=f"HTTP {resp.status_code}")
                continue
            if resp.status_code >= 400:
                raise LLMError(f"LLM HTTP {resp.status_code}: {resp.text[:200]}")
            try:
                return resp.json()
            except ValueError as e:
                raise LLMError(f"LLM returned a non-JSON body: {resp.text[:120]!r}") from e
        raise AssertionError("unreachable")

    def _sleep(self, attempt: int, reason: str) -> None:
        delay = self._backoff * (2 ** attempt)
        logger.warning("LLM call %s — retry %d/%d in %.1fs", reason, attempt + 1, self._max_retries, delay)
        time.sleep(delay)


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Process-wide client built from settings, with budgets and the llm_calls log."""
    from careeros.shared.llm_usage import DbUsageGuard

    s = get_settings()
    if s.llm_provider == "anthropic":
        api_key = s.anthropic_api_key
    else:
        api_key = s.openrouter_api_key
    if not api_key:
        raise LLMNotConfiguredError("No LLM key: set ANTHROPIC_API_KEY or OPENROUTER_API_KEY")
    return LLMClient(
        api_key=api_key,
        provider=s.llm_provider,
        model=s.llm_model,
        base_url=s.llm_base_url,
        fast_model=s.llm_fast_model,
        task_models=s.llm_task_models,
        guard=DbUsageGuard(s.llm_daily_budget_usd, s.llm_user_daily_budget_usd, s.llm_bulk_budget_share),
        max_concurrency=s.llm_max_concurrency,
        data_collection=s.llm_data_collection,
    )
