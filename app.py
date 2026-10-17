"""Run python app.py after python pipeline.py. No downloads occur in web requests."""
import json,re
import pandas as pd
from dash import Dash,Input,Output,State,dcc,html,no_update
from pipeline import ROOT,BOROUGHS,integrate
from charts import QUESTIONS,figures,story,blank

DATA=ROOT/'data/processed'
ready=all((DATA/f'{n}.csv').exists() for n in ['housing_monthly','transport_monthly'])
if ready:
    H=pd.read_csv(DATA/'housing_monthly.csv',parse_dates=['month'])
    T=pd.read_csv(DATA/'transport_monthly.csv',parse_dates=['month'])
else:
    H=pd.DataFrame(columns=['borough','month','category','permits'])
    T=pd.DataFrame(columns=['borough','month','category','incidents','delay_sum','delay_n','student_sum','student_n'])
years=sorted(set(H.month.dt.year)|set(T.month.dt.year)) if ready else [2022,2023,2024]
hcats=['ALL']+sorted(H.category.unique().tolist());tcats=['ALL']+sorted(T.category.unique().tolist())
app=Dash(__name__);server=app.server
app.title='Building NYC · Moving Students'

def dropdown(id,label,options,value,multi=False):
    return html.Div([html.Label(label,htmlFor=id),dcc.Dropdown(options,value,id=id,multi=multi,clearable=False)])

app.layout=html.Main([
 html.Header([html.P('GIU · DATA ENGINEERING & VISUALIZATION · WINTER 2026',className='eyebrow'),html.H1('Building NYC. Moving students.'),html.P('Explore development activity and school-bus disruption across five boroughs, 2022–2024.')]),
 html.Section([html.Label('Search borough, year and category; press Enter or Apply Search'),html.Div([dcc.Input(id='search',placeholder='Brooklyn 2022 heavy traffic',debounce=True),html.Button('Apply Search',id='apply')],className='search'),html.Div(id='search-status'),
 html.Div([dropdown('borough','Borough',BOROUGHS,BOROUGHS,True),dropdown('year','Calendar year',years,years,True),dropdown('housing','Permit work type',hcats,'ALL'),dropdown('transport','Incident reason',tcats,'ALL')],className='filters'),
 html.Button('Generate Report',id='generate',n_clicks=0,className='primary'),html.P('Filters are staged. Generate Report refreshes all eight charts and the story.')],className='card'),
 html.Section([html.H2('Story'),html.P('Question: Do changes in development activity coincide with school-bus disruption?'),html.Div(id='story'),html.P(id='coverage')],className='card'),
 dcc.Loading(html.Div([html.Article([html.H2(f'Q{i+1} · {q[0]}'),html.P(q[1]),html.Small(q[2]),dcc.Graph(id=f'chart-{i}',figure=blank('Click Generate Report'))],className='card') for i,q in enumerate(QUESTIONS)],className='charts')),
 html.Footer([html.A('DOB NOW source',href='https://data.cityofnewyork.us/d/rbx6-tga4'), ' · ',html.A('School-bus source',href='https://data.cityofnewyork.us/d/ez4e-fazm'),html.P('Borough-month association · no causal interpretation · reported incidents, not all journeys')])
])

@app.callback(Output('borough','value'),Output('year','value'),Output('housing','value'),Output('transport','value'),Output('search-status','children'),Input('apply','n_clicks'),Input('search','n_submit'),State('search','value'),prevent_initial_call=True)
def search(_click,_enter,query):
    q=(query or '').upper().strip()
    if not q:return no_update,no_update,no_update,no_update,'Type a borough, available year or exact category.'
    bs=[b for b in BOROUGHS if b in q];ys=[int(y) for y in re.findall(r'\b20\d{2}\b',q)]
    if any(y not in years for y in ys):return no_update,no_update,no_update,no_update,f'Available years: {years}. No filters changed.'
    hc=[c for c in hcats[1:] if c in q];tc=[c for c in tcats[1:] if c in q]
    if len(hc)>1 or len(tc)>1:return no_update,no_update,no_update,no_update,'Use one category from each domain.'
    remainder=q
    for term in bs+[str(y) for y in ys]+hc+tc:remainder=remainder.replace(term,' ')
    if remainder.strip():return no_update,no_update,no_update,no_update,f'Unrecognized text: {remainder.strip()}. Use the exact dropdown labels.'
    return bs or BOROUGHS,ys or years,hc[0] if hc else 'ALL',tc[0] if tc else 'ALL','Search applied to dropdowns. Click Generate Report.'

@app.callback([Output(f'chart-{i}','figure') for i in range(8)]+[Output('story','children'),Output('coverage','children')],Input('generate','n_clicks'),State('borough','value'),State('year','value'),State('housing','value'),State('transport','value'))
def report(n,boroughs,selected_years,hcat,tcat):
    if not ready:return [blank('Run python pipeline.py first.') for _ in range(8)]+['Data not prepared. Follow README setup.','No data loaded; no demonstration numbers are presented.']
    if not n:return [blank('Choose filters, then Generate Report.') for _ in range(8)]+['Ready to generate your first report.','']
    p=integrate(H,T,hcat,tcat);p=p[p.borough.isin(boroughs or [])&p.year.isin(selected_years or [])]
    return figures(p)+[story(p),f'Coverage: {len(p)} observed borough-months; {(p.coverage.astype(str)!="both").sum()} unmatched excluded from paired charts. Categories: {hcat} / {tcat}.']

if __name__=='__main__':app.run(debug=False,host='0.0.0.0',port=8050)
