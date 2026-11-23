"""
Generate the synthetic sales dataset used by this project.

The data is 100% fictional: 12 products, 4 Moroccan regions, 3 sales
channels, one full year (2024) of order lines. A small amount of "dirty"
rows (exact duplicates, missing region, invalid quantity/price) is injected
on purpose so the cleaning step of the pipeline has something real to do.

Usage:
    python src/generate_sample_data.py
Output:
    data/sample/sales.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_ORDERS = 5200

# Product catalogue: (name, category, unit price, unit cost, popularity weight)
# Popularity is deliberately skewed so the ABC / Pareto analysis is meaningful.
PRODUCTS = [
    ("Aurora Laptop 14in",        "Electronics",  8990.0, 6400.0, 0.20),
    ("Vortex Smartphone X2",      "Electronics",  5490.0, 3900.0, 0.16),
    ("Pulse Wireless Headphones", "Electronics",   890.0,  480.0, 0.13),
    ("Nimbus Tablet 10in",        "Electronics",  3290.0, 2350.0, 0.10),
    ("Ergo Comfort Chair",        "Home & Living", 1890.0, 1150.0, 0.09),
    ("Breeze Air Purifier",       "Home & Living", 1450.0,  860.0, 0.08),
    ("Lumen LED Lamp",            "Home & Living",  340.0,  170.0, 0.07),
    ("Terra Dinner Set 24pc",     "Home & Living",  620.0,  350.0, 0.05),
    ("Urban Runner Sneakers",     "Fashion",       790.0,  430.0, 0.04),
    ("Atlas Leather Wallet",      "Fashion",       450.0,  210.0, 0.03),
    ("Solstice Sunglasses",       "Fashion",       520.0,  240.0, 0.03),
    ("Heritage Wool Scarf",       "Fashion",       280.0,  120.0, 0.02),
]

REGIONS = ["Casablanca-Settat", "Rabat-Sale-Kenitra", "Marrakech-Safi", "Tanger-Tetouan"]
REGION_WEIGHTS = [0.35, 0.25, 0.20, 0.20]

CHANNELS = ["Retail", "E-commerce", "Wholesale"]
CHANNEL_WEIGHTS = [0.45, 0.35, 0.20]


def main() -> None:
    rng = np.random.default_rng(SEED)

    names = [p[0] for p in PRODUCTS]
    weights = np.array([p[4] for p in PRODUCTS], dtype=float)
    weights /= weights.sum()
    catalogue = {p[0]: p for p in PRODUCTS}

    product_idx = rng.choice(len(PRODUCTS), size=N_ORDERS, p=weights)
    start = np.datetime64("2024-01-01")
    day_offsets = rng.integers(0, 366, size=N_ORDERS)

    rows = []
    for i, idx in enumerate(product_idx):
        name, category, price, cost, _ = catalogue[names[idx]]
        rows.append(
            {
                "order_id": f"ORD-{i + 1:05d}",
                "order_date": str(start + day_offsets[i]),
                "product": name,
                "category": category,
                "region": rng.choice(REGIONS, p=REGION_WEIGHTS),
                "channel": rng.choice(CHANNELS, p=CHANNEL_WEIGHTS),
                "quantity": int(rng.integers(1, 6)),
                "unit_price": price,
                "unit_cost": cost,
            }
        )

    df = pd.DataFrame(rows)

    # --- Inject a few dirty rows on purpose (cleaning demo) -----------------
    duplicates = df.sample(30, random_state=SEED)                # exact duplicates
    missing_region = df.sample(15, random_state=SEED + 1).copy()  # missing region
    missing_region["region"] = np.nan
    invalid = df.sample(10, random_state=SEED + 2).copy()         # invalid values
    invalid["quantity"] = 0
    invalid["unit_price"] = -5.0

    df = pd.concat([df, duplicates, missing_region, invalid], ignore_index=True)
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)  # shuffle

    out = Path(__file__).resolve().parents[1] / "data" / "sample" / "sales.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df):,} rows -> {out}")


if __name__ == "__main__":
    main()
