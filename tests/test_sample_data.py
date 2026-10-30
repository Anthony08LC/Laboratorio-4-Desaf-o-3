import csv

from data.generate_sample import generate

REQUIRED = ["order_id", "date", "category", "amount", "is_purchase"]


def test_sample_csv_has_required_columns_and_rows(tmp_path):
    path = generate(tmp_path / "sample.csv")
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0].keys()) == REQUIRED
    assert len(rows) >= 100
    assert {r["is_purchase"] for r in rows} <= {"0", "1"}


def test_sample_is_reproducible(tmp_path):
    a = generate(tmp_path / "a.csv").read_text(encoding="utf-8")
    b = generate(tmp_path / "b.csv").read_text(encoding="utf-8")
    assert a == b
