# Eight research questions

## Q1 — Member 1

Do borough-months with more permit activity also report more school-bus incidents?

Scatter: counts, coloured by borough; exposes scale confounding.

```python
research_figures = figures(selected)
research_figures[0].show()
```

## Q2 — Member 1

Do permit and incident trends move together within each borough relative to its first selected month?

Indexed time series: baseline 100, one panel per borough.

```python
research_figures = figures(selected)
research_figures[1].show()
```

## Q3 — Member 2

Which seasons show unusually high incident reporting relative to development activity?

Heatmap: incident seasonal index minus permit seasonal index.

```python
research_figures = figures(selected)
research_figures[2].show()
```

## Q4 — Member 2

Are year-over-year changes in permits associated with changes in incident reports?

Scatter: same-month annual percentage changes, avoiding adjacent-season comparisons.

```python
research_figures = figures(selected)
research_figures[3].show()
```

## Q5 — Member 3

Is permit activity associated with incident reporting one to three months later?

Heatmap: within-borough Spearman correlations at calendar-aligned lags, including lag zero.

```python
research_figures = figures(selected)
research_figures[4].show()
```

## Q6 — Member 3

Are reported delays longer in high-permit months than low-permit months within a borough?

Box plot of monthly mean delay, split at each borough’s median permit count.

```python
research_figures = figures(selected)
research_figures[5].show()
```

## Q7 — Member 4

Which boroughs account for a larger share of reported incidents than of permit activity?

Grouped share bars: descriptive concentration, not an exposure-adjusted risk.

```python
research_figures = figures(selected)
research_figures[6].show()
```

## Q8 — Member 4

Does the relationship persist after removing borough and shared calendar-month effects?

Residual scatter: additive borough and date fixed effects for both count variables.

```python
research_figures = figures(selected)
research_figures[7].show()
```

