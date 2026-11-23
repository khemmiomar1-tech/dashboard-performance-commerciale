# Sales Performance & Profitability Dashboard

A data-analysis project that turns raw sales transactions into a
decision-ready **Power BI dashboard**: revenue, margin and average basket,
with drill-down by product, region and channel, period-over-period
comparisons, and an **ABC / Pareto** analysis of the product portfolio.

> The dataset in `data/sample/` is **100% synthetic** (fictional products,
> regions and amounts, generated with a fixed seed) so the project can be
> shared publicly. The preparation logic is exactly the one used on the real
> data.

## Business goal

The sales management team needs one reliable view of commercial performance:

- How much revenue and margin do we make — overall, per product, per region,
  per channel?
- Is performance improving month over month?
- Which products actually carry the business (Pareto), and where should the
  commercial effort go?

## Data model — star schema

The preparation script models the cleaned sales data as a star schema:

```
                DimProduct
                    |
DimDate —— FactSales —— (region, channel as degenerate dimensions)
```

| Table | Content |
|---|---|
| `fact_sales.csv` | One row per order line: quantity, unit price/cost, and computed `revenue`, `cost`, `margin` |
| `dim_product.csv` | Product, category, catalogue price and cost |
| `dim_date.csv` | Date, year, quarter, month, month name, year-month |

In the original project the preparation was done with **SQL** and
**Power Query**; this repository reproduces the same preparation in
**Python (pandas)** so it runs anywhere, and the aggregated tables in
`output/` feed the Power BI report directly.

## KPIs

| KPI | Definition |
|---|---|
| Revenue (CA) | Σ quantity × unit price |
| Margin | Σ quantity × (unit price − unit cost) |
| Margin rate | Margin / Revenue |
| Orders | Distinct order IDs |
| Average basket | Revenue / Orders |

All DAX measures (including month-over-month and year-over-year evolution,
Top-5 products and a DAX version of the ABC classification) are in
[`powerbi/dax_measures.md`](powerbi/dax_measures.md).

## ABC / Pareto finding (sample data)

Running the pipeline on the sample data:

- **5,200** valid order lines after cleaning (55 dirty rows removed:
  duplicates, missing regions, invalid quantities/prices)
- Revenue **56,168,280**, margin **30.8%**
- **Class A = 2 of 12 products = 76.3% of revenue** — a textbook Pareto
  profile: a small part of the catalogue carries most of the business, which
  is where stock availability and commercial focus should be guaranteed
  first. Classes B (next 15%) and C (the long tail) follow from the
  cumulative revenue share in `output/abc_pareto.csv`.

## Repository layout

```
dashboard-performance-commerciale/
├── data/sample/sales.csv          synthetic raw sales extract
├── src/
│   ├── generate_sample_data.py    regenerates the sample dataset (seeded)
│   └── prepare_dashboard_data.py  clean → star schema → KPI & ABC tables
├── powerbi/dax_measures.md        all DAX measures of the dashboard
└── output/                        generated tables (fact, dims, KPIs, ABC)
```

## How to run

```bash
pip install -r requirements.txt
python src/generate_sample_data.py     # optional: rebuild the sample data
python src/prepare_dashboard_data.py   # writes all tables to output/
```

## Reproducing the Power BI dashboard

1. Run the preparation script to produce the tables in `output/`.
2. In Power BI Desktop, import `fact_sales.csv`, `dim_product.csv` and
   `dim_date.csv`; create relationships `FactSales[Product] → DimProduct[Product]`
   and `FactSales[OrderDate] → DimDate[Date]`, and mark `DimDate` as the
   date table.
3. Create a `_Measures` table and paste the measures from
   `powerbi/dax_measures.md`.
4. Build the pages: KPI cards (CA, Marge, Taux de marge, Panier moyen),
   monthly revenue trend with the MoM/YoY measures, bar charts by product /
   region / channel with slicers, and the ABC table from `abc_pareto.csv`.

## Tech stack

SQL · Power BI · DAX · Power Query · Excel · Python (pandas) for the
reproducible preparation pipeline.
