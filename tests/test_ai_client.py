from unittest.mock import MagicMock
from scraper.ai.client import call_claude, CachedPrompt


def test_cached_prompt_builds_blocks():
    cp = CachedPrompt(static="System rules go here", dynamic="company-specific data")
    blocks = cp.to_system_blocks()
    assert blocks[0]["text"] == "System rules go here"
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert blocks[1]["text"] == "company-specific data"
    assert "cache_control" not in blocks[1]


def test_call_claude_returns_text(monkeypatch):
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.content = [MagicMock(text='{"ok": true}')]
    fake_client.messages.create.return_value = fake_response

    monkeypatch.setattr("scraper.ai.client._get_client", lambda: fake_client)

    out = call_claude(
        model="claude-haiku-4-5-20251001",
        system=CachedPrompt(static="rules", dynamic=""),
        user="payload",
    )
    assert out == '{"ok": true}'
    fake_client.messages.create.assert_called_once()
