# Snapshot findings

ALL categories, all five boroughs, 2022–2024. Descriptive only; no causal/significance claims. Recompute with `python report_results.py`.

**Q1.** Pooled Spearman correlation: 0.254, across 180 borough-months. Borough size may explain co-movement.

**Q2.** Final-month indices (January 2022=100): BRONX: permits 163.4, incidents 101.0; BROOKLYN: permits 141.7, incidents 152.4; MANHATTAN: permits 109.7, incidents 68.2; QUEENS: permits 139.4, incidents 125.4; STATEN ISLAND: permits 171.8, incidents 88.8. Baseline-dependent endpoint comparison.

**Q3.** Largest seasonal incident-minus-permit index gap: STATEN ISLAND, month 10, 149.4 points. School schedules are a plausible explanation.

**Q4.** Spearman correlation of annual percentage changes: 0.068 (120 pairs). Reporting changes remain a limitation.

**Q5.** One-month-lag Spearman: BRONX: -0.156 (n=35); BROOKLYN: -0.245 (n=35); MANHATTAN: -0.318 (n=35); QUEENS: -0.330 (n=35); STATEN ISLAND: -0.118 (n=35). Chart includes 0–3 months; none is a causal effect or forecast.

**Q6.** Median of monthly mean delays (high/low permit months, minutes): BRONX: 28.1/28.5; BROOKLYN: 42.7/37.6; MANHATTAN: 41.7/39.8; QUEENS: 50.9/45.7; STATEN ISLAND: 38.6/37.0. These are monthly vendor-estimate summaries, not measured student journeys.

**Q7.** Largest share gap: BRONX, 15.2 percentage points (24.8% incidents, 9.6% permits). Not an exposure-adjusted failure rate.

**Q8.** Pearson correlation of residual counts after borough/calendar-month effects: 0.035, residual df=140. This is a different statistic from pooled Spearman, not proof of causation.

**NYC impact:** nominate boroughs/periods for joint DOB–DOE review, followed by route-level investigation before decisions. Permit-work records include renewals/non-residential work. Incidents exclude on-time journeys. Missing/out-of-city records, calendar seasonality and reporting changes limit generalization.