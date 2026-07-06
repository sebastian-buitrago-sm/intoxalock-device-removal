import pytest
from core.greeting import greet
from elevenlabs_agent.cli import main


def test_greet_default() -> None:
    assert greet() == "Hello, world!"


def test_main_prints_greeting(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    main()
    captured = capsys.readouterr()
    assert "Hello, world!" in captured.out
