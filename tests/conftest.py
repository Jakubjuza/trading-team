import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def _isolate_runtime_files(tmp_path, monkeypatch):
    """Testy nesmí zapisovat do skutečného deníku signálů ani papírových obchodů."""
    import scanner.broker
    import scanner.scan
    monkeypatch.setattr(scanner.scan, "SIGNALS", tmp_path / "signals.jsonl")
    monkeypatch.setattr(scanner.scan, "FACTSHEETS", tmp_path / "factsheets")
    monkeypatch.setattr(scanner.scan, "OUTCOMES", tmp_path / "outcomes.jsonl")
    import scanner.demo
    import scanner.pyramid
    monkeypatch.setattr(scanner.demo, "LOG", tmp_path / "demo_trades.jsonl")
    monkeypatch.setattr(scanner.pyramid, "OUTCOMES", tmp_path / "pyramid_outcomes.jsonl")
    monkeypatch.setattr(scanner.scan, "_DEMO", {"broker": None, "error": None})
    monkeypatch.setattr(scanner.broker, "PAPER_LOG", tmp_path / "paper_trades.json")
