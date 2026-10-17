"""Tests for analytical risks: false zeros, fan-out, dates and callback semantics."""
import numpy as np
import pandas as pd
from pipeline import integrate,parse_delay,clean
from charts import figures

def fixture():
    h=pd.DataFrame([['BRONX','2022-01-01','A',2],['BRONX','2022-01-01','B',3],['QUEENS','2022-01-01','A',4]],columns=['borough','month','category','permits'])
    t=pd.DataFrame([['BRONX','2022-01-01','TRAFFIC',7,70,7,14,7]],columns=['borough','month','category','incidents','delay_sum','delay_n','student_sum','student_n'])
    for d in [h,t]:d['month']=pd.to_datetime(d.month)
    return h,t

def test_no_fanout_unknown_and_category_zero():
    h,t=fixture();p=integrate(h,t)
    assert len(p)==2 and p.loc[p.borough=='BRONX','permits'].iloc[0]==5
    assert pd.isna(p.loc[p.borough=='QUEENS','incidents'].iloc[0])
    p=integrate(h,t,'NOT PRESENT','TRAFFIC')
    assert (p.permits==0).all()
    assert p.loc[p.borough=='BRONX','mean_delay'].iloc[0]==10

def test_delay_parser():
    assert parse_delay('31-45 Min')==38
    assert parse_delay('1 hour')==60
    for x in ['unknown','30+','-2','500','45-31 min']:assert np.isnan(parse_delay(x))

def test_eight_charts_sparse_and_empty():
    h,t=fixture();p=integrate(h,t)
    for d in [p,p.iloc[:0]]:
        fs=figures(d);assert len(fs)==8
        for f in fs:assert f.to_json()

def test_bus_latest_id_and_domain_rules():
    raw=pd.DataFrame(dict(busbreakdown_id=['1','1','2','3'],occurred_on=['2022-01-05']*4,created_on=['2022-01-05']*4,last_updated_on=['2022-01-05','2022-01-06','2022-01-05','2022-01-05'],boro=['Bronx','Bronx','Nassau','Queens'],reason=['Other']*4,how_long_delayed=['10','30','20','bad'],number_of_students_on_the_bus=['2','3','4','999']))
    d,a=clean(raw,'transport')
    assert len(d)==2 and d.loc[d.busbreakdown_id=='1','delay_minutes'].iloc[0]==30
    assert d.loc[d.busbreakdown_id=='3','students'].isna().all()

def test_housing_preserves_distinct_work_and_issuance():
    rows=[]
    for date,work in [('2022-01-05','PLUMBING'),('2022-01-05','FOUNDATION'),('2022-02-05','PLUMBING')]:
        rows.append(dict(job_filing_number='B123-I1',work_permit='B123-I1-GC',sequence_number='1',borough='Brooklyn',issued_date=date,work_type=work,zip_code='11201-1234',estimated_job_costs='100',latitude='40.7',longitude='-73.9'))
    raw=pd.DataFrame(rows+[rows[0]])
    d,a=clean(raw,'housing')
    assert len(d)==3 and a['exact_duplicates_removed']==1
    assert d.zip_code.eq('11201').all()
