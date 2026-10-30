"""Genera data/sample_sales.csv con datos sintéticos (sin datos personales)."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

OUTPUT = Path(__file__).parent / "sample_sales.csv"
CATEGORIES = ["Electrónica", "Hogar", "Ropa", "Deportes", "Libros"]
N_ROWS = 200
SEED = 42


def generate(path: Path = OUTPUT, n_rows: int = N_ROWS, seed: int = SEED) -> Path:
    rng = random.Random(seed)
    start = date(2026, 1, 1)
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "date", "category", "amount", "is_purchase"])
        for i in range(1, n_rows + 1):
            writer.writerow([
                f"ORD-{i:04d}",
                (start + timedelta(days=rng.randint(0, 89))).isoformat(),
                rng.choice(CATEGORIES),
                round(rng.uniform(5, 500), 2),
                1 if rng.random() < 0.6 else 0,
            ])
    return Path(path)


if __name__ == "__main__":
    print(f"Generado: {generate()} ({N_ROWS} filas)")
