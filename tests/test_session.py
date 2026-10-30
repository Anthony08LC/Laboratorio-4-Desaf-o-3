from src.session import SessionHistory, max_history_from_env


def test_keeps_last_five_newest_first():
    history = SessionHistory()
    for i in range(7):
        history.add(f"resumen {i}", simulated=True)
    assert len(history) == 5
    assert [e["text"] for e in history.items()] == [f"resumen {i}" for i in range(6, 1, -1)]


def test_max_history_from_env(monkeypatch):
    monkeypatch.setenv("MAX_HISTORY", "8")
    assert max_history_from_env() == 8
    monkeypatch.setenv("MAX_HISTORY", "abc")
    assert max_history_from_env() == 5
    monkeypatch.setenv("MAX_HISTORY", "0")
    assert max_history_from_env() == 1
