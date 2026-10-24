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
    monkeypatch.setattr(scanner.broker, "PAPER_LOG", tmp_path / "paper_trades.json")
