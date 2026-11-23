"""
Prepare dashboard-ready tables from the raw sales extract.

Pipeline (mirrors the Power Query / SQL preparation of the Power BI project):
  1. Clean  - drop exact duplicates, invalid quantities/prices, missing keys.
  2. Model  - star schema: one fact table + product and date dimensions.
  3. Aggregate - KPI tables by product, region and month, plus an ABC/Pareto
     classification of the product portfolio.

Usage:
    python src/prepare_dashboard_data.py
Inputs:
    data/sample/sales.csv
Outputs (output/):
    fact_sales.csv        one row per order line, with revenue / cost / margin
    dim_product.csv       product dimension (category, price, cost)
    dim_date.csv          date dimension (year, month, quarter, month name)
    kpi_by_product.csv    revenue, margin, margin rate, orders, avg basket
    kpi_by_region.csv     same KPIs by region (and channel breakdown kept in fact)
    kpi_by_month.csv      monthly revenue / margin for period comparisons
    abc_pareto.csv        products ranked by revenue with cumulative share + ABC class
"""

from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "sample" / "sales.csv"
OUT = BASE / "output"


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates and rows that cannot be trusted for KPI reporting."""
    n0 = len(df)
    df = df.drop_duplicates().copy()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date", "region", "product"])
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0) & (df["unit_cost"] >= 0)]
    print(f"Cleaning: {n0:,} raw rows -> {len(df):,} valid rows "
          f"({n0 - len(df)} removed)")
    return df


def build_star_schema(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fact table with computed amounts + product and date dimensions."""
    fact = df.copy()
    fact["revenue"] = fact["quantity"] * fact["unit_price"]
    fact["cost"] = fact["quantity"] * fact["unit_cost"]
    fact["margin"] = fact["revenue"] - fact["cost"]

    dim_product = (
        df[["product", "category", "unit_price", "unit_cost"]]
        .drop_duplicates()
        .sort_values("product")
        .reset_index(drop=True)
    )
    dim_product.insert(0, "product_id", range(1, len(dim_product) + 1))

    dates = pd.DataFrame({"date": pd.date_range(df["order_date"].min(), df["order_date"].max())})
    dates["year"] = dates["date"].dt.year
    dates["month"] = dates["date"].dt.month
    dates["quarter"] = dates["date"].dt.quarter
    dates["month_name"] = dates["date"].dt.strftime("%B")
    dates["year_month"] = dates["date"].dt.strftime("%Y-%m")
    return fact, dim_product, dates


def kpi_table(fact: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Revenue / margin / orders / average basket for any drill-down level."""
    out = (
        fact.groupby(group_col)
        .agg(
            revenue=("revenue", "sum"),
            margin=("margin", "sum"),
            orders=("order_id", "nunique"),
            units=("quantity", "sum"),
        )
        .reset_index()
    )
    out["margin_rate_pct"] = (out["margin"] / out["revenue"] * 100).round(2)
    out["avg_basket"] = (out["revenue"] / out["orders"]).round(2)
    out["revenue"] = out["revenue"].round(2)
    out["margin"] = out["margin"].round(2)
    return out.sort_values("revenue", ascending=False).reset_index(drop=True)


def abc_pareto(fact: pd.DataFrame) -> pd.DataFrame:
    """Rank products by revenue; class A = up to 80% of revenue, B = next 15%, C = rest."""
    abc = kpi_table(fact, "product")[["product", "revenue", "margin"]]
    total = abc["revenue"].sum()
    abc["revenue_share_pct"] = (abc["revenue"] / total * 100).round(2)
    abc["cumulative_share_pct"] = abc["revenue_share_pct"].cumsum().round(2)
    abc["abc_class"] = pd.cut(
        abc["cumulative_share_pct"], bins=[0, 80, 95, 100.01],
        labels=["A", "B", "C"], include_lowest=True,
    )
    return abc


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(RAW)
    fact, dim_product, dim_date = build_star_schema(clean(raw))

    fact_out = fact[["order_id", "order_date", "product", "category", "region",
                     "channel", "quantity", "unit_price", "unit_cost",
                     "revenue", "cost", "margin"]]
    fact_out.to_csv(OUT / "fact_sales.csv", index=False)
    dim_product.to_csv(OUT / "dim_product.csv", index=False)
    dim_date.to_csv(OUT / "dim_date.csv", index=False)

    kpi_table(fact, "product").to_csv(OUT / "kpi_by_product.csv", index=False)
    kpi_table(fact, "region").to_csv(OUT / "kpi_by_region.csv", index=False)

    monthly = kpi_table(fact.assign(year_month=fact["order_date"].dt.strftime("%Y-%m")),
                        "year_month").sort_values("year_month")
    monthly.to_csv(OUT / "kpi_by_month.csv", index=False)

    abc = abc_pareto(fact)
    abc.to_csv(OUT / "abc_pareto.csv", index=False)

    total_rev = fact["revenue"].sum()
    total_margin = fact["margin"].sum()
    print(f"Revenue (CA)      : {total_rev:,.2f}")
    print(f"Margin            : {total_margin:,.2f} "
          f"({total_margin / total_rev * 100:.1f}%)")
    print(f"Orders            : {fact['order_id'].nunique():,}")
    print(f"Average basket    : {total_rev / fact['order_id'].nunique():,.2f}")
    a_share = abc.loc[abc["abc_class"] == "A", "revenue_share_pct"].sum()
    a_count = (abc["abc_class"] == "A").sum()
    print(f"ABC class A       : {a_count} of {len(abc)} products "
          f"= {a_share:.1f}% of revenue")
    print(f"Tables written to {OUT}/")


if __name__ == "__main__":
    main()
