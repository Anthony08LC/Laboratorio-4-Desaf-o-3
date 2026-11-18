"""Genera data/sample_sales.csv con datos sintéticos (sin datos personales)."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

OUTPUT = Path(__file__).parent / "sample_sales.csv"
COLUMNS = ["order_id", "date", "category", "quantity", "amount", "is_purchase"]
# Rango de precio unitario por categoría (datos ficticios).
PRICE_RANGES = {
    "Electrónica": (40, 250),
    "Hogar": (15, 90),
    "Ropa": (10, 60),
    "Deportes": (20, 120),
    "Libros": (8, 35),
}
N_ROWS = 200
SEED = 42


def generate(path: Path = OUTPUT, n_rows: int = N_ROWS, seed: int = SEED) -> Path:
    rng = random.Random(seed)
    start = date(2026, 1, 1)
    categories = list(PRICE_RANGES)
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        for i in range(1, n_rows + 1):
            category = rng.choice(categories)
            quantity = rng.randint(1, 5)
            unit_price = rng.uniform(*PRICE_RANGES[category])
            writer.writerow([
                f"ORD-{i:04d}",
                (start + timedelta(days=rng.randint(0, 89))).isoformat(),
                category,
                quantity,
                round(quantity * unit_price, 2),
                1 if rng.random() < 0.6 else 0,
            ])
    return Path(path)


if __name__ == "__main__":
    print(f"Generado: {generate()} ({N_ROWS} filas)")
