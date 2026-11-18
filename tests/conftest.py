import pytest

from data.generate_sample import generate

HEADER = "order_id,date,category,quantity,amount,is_purchase"


@pytest.fixture(autouse=True)
def no_real_keys(monkeypatch):
    """Garantiza que ningún test use claves reales ni llame a las APIs."""
    for key in ("GEMINI_API_KEY", "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "GEMINI_MODEL"):
        monkeypatch.setenv(key, "")


@pytest.fixture
def sample_csv(tmp_path):
    return generate(tmp_path / "sample.csv")


def write_csv(path, rows, header=HEADER):
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def make_rows(n, amount="10.0", is_purchase="1", quantity="1", prefix="O"):
    return [f"{prefix}{i},2026-01-{(i % 28) + 1:02d},A,{quantity},{amount},{is_purchase}" for i in range(n)]
