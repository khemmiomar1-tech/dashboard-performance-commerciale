# Power BI — DAX Measures

Measures for the **Sales Performance & Profitability** dashboard, written
against the star schema produced by `src/prepare_dashboard_data.py`:

- Fact table: `FactSales` (`Quantity`, `UnitPrice`, `UnitCost`, `Revenue`, `Cost`, `Margin`, `OrderId`, `Product`, `Region`, `Channel`, `OrderDate`)
- Dimensions: `DimProduct`, `DimDate` (marked as the date table, related to `FactSales[OrderDate]`)

All measures live in a dedicated `_Measures` table.

---

## Core KPIs

```dax
-- Total revenue (chiffre d'affaires)
CA =
SUM ( FactSales[Revenue] )
```

```dax
-- Total margin
Marge =
SUM ( FactSales[Margin] )
```

```dax
-- Margin rate (%)
Taux de marge =
DIVIDE ( [Marge], [CA] )
```

```dax
-- Number of orders
Commandes =
DISTINCTCOUNT ( FactSales[OrderId] )
```

```dax
-- Average basket (panier moyen)
Panier moyen =
DIVIDE ( [CA], [Commandes] )
```

```dax
-- Units sold
Unites vendues =
SUM ( FactSales[Quantity] )
```

## Shares and rankings

```dax
-- Revenue share of the current selection (product, region, channel...)
Part du CA =
DIVIDE (
    [CA],
    CALCULATE ( [CA], ALLSELECTED ( FactSales ) )
)
```

```dax
-- Product rank by revenue (for the Top-N visual)
Rang produit =
RANKX ( ALL ( DimProduct[Product] ), [CA],, DESC, DENSE )
```

```dax
-- Revenue of the Top 5 products only
CA Top 5 produits =
CALCULATE (
    [CA],
    FILTER ( VALUES ( DimProduct[Product] ), [Rang produit] <= 5 )
)
```

```dax
-- ABC class of a product, from its cumulative revenue share (Pareto)
-- Uses the ranking to rebuild the running total of revenue shares.
Part cumulee CA =
VAR RangActuel = [Rang produit]
VAR TotalCA = CALCULATE ( [CA], ALL ( DimProduct ) )
VAR CA_Cumule =
    SUMX (
        FILTER ( ALL ( DimProduct[Product] ), [Rang produit] <= RangActuel ),
        [CA]
    )
RETURN
    DIVIDE ( CA_Cumule, TotalCA )

Classe ABC =
SWITCH (
    TRUE (),
    [Part cumulee CA] <= 0.80, "A",
    [Part cumulee CA] <= 0.95, "B",
    "C"
)
```

## Period comparisons

```dax
-- Revenue of the previous month
CA mois precedent =
CALCULATE ( [CA], DATEADD ( DimDate[Date], -1, MONTH ) )
```

```dax
-- Month-over-month growth (évolution mensuelle)
Evolution CA % =
DIVIDE ( [CA] - [CA mois precedent], [CA mois precedent] )
```

```dax
-- Revenue of the same month last year
CA annee precedente =
CALCULATE ( [CA], SAMEPERIODLASTYEAR ( DimDate[Date] ) )
```

```dax
-- Year-over-year growth
Evolution annuelle % =
DIVIDE ( [CA] - [CA annee precedente], [CA annee precedente] )
```

```dax
-- Year-to-date revenue
CA YTD =
TOTALYTD ( [CA], DimDate[Date] )
```

## Notes

- Format `Taux de marge`, `Part du CA`, `Evolution CA %` and
  `Evolution annuelle %` as percentages in the model view.
- Dynamic filters (region, channel, category) work through the star-schema
  relationships — no measure needs to be duplicated per drill-down level.
- The ABC/Pareto thresholds (80% / 95%) match the classification computed in
  `output/abc_pareto.csv` by the Python preparation script.
