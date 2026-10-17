"""Raw-data diagnostics; EDA figures are separate from eight research figures."""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pipeline import ROOT, SOURCES

def inspect(name,df):
    out=ROOT/'reports';out.mkdir(exist_ok=True)
    profile=pd.DataFrame({'dtype':df.dtypes.astype(str),'missing_n':df.isna().sum(),'missing_pct':100*df.isna().mean(),'unique_n':df.nunique()})
    profile.to_csv(out/f'{name}_profile.csv')
    df.describe(include='all').to_csv(out/f'{name}_summary.csv')
    print(name,df.shape,'exact duplicates:',df.duplicated().sum())
    print(profile.to_string())
    fig,axs=plt.subplots(1,2,figsize=(14,5))
    profile.missing_pct.sort_values().plot.barh(ax=axs[0],title=f'{name}: missing values (%)')
    category='work_type' if name=='housing' else 'reason'
    counts=df[category].fillna('UNKNOWN').value_counts().head(10)
    sns.barplot(x=counts.values,y=counts.index,ax=axs[1],color='#147d69');axs[1].set_title(f'{name}: top categories');axs[1].set_xlabel('Records')
    fig.tight_layout();fig.savefig(out/f'{name}_eda.png',dpi=140);plt.show()
    dates=pd.to_datetime(df[SOURCES[name]['date']],format='mixed',errors='coerce')
    print('Invalid dates:',dates.isna().sum(),'date range:',dates.min(),dates.max())
    return profile

def numeric_eda(h,t):
    fig,axs=plt.subplots(1,2,figsize=(12,4))
    sns.histplot(h.loc[h.cost>0,"cost"],ax=axs[0],log_scale=(True,False));axs[0].set_title('Valid positive job costs (log scale)')
    sns.histplot(t.delay_minutes.dropna(),ax=axs[1],bins=30);axs[1].set_title('Parsed delay estimates (minutes)')
    fig.tight_layout();fig.savefig(ROOT/'reports/clean_distributions.png',dpi=140);plt.show()
    print('Costs (not summed across permits):\n',h.cost.describe())
    print('Delay minutes:\n',t.delay_minutes.describe())
