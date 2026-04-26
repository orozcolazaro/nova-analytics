import os
from dataclasses import dataclass
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from anthropic import APIStatusError, APIConnectionError, RateLimitError


_singleton: Anthropic | None = None


def _get_client() -> Anthropic:
    global _singleton
    if _singleton is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        _singleton = Anthropic(api_key=api_key)
    return _singleton


@dataclass(frozen=True)
class CachedPrompt:
    """A two-block system prompt: static (cached) + dynamic (per-call)."""
    static: str
    dynamic: str = ""

    def to_system_blocks(self) -> list[dict]:
        blocks = [{"type": "text", "text": self.static, "cache_control": {"type": "ephemeral"}}]
        if self.dynamic:
            blocks.append({"type": "text", "text": self.dynamic})
        return blocks


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIStatusError)),
    reraise=True,
)
def call_claude(
    model: str,
    system: CachedPrompt,
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> str:
    """Single-turn call. Returns the assistant's text content."""
    client = _get_client()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system.to_system_blocks(),
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text
