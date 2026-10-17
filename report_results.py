"""Recompute source counts and eight descriptive summaries."""
import json
import numpy as np
import pandas as pd
from pipeline import ROOT
p=pd.read_csv(ROOT/'data/processed/integrated.csv',parse_dates=['month'])
m=json.loads((ROOT/'data/processed/provenance.json').read_text());r=ROOT/'reports'
lines=['# Verified dataset overview','','| Dataset | All rows | Source columns | Extract rows | Extract columns | Clean rows |','|---|---:|---:|---:|---:|---:|']
for name,v in m['sources'].items():lines.append(f"| {v['name']} (`{v['dataset_id']}`) | {v['full_source_rows']:,} | {v['source_columns']} | {v['extracted_rows']:,} | {v['extracted_columns']} | {m['cleaning'][name]['output_rows']:,} |")
for name,v in m['sources'].items():lines.extend(['',f"{name}: {v['retrieved_utc']}; raw gzip SHA-256 `{v['sha256']}`."])
lines+=['',f'Panel: {len(p)} rows, {len(p.columns)} columns. Coverage: {p.coverage.value_counts().to_dict()}. Counts are snapshot-specific.']
(r/'DATASET_OVERVIEW.md').write_text('\n'.join(lines))
d=p[p.coverage=='both'].sort_values(['borough','month']).copy();lines=['# Snapshot findings','ALL categories, all five boroughs, 2022–2024. Descriptive only; no causal/significance claims. Recompute with `python report_results.py`.']
lines += [f'**Q1.** Pooled Spearman correlation: {d.permits.rank().corr(d.incidents.rank()):.3f}, across {len(d)} borough-months. Borough size may explain co-movement.']
parts=[]
for b,g in d.groupby('borough'):
 a,z=g.iloc[0],g.iloc[-1];parts.append(f'{b}: permits {100*z.permits/a.permits:.1f}, incidents {100*z.incidents/a.incidents:.1f}')
lines+=['**Q2.** Final-month indices (January 2022=100): '+ '; '.join(parts)+'. Baseline-dependent endpoint comparison.']
z=d.assign(m=d.month.dt.month).groupby(['borough','m'])[['permits','incidents']].mean().reset_index()
for c in ['permits','incidents']:z[c]=100*z[c]/z.groupby('borough')[c].transform('mean')
z['gap']=z.incidents-z.permits;a=z.loc[z.gap.idxmax()]
lines += [f'**Q3.** Largest seasonal incident-minus-permit index gap: {a.borough}, month {int(a.m)}, {a.gap:.1f} points. School schedules are a plausible explanation.']
o=d[['borough','month','permits','incidents']].copy();o.month+=pd.DateOffset(years=1);y=d.merge(o,on=['borough','month'],suffixes=('','_prior'))
for c in ['permits','incidents']:y[c+'_yoy']=100*(y[c]/y[c+'_prior'].replace(0,np.nan)-1)
lines += [f'**Q4.** Spearman correlation of annual percentage changes: {y.permits_yoy.rank().corr(y.incidents_yoy.rank()):.3f} ({len(y)} pairs). Reporting changes remain a limitation.']
parts=[]
for b,g in d.groupby('borough'):
 x=g[['month','permits']].copy();x.month+=pd.DateOffset(months=1);a=x.merge(g[['month','incidents']],on='month');parts.append(f'{b}: {a.permits.rank().corr(a.incidents.rank()):.3f} (n={len(a)})')
lines += ['**Q5.** One-month-lag Spearman: '+ '; '.join(parts)+'. Chart includes 0–3 months; none is a causal effect or forecast.']
z=d[d.delay_n>=10].copy();z['activity']=np.where(z.permits>z.groupby('borough').permits.transform('median'),'high','low');parts=[]
for b,g in z.groupby('borough'):
 a=g.groupby('activity').mean_delay.median();parts.append(f'{b}: {a.get("high",np.nan):.1f}/{a.get("low",np.nan):.1f}')
lines += ['**Q6.** Median of monthly mean delays (high/low permit months, minutes): '+ '; '.join(parts)+'. These are monthly vendor-estimate summaries, not measured student journeys.']
z=d.groupby('borough')[['permits','incidents']].sum();z=100*z/z.sum();z['gap']=z.incidents-z.permits;a=z.loc[z.gap.idxmax()]
lines += [f'**Q7.** Largest share gap: {z.gap.idxmax()}, {a.gap:.1f} percentage points ({a.incidents:.1f}% incidents, {a.permits:.1f}% permits). Not an exposure-adjusted failure rate.']
x=pd.get_dummies(d[['borough','month']].astype(str),drop_first=True,dtype=float);x=np.column_stack([np.ones(len(d)),x]);res=[]
for c in ['permits','incidents']:
 v=d[c].to_numpy(float);res.append(v-x@np.linalg.lstsq(x,v,rcond=None)[0])
lines += [f'**Q8.** Pearson correlation of residual counts after borough/calendar-month effects: {np.corrcoef(res)[0,1]:.3f}, residual df={len(d)-np.linalg.matrix_rank(x)}. This is a different statistic from pooled Spearman, not proof of causation.','**NYC impact:** nominate boroughs/periods for joint DOB–DOE review, followed by route-level investigation before decisions. Permit-work records include renewals/non-residential work. Incidents exclude on-time journeys. Missing/out-of-city records, calendar seasonality and reporting changes limit generalization.']
(r/'FINDINGS.md').write_text('\n\n'.join(lines));print('\n'.join(lines))
