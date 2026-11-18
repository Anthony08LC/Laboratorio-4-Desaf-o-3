import csv

from data.generate_sample import COLUMNS, OUTPUT, generate
from src.kpis import REQUIRED_COLUMNS, validate_csv


def test_sample_csv_meets_lab_requirements(tmp_path):
    path = generate(tmp_path / "sample.csv")
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0].keys()) == COLUMNS == REQUIRED_COLUMNS
    assert len(rows) >= 100 and len(COLUMNS) >= 5
    assert {r["is_purchase"] for r in rows} <= {"0", "1"}
    assert all(int(r["quantity"]) >= 1 and float(r["amount"]) > 0 for r in rows)
    assert len({r["order_id"] for r in rows}) == len(rows)


def test_sample_is_reproducible_and_matches_repo_file(tmp_path):
    a = generate(tmp_path / "a.csv").read_text(encoding="utf-8")
    b = generate(tmp_path / "b.csv").read_text(encoding="utf-8")
    assert a == b == OUTPUT.read_text(encoding="utf-8")


def test_repo_sample_passes_validation():
    df = validate_csv(str(OUTPUT))
    assert df.attrs["quality"]["dropped_rows"] == 0
    assert df.select_dtypes("number").shape[1] >= 2
