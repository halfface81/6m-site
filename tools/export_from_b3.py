# 從 B3Scanner 匯出網站公開資料:權威 CSV 裁切 + 加權報酬指數月報酬。
# 每月出刊流程第一步。在 B3Scanner 目錄下執行:
#   .venv/bin/python ../6m-site/tools/export_from_b3.py
from pathlib import Path

import duckdb
import pandas as pd

B3 = Path(__file__).resolve().parents[2] / 'B3Scanner'
SITE = Path(__file__).resolve().parents[1]

df = pd.read_csv(B3 / 'docs' / 'momentum_official_monthly.csv', parse_dates=['date'])
con = duckdb.connect(str(B3 / 'data' / 'market.duckdb'), read_only=True)
tr = con.execute("SELECT date, close FROM index_daily WHERE name='TAIEX_TR' ORDER BY date").df()
tr['date'] = pd.to_datetime(tr['date'])
s = tr.set_index('date')['close']
trm = s.groupby(s.index.to_period('M')).last().pct_change()

df['ym'] = df['date'].dt.to_period('M')
df['taiex_tr'] = df['ym'].map(trm)
missing = df['taiex_tr'].isna().sum()
pub = df[['date', 'full', 'actual', 'bench', 'taiex_tr', 'vol_w']].copy()
for c in ['full', 'actual', 'bench', 'taiex_tr', 'vol_w']:
    pub[c] = pub[c].round(6)
pub.to_csv(SITE / 'data' / '6m_monthly.csv', index=False)
print(f'公開 CSV:{len(pub)} 列,缺指數 {missing} 列(2003 前),末列 {pub.iloc[-1]["date"]}')
print(pub.tail(2).to_string())
