from app.core.config import Settings


def test_claude_api_key_alias(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("CLAUDE_API_KEY", "test-claude-key")

    configured = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        jwt_secret_key="test-secret",
    )

    assert configured.anthropic_api_key == "test-claude-key"
