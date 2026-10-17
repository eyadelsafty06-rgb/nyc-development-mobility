"""Eight research questions shared by notebook and dashboard."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

QUESTIONS=[
 ('Member 1','Do borough-months with more permit activity also report more school-bus incidents?','Scatter: counts, coloured by borough; exposes scale confounding.'),
 ('Member 1','Do permit and incident trends move together within each borough relative to its first selected month?','Indexed time series: baseline 100, one panel per borough.'),
 ('Member 2','Which seasons show unusually high incident reporting relative to development activity?','Heatmap: incident seasonal index minus permit seasonal index.'),
 ('Member 2','Are year-over-year changes in permits associated with changes in incident reports?','Scatter: same-month annual percentage changes, avoiding adjacent-season comparisons.'),
 ('Member 3','Is permit activity associated with incident reporting one to three months later?','Heatmap: within-borough Spearman correlations at calendar-aligned lags, including lag zero.'),
 ('Member 3','Are reported delays longer in high-permit months than low-permit months within a borough?','Box plot of monthly mean delay, split at each borough’s median permit count.'),
 ('Member 4','Which boroughs account for a larger share of reported incidents than of permit activity?','Grouped share bars: descriptive concentration, not an exposure-adjusted risk.'),
 ('Member 4','Does the relationship persist after removing borough and shared calendar-month effects?','Residual scatter: additive borough and date fixed effects for both count variables.')]

def blank(message):
    f=go.Figure();f.add_annotation(text=message,x=.5,y=.5,xref='paper',yref='paper',showarrow=False);return f

def figures(panel):
    d=panel[panel.coverage.astype(str)=='both'].copy().sort_values(['borough','month'])
    d['month']=pd.to_datetime(d.month)
    if d.empty:return [blank('No matched borough-months for these filters.') for _ in QUESTIONS]
    fs=[]
    fs.append(px.scatter(d,x='permits',y='incidents',color='borough',hover_data=['month']))
    z=d.copy()
    for c in ['permits','incidents']:
        first=z.groupby('borough')[c].transform('first').replace(0,np.nan)
        z[c]=100*z[c]/first
    z=z.melt(id_vars=['borough','month'],value_vars=['permits','incidents'],var_name='metric',value_name='index')
    fs.append(px.line(z,x='month',y='index',color='metric',facet_col='borough',facet_col_wrap=2,markers=True))
    z=d.assign(month_number=d.month.dt.month).groupby(['borough','month_number'])[['permits','incidents']].mean().reset_index()
    for c in ['permits','incidents']:z[c]=100*z[c]/z.groupby('borough')[c].transform('mean').replace(0,np.nan)
    z['gap']=z.incidents-z.permits
    fs.append(px.imshow(z.pivot(index='borough',columns='month_number',values='gap'),color_continuous_scale='RdBu_r',color_continuous_midpoint=0,labels={'color':'Index-point gap','x':'Month of year'}))
    old=d[['borough','month','permits','incidents']].copy();old['month']+=pd.DateOffset(years=1)
    y=d.merge(old,on=['borough','month'],suffixes=('','_prior'),validate='one_to_one')
    for c in ['permits','incidents']:y[c+'_yoy']=100*(y[c]/y[c+'_prior'].replace(0,np.nan)-1)
    y=y.dropna(subset=['permits_yoy','incidents_yoy'])
    fs.append(px.scatter(y,x='permits_yoy',y='incidents_yoy',color='borough',hover_data=['month']) if len(y) else blank('Select at least two overlapping calendar years; zero baselines are excluded.'))
    rows=[]
    for borough,g in d.groupby('borough'):
        for lag in range(4):
            x=g[['month','permits']].copy();x['month']+=pd.DateOffset(months=lag)
            a=x.merge(g[['month','incidents']],on='month')
            r=a.permits.rank().corr(a.incidents.rank()) if len(a)>=12 and a.permits.nunique()>1 and a.incidents.nunique()>1 else np.nan
            rows.append({'borough':borough,'lag':lag,'rho':r,'pairs':len(a)})
    z=pd.DataFrame(rows)
    f=px.imshow(z.pivot(index='borough',columns='lag',values='rho'),zmin=-1,zmax=1,color_continuous_scale='RdBu_r',labels={'x':'Months after permits','color':'Spearman rho'})
    fs.append(f)
    z=d[d.delay_n>=10].copy();z['activity']=np.where(z.permits>z.groupby('borough').permits.transform('median'),'High permits','Low/equal permits')
    fs.append(px.box(z,x='borough',y='mean_delay',color='activity',points='all',hover_data=['month','delay_n','delay_coverage']) if len(z) else blank('At least 10 usable delay estimates per borough-month are required.'))
    z=d.groupby('borough')[['permits','incidents']].sum()
    z=100*z/z.sum().replace(0,np.nan)
    fs.append(px.bar(z.reset_index().melt(id_vars='borough',var_name='metric',value_name='share_pct'),x='borough',y='share_pct',color='metric',barmode='group'))
    x=pd.get_dummies(d[['borough','month']].astype(str),drop_first=True,dtype=float)
    x=np.column_stack([np.ones(len(d)),x.to_numpy()])
    if len(d)-np.linalg.matrix_rank(x)>=5:
        z=d.copy()
        for c in ['permits','incidents']:
            v=z[c].to_numpy(float);z[c+'_residual']=v-x@np.linalg.lstsq(x,v,rcond=None)[0]
        fs.append(px.scatter(z,x='permits_residual',y='incidents_residual',color='borough',hover_data=['month']))
    else:fs.append(blank('Select more boroughs/months: fewer than 5 residual degrees of freedom.'))
    for i,f in enumerate(fs):
        f.update_layout(title=f'Q{i+1} · {QUESTIONS[i][0]}',template='plotly_white',margin=dict(l=50,r=30,t=60,b=50),height=480)
    return fs

def story(panel):
    d=panel[panel.coverage.astype(str)=='both']
    if d.empty:return 'No paired observations. Broaden the filters; missing coverage is not zero activity.'
    rho=d.permits.rank().corr(d.incidents.rank()) if d.permits.nunique()>1 and d.incidents.nunique()>1 else np.nan
    r=f'{rho:.2f}' if pd.notna(rho) else 'undefined (constant counts)'
    return (f'For the applied filters, {len(d)} matched borough-months contain {d.permits.sum():,.0f} permit records and '
            f'{d.incidents.sum():,.0f} reported school-bus incidents. The pooled Spearman correlation is {r}. '
            'This is a descriptive association, not evidence that construction causes delays. Borough size, school schedules, '
            'reporting practices and traffic exposure can explain co-movement. Permits include non-residential work and do not '
            'measure completed homes. Incident reports exclude on-time journeys; rates of failure cannot be calculated. '
            'Use these patterns to nominate boroughs and periods for joint DOB/DOE review and route-level follow-up, not to rank safety or assign blame.')
