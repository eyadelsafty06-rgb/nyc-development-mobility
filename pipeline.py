"""Reproducible NYC extraction, cleaning and aggregate integration."""
from pathlib import Path
import argparse, hashlib, json, os, re
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent
BOROUGHS = ['BRONX', 'BROOKLYN', 'MANHATTAN', 'QUEENS', 'STATEN ISLAND']
START, END = '2022-01-01', '2025-01-01'  # closed calendar years; end exclusive
SOURCES = {
 'housing': dict(id='rbx6-tga4', date='issued_date', columns=['job_filing_number','work_permit','sequence_number','borough','issued_date','approved_date','work_type','permit_status','zip_code','bin','estimated_job_costs','latitude','longitude','filing_reason']),
 'transport': dict(id='ez4e-fazm', date='occurred_on', columns=['busbreakdown_id','occurred_on','created_on','last_updated_on','boro','reason','run_type','how_long_delayed','number_of_students_on_the_bus','breakdown_or_running_late','school_year','route_number'])
}

def session():
    s = requests.Session()
    s.mount('https://', HTTPAdapter(max_retries=Retry(total=4, backoff_factor=1, status_forcelist=[429,500,502,503,504])))
    if os.getenv('SOCRATA_APP_TOKEN'): s.headers['X-App-Token'] = os.environ['SOCRATA_APP_TOKEN']
    return s

def extract(name, start=START, end=END):
    spec = SOURCES[name]; sid = spec['id']; s = session()
    def get(url, params=None):
        r = s.get(url, params=params, timeout=120); r.raise_for_status(); return r.json()
    api = f'https://data.cityofnewyork.us/resource/{sid}.json'
    meta = get(f'https://data.cityofnewyork.us/api/views/{sid}.json')
    fields = [c['fieldName'] for c in meta['columns'] if not c['fieldName'].startswith(':')]
    missing = set(spec['columns']) - set(fields)
    if len(fields) < 9 or missing: raise ValueError(f'Schema changed: {missing}; columns={len(fields)}')
    where = f"{spec['date']} >= '{start}T00:00:00' AND {spec['date']} < '{end}T00:00:00'"
    count = lambda clause: int(get(api, {'$select':'count(*) as n', **({'$where':clause} if clause else {})})[0]['n'])
    total, expected = count(None), count(where)
    pages=[]; offset=0
    while True:
        records = get(api, {'$select':','.join(spec['columns']), '$where':where, '$order':':id', '$limit':50000, '$offset':offset})
        if not records: break
        pages.append(pd.DataFrame(records)); offset += len(records)
        print(f'{name}: {offset:,}/{expected:,}', flush=True)
        if len(records)<50000: break
    if offset != expected or count(where) != expected:
        raise RuntimeError('Source count changed or extraction truncated. Retry extraction; no output accepted.')
    after=get(f'https://data.cityofnewyork.us/api/views/{sid}.json')
    if meta.get('rowsUpdatedAt') != after.get('rowsUpdatedAt'):
        raise RuntimeError('Source updated during pagination. Retry on a stable snapshot.')
    if not pages: raise ValueError('No rows in requested window')
    df=pd.concat(pages,ignore_index=True).reindex(columns=spec['columns'])
    raw=ROOT/'data/raw';raw.mkdir(parents=True,exist_ok=True)
    path=raw/f'{name}.csv.gz'; df.to_csv(path,index=False,compression='gzip')
    manifest=dict(name=meta['name'], dataset_id=sid, full_source_rows=total, source_columns=len(fields), extracted_rows=len(df), extracted_columns=len(df.columns), start=start,end_exclusive=end,retrieved_utc=datetime.now(timezone.utc).isoformat(), rows_updated_at=meta.get('rowsUpdatedAt'),where=where,fields=spec['columns'],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),api=api,download=f'https://data.cityofnewyork.us/api/views/{sid}/rows.csv?accessType=DOWNLOAD')
    (raw/f'{name}_manifest.json').write_text(json.dumps(manifest,indent=2))
    (raw/f'{name}_schema.json').write_text(json.dumps(meta,indent=2))
    return df,manifest

def clean(df, name, start=START, end=END):
    d=df.copy(); audit={'input_rows':len(d)}
    for c in d.select_dtypes(include=['object','string']).columns:
        d[c]=d[c].astype('string').str.strip().replace('',pd.NA)
    d=d.drop_duplicates();audit['exact_duplicates_removed']=len(df)-len(d)
    date=SOURCES[name]['date'];d['date']=pd.to_datetime(d[date],errors='coerce',format='mixed')
    b='borough' if name=='housing' else 'boro'
    aliases={'1':'MANHATTAN','2':'BRONX','3':'BROOKLYN','4':'QUEENS','5':'STATEN ISLAND','RICHMOND':'STATEN ISLAND','NEW YORK':'MANHATTAN','KINGS':'BROOKLYN','THE BRONX':'BRONX'}
    d['borough']=d[b].str.upper().replace(aliases)
    valid=d.borough.isin(BOROUGHS)&d.date.ge(start)&d.date.lt(end)
    audit['invalid_geography_or_date_removed']=int((~valid).sum());d=d.loc[valid].copy()
    if name=='transport':
        audit['missing_identifier_removed']=int(d.busbreakdown_id.isna().sum())
        d=d.dropna(subset=['busbreakdown_id'])
        d['update']=pd.to_datetime(d.last_updated_on,errors='coerce',format='mixed')
        n=len(d);d=d.sort_values(['update','created_on'],na_position='first',kind='stable').drop_duplicates('busbreakdown_id',keep='last')
        audit['duplicate_ids_removed']=n-len(d)
        d['category']=d.reason.fillna('UNKNOWN').str.upper()
        d['students']=pd.to_numeric(d.number_of_students_on_the_bus,errors='coerce')
        bad=(d.students<0)|(d.students>100)|(d.students%1!=0)
        audit['students_invalid_or_missing']=int((bad|d.students.isna()).sum());d.loc[bad,'students']=np.nan
        d['delay_minutes']=d.how_long_delayed.map(parse_delay)
        audit['delay_unusable']=int(d.delay_minutes.isna().sum())
    else:
        # Grain: permit-work-type issuance record; preserve multi-work permits and renewals.
        keys=['job_filing_number','work_permit','sequence_number']
        audit['missing_identifier_removed']=int(d[keys].isna().any(axis=1).sum())
        d=d.dropna(subset=keys)
        invalid_id=~d.job_filing_number.str.match(r'^[BMQSX][0-9]+-',na=False)
        audit['placeholder_identifiers_removed']=int(invalid_id.sum())
        d=d.loc[~invalid_id].copy()
        d['category']=d.work_type.fillna('UNKNOWN').str.upper()
        keys += ['date','category']
        duplicated=d.duplicated(keys,keep=False)
        # Conflicting natural keys cannot be safely reconciled without version timestamps.
        audit['conflicting_key_rows_quarantined']=int(duplicated.sum())
        d=d.loc[~duplicated].copy()
        d['category']=d.work_type.fillna('UNKNOWN').str.upper()
        d['zip_code']=d.zip_code.str.extract(r'^(\d{5})(?:-\d{4})?$')[0]
        d['cost']=pd.to_numeric(d.estimated_job_costs.str.replace(r'[$,]','',regex=True),errors='coerce')
        audit['negative_costs']=int((d.cost<0).sum());d.loc[d.cost<0,'cost']=np.nan
        q1,q3=d.cost.quantile([.25,.75]);d['cost_iqr_outlier']=(d.cost<q1-1.5*(q3-q1))|(d.cost>q3+1.5*(q3-q1))
        audit['cost_iqr_outliers_retained']=int(d.cost_iqr_outlier.sum())
        for c,lo,hi in [('latitude',40.45,40.95),('longitude',-74.3,-73.65)]:
            d[c]=pd.to_numeric(d[c],errors='coerce');d.loc[~d[c].between(lo,hi),c]=np.nan
    d['month']=d.date.dt.to_period('M').dt.to_timestamp()
    audit['output_rows']=len(d)
    return d,audit

def parse_delay(value):
    """Parse only explicit minutes, hours or bounded numeric ranges; no guessed text."""
    if pd.isna(value): return np.nan
    t=str(value).strip().lower()
    m=re.fullmatch(r'(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*(min(?:ute)?s?|hr?s?|hours?)?',t)
    if not m: return np.nan
    a=float(m[1]);b=float(m[2]) if m[2] else a
    if b<a:return np.nan
    v=(a+b)/2*(60 if m[3] and m[3].startswith(('h')) else 1)
    return v if 0<=v<=240 else np.nan

def aggregate(h,t):
    keys=['borough','month','category']
    ha=h.groupby(keys,dropna=False).size().rename('permits').reset_index()
    ta=t.groupby(keys,dropna=False).agg(incidents=('busbreakdown_id','size'),delay_sum=('delay_minutes','sum'),delay_n=('delay_minutes','count'),student_sum=('students','sum'),student_n=('students','count')).reset_index()
    return ha,ta

def integrate(ha,ta,hcategory='ALL',tcategory='ALL'):
    """Filter each domain BEFORE aggregation; category dimensions never cross-join."""
    keys=['borough','month']
    h=ha if hcategory=='ALL' else ha[ha.category==hcategory]
    t=ta if tcategory=='ALL' else ta[ta.category==tcategory]
    h=h.groupby(keys).permits.sum().reset_index()
    t=t.groupby(keys)[['incidents','delay_sum','delay_n','student_sum','student_n']].sum().reset_index()
    # Coverage uses unfiltered sources: missing domain-month remains unknown, never fabricated zero.
    coverage=ha[keys].drop_duplicates().merge(ta[keys].drop_duplicates(),on=keys,how='outer',indicator=True,validate='one_to_one')
    out=coverage.merge(h,on=keys,how='left',validate='one_to_one').merge(t,on=keys,how='left',validate='one_to_one')
    hseen=out._merge.isin(['left_only','both']);tseen=out._merge.isin(['right_only','both'])
    out.loc[hseen,'permits']=out.loc[hseen,'permits'].fillna(0)
    tc=['incidents','delay_sum','delay_n','student_sum','student_n']
    out.loc[tseen,tc]=out.loc[tseen,tc].fillna(0)
    out['mean_delay']=out.delay_sum/out.delay_n.replace(0,np.nan)
    out['mean_students']=out.student_sum/out.student_n.replace(0,np.nan)
    out['delay_coverage']=out.delay_n/out.incidents.replace(0,np.nan)
    out['year']=pd.to_datetime(out.month).dt.year
    return out.rename(columns={'_merge':'coverage'}).sort_values(keys).reset_index(drop=True)

def build(start=START,end=END,download=True):
    frames={};audits={};manifests={}
    for name in SOURCES:
        if download: raw,manifest=extract(name,start,end)
        else:
            raw=pd.read_csv(ROOT/f'data/raw/{name}.csv.gz',dtype='string')
            manifest=json.loads((ROOT/f'data/raw/{name}_manifest.json').read_text())
            if (manifest['start'],manifest['end_exclusive'])!=(start,end):raise ValueError('Cached window differs')
        frames[name],audits[name]=clean(raw,name,start,end);manifests[name]=manifest
    ha,ta=aggregate(frames['housing'],frames['transport']);panel=integrate(ha,ta)
    dest=ROOT/'data/processed';dest.mkdir(parents=True,exist_ok=True)
    for name,frame in [('housing_monthly',ha),('transport_monthly',ta),('integrated',panel)]:frame.to_csv(dest/f'{name}.csv',index=False)
    (dest/'provenance.json').write_text(json.dumps({'sources':manifests,'cleaning':audits},indent=2))
    print(json.dumps(audits,indent=2));return frames,ha,ta,panel

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cached',action='store_true');args=p.parse_args();build(download=not args.cached)
