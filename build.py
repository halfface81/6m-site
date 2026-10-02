# 6M 動能月誌網站產製器。
# 唯一數字來源：data/6m_monthly.csv(由 B3Scanner 權威 CSV 裁切);
# 每期敘事內容在 content/YYYY-MM.json；體檢表自 B3Scanner 的原稿同步。
# 用法：python3 build.py  → 輸出至 site/
import csv
import json
import math
import re
import shutil
import statistics
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / 'site'
CHECKUP_SRC = ROOT.parent / 'B3Scanner' / 'docs' / 'momentum-checkup.html'
OFFICIAL_START = '2027-01'
TEST_MONTHS = ['2026-09', '2026-10', '2026-11', '2026-12']
STOP_LINE = -20.0
BRAKE_WIN = 12
SITE_URL = 'https://6m.jeromewang.cloud'

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Noto+Serif+TC:wght@600;700&family=Noto+Sans+TC:wght@400;500;700&'
         'family=IBM+Plex+Mono:wght@500&display=swap">')

THEME_JS = """<script>
(function(){
  var k='6m-theme';
  try{var t=localStorage.getItem(k); if(t) document.documentElement.setAttribute('data-theme',t);}catch(e){}
  window.toggleTheme=function(){
    var el=document.documentElement;
    var cur=el.getAttribute('data-theme')||
      (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
    var nxt=cur==='dark'?'light':'dark';
    el.setAttribute('data-theme',nxt);
    try{localStorage.setItem(k,nxt);}catch(e){}
    if(window.REMARK42) window.REMARK42.changeTheme(nxt);
  };
})();
</script>"""

FAVICON = ("%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' rx='5' fill='%23C2402F'/%3E"
           "%3Ctext x='16' y='22' font-size='14' font-family='monospace' fill='%23FBFAF6'"
           " text-anchor='middle' font-weight='bold'%3E6M%3C/text%3E%3C/svg%3E")
DATA_END = ''


# ---------- 資料 ----------

def load_rows():
    rows = []
    with open(ROOT / 'data' / '6m_monthly.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(dict(ym=r['date'][:7], date=r['date'],
                             full=float(r['full']), actual=float(r['actual']),
                             bench=float(r['bench']), vol_w=float(r['vol_w'])))
    return rows


def site_rows(rows):
    vis = [r for r in rows if r['ym'] >= TEST_MONTHS[0]]
    for r in vis:
        if r['ym'] < OFFICIAL_START:
            r['issue'] = '#T' + str(TEST_MONTHS.index(r['ym']) + 1)
            r['official'] = False
        else:
            n = (int(r['ym'][:4]) - 2027) * 12 + int(r['ym'][5:7])
            r['issue'] = f'#{n:03d}'
            r['official'] = True
    return vis


def load_content(ym):
    p = ROOT / 'content' / f'{ym}.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


def brake_series(rows):
    out = {}
    for i in range(len(rows)):
        if i + 1 >= BRAKE_WIN:
            w = rows[i + 1 - BRAKE_WIN:i + 1]
            out[rows[i]['ym']] = sum(r['full'] - r['bench'] for r in w) * 100
    return out


def next_weight(rows):
    w = [r['full'] for r in rows[-12:]]
    return min(1.0, 0.3 / (statistics.stdev(w) * math.sqrt(12)))


def pct(x, dp=1):
    return f'{x*100:+.{dp}f}%'


def cls(x):
    return 'pos' if x > 0 else ('neg' if x < 0 else '')


def shade(x):
    a = abs(x)
    lv = 1 if a < 0.02 else (2 if a < 0.06 else 3)
    return f'var(--{"up" if x > 0 else "dn"}-{lv})' if x != 0 else 'var(--hair)'


# ---------- 頁面外殼 ----------

def page(title, active, body, root='', bare=False, desc=''):
    links = [('index.html', '首頁', 'home'), ('journal/index.html', '月誌', 'journal'),
             ('factsheet.html', '體檢表', 'factsheet'), ('about.html', '關於', 'about')]
    nav = ''.join(
        f'<a href="{root}{h}" class="{"on" if k == active else ""}">{t}</a>'
        for h, t, k in links)
    inner = body if bare else f'<div class="wrap">{body}{footer(root)}</div>'
    meta_desc = f'<meta name="description" content="{desc}">' if desc else ''
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
{meta_desc}
<link rel="icon" href="data:image/svg+xml,{FAVICON}">
{FONTS}
<link rel="stylesheet" href="{root}assets/site.css">
<link rel="alternate" type="application/rss+xml" title="6M 動能月誌" href="{root}feed.xml">
{THEME_JS}
</head>
<body>
<nav class="nav"><div class="nav-in">
  <a class="brand" href="{root}index.html"><span class="seal">6M</span>動能月誌</a>
  <div class="nav-links">{nav}
  <button class="theme-btn" onclick="toggleTheme()">主題</button></div>
</div></nav>
{inner}
</body></html>"""


def footer(root=''):
    return f"""
<div class="foot">
  <span>個人研究紀錄，非投資建議。詳見<a href="{root}about.html">關於頁</a>。</span>
  <span class="mono">資料截至 {DATA_END}</span>
  <div class="links"><a href="{root}about.html#errata">勘誤</a>
  <a href="{root}feed.xml">RSS</a><a href="{root}6m_monthly.csv">CSV</a></div>
</div>"""


def eyebrow(no, t, aside=''):
    a = f'<span class="aside">{aside}</span>' if aside else ''
    return (f'<div class="eyebrow"><span class="no">{no}</span>'
            f'<span class="t">{"&nbsp;".join(t)}</span>{a}</div>')


# ---------- 首頁 ----------

def wall_html(vis):
    by_ym = {r['ym']: r for r in vis}
    done = len([r for r in vis if r['official']])
    latest = vis[-1]
    warm = ''
    for ym in TEST_MONTHS:
        r = by_ym.get(ym)
        if r:
            warm += (f'<a class="cell f" style="background:{shade(r["full"])};'
                     f'border-style:dashed" title="{ym} 暖身 全倉 {pct(r["full"])}"'
                     f' href="journal/{ym}.html"></a>')
        else:
            warm += '<div class="cell" style="border-style:dashed"></div>'
    head = '<div></div>' + ''.join(f'<div class="mlab">{m}</div>' for m in range(1, 13))
    grid = ''
    for y in range(2027, 2037):
        grid += f'<div class="ylab">{y}</div>'
        for m in range(1, 13):
            ym = f'{y}-{m:02d}'
            r = by_ym.get(ym)
            if r and r['official']:
                sel = ' sel' if ym == latest['ym'] else ''
                grid += (f'<a class="cell f{sel}" style="background:{shade(r["full"])}"'
                         f' title="{ym} 全倉 {pct(r["full"])}" href="journal/{ym}.html"></a>')
            else:
                grid += '<div class="cell"></div>'
    label = (f'第 {int(latest["issue"][1:])}／120 個月' if latest['official']
             else f'暖身 {latest["issue"]}，不計入')
    foot = (f'<div class="wall-foot"><b class="mono">{latest["ym"]}</b>'
            f'<span class="mono">{latest["issue"]}</span><span>{label}</span>'
            f'<span class="mono">全倉 <b class="{cls(latest["full"])}">{pct(latest["full"])}</b></span>'
            f'<span class="mono">等權池 <b class="{cls(latest["bench"])}">{pct(latest["bench"])}</b></span>'
            f'<a class="read" href="journal/{latest["ym"]}.html">閱讀月誌 /{latest["ym"]} →</a></div>')
    aside = f'<b style="font-size:1.3em;color:var(--ink)">{done}</b> / 120 個月'
    return f"""
{eyebrow('01', '十年牆', aside)}
<div class="wall">
<div class="warm"><div class="wl">暖身<br>不計入</div>{warm}
  <span class="note" style="border:0;background:none;padding:0;margin:0">2026-09 ~ 12 執行測試期</span></div>
<div class="wall-grid">{head}{grid}</div>
</div>
{foot}
<div class="legend-line">
  <span><span class="sw" style="background:var(--up-3)"></span>當月獲利</span>
  <span><span class="sw" style="background:var(--dn-3)"></span>當月虧損</span>
  <span><span class="sw" style="border:1px solid var(--hair)"></span>尚未到來</span>
  <span>色深＝幅度(2%／6%)</span>
</div>"""


def three_tiles(latest, nw):
    return f"""
{eyebrow('02', '本月三數字', latest['ym'])}
<div class="tiles">
  <div class="tile"><div class="l">全倉線 當月</div>
    <div class="n {cls(latest['full'])}">{pct(latest['full'])}</div>
    <div class="l">20 檔籃子滿倉的原始報酬</div></div>
  <div class="tile"><div class="l">等權含息池 當月</div>
    <div class="n {cls(latest['bench'])}">{pct(latest['bench'])}</div>
    <div class="l">無資訊等權基準，煞車的尺</div></div>
  <div class="tile"><div class="l">下月建議倉位</div>
    <div class="n">{nw*100:.0f}<small>%</small></div>
    <div class="l">依 30% 波動目標自動調節</div></div>
</div>"""


def cum_chart(vis, root=''):
    pre = [r for r in vis if not r['official']]
    post = [r for r in vis if r['official']]
    labels, strat, ew = [], [], []
    sv = ev = 1.0
    for r in pre:
        sv *= 1 + r['actual']; ev *= 1 + r['bench']
        labels.append(r['ym']); strat.append(sv); ew.append(ev)
    if pre:
        strat = [v / sv for v in strat]
        ew = [v / ev for v in ew]
    sv = ev = 1.0
    for r in post:
        sv *= 1 + r['actual']; ev *= 1 + r['bench']
        labels.append(r['ym']); strat.append(sv); ew.append(ev)
    data = dict(labels=labels, npre=len(pre),
                strat=[round(v, 4) for v in strat], ew=[round(v, 4) for v in ew])
    return f"""
{eyebrow('03', '累積曲線')}
<div class="legend">
  <span><span class="sw" style="background:var(--s-strat)"></span><b>本策略(實際線)</b></span>
  <span><span class="sw" style="background:var(--s-ew)"></span><b>等權含息基準</b></span>
  <span style="margin-left:auto">虛線＝測試期</span>
</div>
<div class="chart-wrap" id="cumWrap"></div>
<p class="caption">累積報酬以 2027-01-01 正式實盤起算日為 0%。測試期段以虛線呈現，不計入十年。
加權報酬指數軌將於正式期開始後加入。</p>
<script>window.__CUM = {json.dumps(data)};</script>
<script src="{root}assets/cum_chart.js"></script>"""


def brake_block(val, win, note=True):
    lo, hi = -40, 40
    def x(v):
        return max(0, min(100, (v - lo) / (hi - lo) * 100))
    color = 'var(--up)' if val > 0 else 'var(--dn)'
    html = f"""
<div class="brake-head"><span class="brake-label">12 個月滾動超額(對等權池)</span>
  <span class="brake-val" style="color:{color}">{val:+.1f}pp</span>
  <span class="brake-dist">距停止線 {val - STOP_LINE:.1f}pp</span></div>
<div class="brake-bar">
  <div class="brake-danger" style="width:{x(STOP_LINE)}%"></div>
  <div class="brake-stop" style="left:{x(STOP_LINE)}%"></div>
  <div class="brake-zero" style="left:{x(0)}%"></div>
  <div class="brake-now" style="left:{x(val)}%;background:{color}"></div>
</div>
<div class="brake-scale"><span>−40pp</span><span>−20pp 停止線</span><span>0</span><span>+40pp</span></div>"""
    if note:
        html += """
<div class="note">觸線＝停止投入、重新驗證，不加碼攤平。</div>
<p class="caption">這是唯一的停止條款。儀表永遠展示，不論讀數好壞。</p>"""
    return html


def recent_html(vis):
    rows = ''
    for r in reversed(vis[-6:]):
        dim = ' class="dim"' if not r['official'] else ''
        rows += (f'<tr{dim}><td class="mono">{r["issue"]}</td>'
                 f'<td><a href="journal/{r["ym"]}.html" class="mono">/{r["ym"]}</a></td>'
                 f'<td class="{cls(r["full"])}">{pct(r["full"])}</td>'
                 f'<td class="{cls(r["bench"])}">{pct(r["bench"])}</td>'
                 f'<td>{r["vol_w"]*100:.0f}%</td></tr>')
    return f"""
{eyebrow('05', '最近月誌', '<a href="journal/index.html">全部 →</a>')}
<div class="tbl"><table>
<tr><th>期數</th><th>月份</th><th>全倉</th><th>等權池</th><th>倉位</th></tr>
{rows}
</table></div>"""


# ---------- 月誌 ----------

def journal_page(r, vis, bs, rows_all):
    _n = [0]
    def no():
        _n[0] += 1
        return f'{_n[0]:02d}'
    c = load_content(r['ym']) or {}
    root = '../'
    seq = '正式實盤第 ' + str(int(r['issue'][1:])) + '／120 個月' if r['official'] \
        else '執行測試期，不計入十年'
    acct = c.get('account_ret')
    seg = [x for x in vis if x['official'] == r['official'] and x['ym'] <= r['ym']]
    cum_from = OFFICIAL_START if r['official'] else TEST_MONTHS[0]
    cum_model = math.prod(1 + x['actual'] for x in seg) - 1
    cum_full = math.prod(1 + x['full'] for x in seg) - 1
    cum_bench = math.prod(1 + x['bench'] for x in seg) - 1
    accts = [(load_content(x['ym']) or {}).get('account_ret') for x in seg]
    prev_issues = [x for x in vis if x['ym'] < r['ym']]
    issue_start = ((load_content(prev_issues[-1]['ym']) or {}).get('account_value', 1000000)
                   if prev_issues else 1000000)
    cum_acct = (math.prod(1 + a for a in accts) - 1) if all(a is not None for a in accts) else None

    # 01 本月持倉
    holds = ''
    if c.get('holdings'):
        hr = ''
        for h in c['holdings']:
            hr += (f'<tr><td class="zh">{h["name"]} <span class="mono" style="color:var(--muted)">'
                   f'{h["code"]}</span></td>'
                   f'<td>{h["entry"]:g}</td><td>{h["shares"]:,}</td><td>{h["cost"]:,}</td>'
                   f'<td>{h["exit"]:g}</td>'
                   f'<td class="{cls(h["ret"])}">{pct(h["ret"])}</td>'
                   f'<td>{h["weight"]*100:.1f}%</td>'
                   f'<td class="zh">{h["note"]}</td></tr>')
        holds = f"""
{eyebrow(no(), '本月持倉', '作者已持有・交易完成後揭露')}
<div class="tbl"><table>
<tr><th style="text-align:left">股票</th><th>進場價</th><th>股數</th><th>成本</th><th>結算價</th><th>當月損益</th><th>權重</th><th>月底處置</th></tr>
{hr}
</table></div>
<p class="caption">{c.get('holdings_note', '')}</p>"""

    # 02 成績單(單月+累積)
    def cell(v):
        return f'<td class="{cls(v)}">{pct(v, 2)}</td>' if v is not None else '<td>—</td>'
    score = f"""
{eyebrow(no(), '成績單', f'累積自 {cum_from}')}
<div class="tbl"><table>
<tr><th></th><th>當月</th><th>累積</th></tr>
<tr><td class="zh">實際帳戶 <span class="hint" title="作者真實資金的對帳結果，以總資產(含現金)為分母">ⓘ</span></td>{cell(acct)}{cell(cum_acct)}</tr>
<tr><td class="zh">帳戶總值 <span class="hint" title="本期期初 → 期末的實際金額；累積欄為對計畫期初之報酬">ⓘ</span></td>
<td class="mono">{issue_start:,} → {c.get('account_value', 0):,} 元
({pct(c.get('account_value', 0)/issue_start - 1, 2)})</td>
<td class="{cls(c.get('account_value', 1000000)/1000000 - 1)}">對計畫期初 1,000,000：{pct(c.get('account_value', 1000000)/1000000 - 1, 2)}</td></tr>
<tr><td class="zh">全倉線 <span class="hint" title="20 檔等權籃子滿倉的原始報酬，不含倉位調節；十年牆與煞車都用這條">ⓘ</span></td>{cell(r['full'])}{cell(cum_full)}</tr>
<tr><td class="zh">等權含息池 <span class="hint" title="同流動性條件的等權含息基準，煞車的對照尺">ⓘ</span></td>{cell(r['bench'])}{cell(cum_bench)}</tr>
</table></div>
<p class="caption">帳戶報酬以<b>總資產</b>為分母(含未投入現金)。本月依倉位規則投入
{r['vol_w']*100:.0f}%(30% 波動目標自動調節)；只看已投入資金，本月報酬為
{(c.get('invested_ret', 0))*100:+.2f}%，與全倉線的差距見下方拆解。十年牆與煞車皆以全倉線計。
下月建議倉位 {next_weight([x for x in rows_all if x['ym'] <= r['ym']])*100:.0f}%。</p>"""
    if c.get('diff_reason'):
        score += f'<div class="note">執行誤差主因：{c["diff_reason"]}</div>'

    # 03 意外與處理
    events = ''
    if c.get('episode'):
        events = f"""
{eyebrow(no(), '意外與處理')}
<p>{c['episode']}</p>"""

    # 下月換股與持倉(發佈時已成交)
    nxt = ''
    if c.get('next_holdings'):
        t2 = c.get('next_turnover', {})
        nr = ''
        for h in c['next_holdings']:
            nr += (f'<tr><td class="zh">{h["name"]} <span class="mono" style="color:var(--muted)">'
                   f'{h["code"]}</span></td>'
                   f'<td class="zh">{h["kind"]}</td>'
                   f'<td>{h["entry"]:g}</td><td>{h["shares"]:,}</td><td>{h["cost"]:,}</td>'
                   f'<td>{h["weight"]*100:.1f}%</td></tr>')
        nxt = f"""
{eyebrow(no(), '下月換股與持倉', '發佈時已全數成交')}
<div class="tiles">
  <div class="tile"><div class="l">賣出</div><div class="n">{t2.get('sell', 0)}<small> 檔</small></div></div>
  <div class="tile"><div class="l">買進</div><div class="n">{t2.get('buy', 0)}<small> 檔</small></div></div>
  <div class="tile"><div class="l">續抱</div><div class="n">{t2.get('keep', 0)}<small> 檔</small></div></div>
  <div class="tile"><div class="l">下月曝險</div>
    <div class="n">{next_weight([x for x in rows_all if x['ym'] <= r['ym']])*100:.0f}<small>%</small></div>
    <div class="l">依 30% 波動目標自動調節，其餘持現金</div></div>
</div>
<div class="tbl"><table>
<tr><th style="text-align:left">股票</th><th>進出</th><th>進場價</th><th>股數</th><th>成本</th><th>權重</th></tr>
{nr}
</table></div>
<p class="caption">{c.get('next_note', '')}</p>"""

    # 作者復盤
    review = ''
    if c.get('review'):
        paras = ''.join(f'<p>{p}</p>' for p in c['review'].split('\n') if p.strip())
        review = f"""
{eyebrow(no(), '作者復盤')}
{paras}
<p><span class="seal" style="font-size:.78rem;letter-spacing:.14em;color:var(--seal);
border:1.5px solid var(--seal);border-radius:4px;padding:.1rem .5rem;font-weight:700">簽收</span>
<span class="mono" style="font-size:.84rem;color:var(--muted)"> {c.get('published', '')}</span></p>"""

    bval = bs.get(r['ym'])
    brake = ''
    if bval is not None:
        brake = (eyebrow(no(), '煞車讀數', '<a href="../index.html">累積曲線見首頁 →</a>')
                 + brake_block(bval, '', note=False)
                 + '<p class="caption">觸線＝停止投入、重新驗證，不加碼攤平。</p>')
    mailbag = ''
    if c.get('mailbag'):
        mb = c['mailbag']
        mailbag = f"""
{eyebrow(no(), '讀者來信')}
<p><b style="color:var(--seal)">問</b> {mb['q']}<br>
<span class="caption">{mb.get('from', '讀者')}，已匿名</span></p>
<p><b style="color:var(--seal)">答</b> {mb['a']}</p>"""
    comments = f"""
{eyebrow(no(), '留言')}
<div class="note" style="border-left-color:var(--hair)">
一、歡迎就策略提出討論。<br>
二、勿討論個股買賣問題。
</div>
<div id="remark42"></div>
<script>
  var remark_config = {{host: "https://comments.jeromewang.cloud", site_id: "6m",
    components: ["embed"], locale: "zh", show_email_subscription: false,
    theme: (document.documentElement.getAttribute('data-theme') === 'dark' ||
      (!document.documentElement.getAttribute('data-theme') &&
       matchMedia('(prefers-color-scheme: dark)').matches)) ? 'dark' : 'light'}};
</script>
<script src="https://comments.jeromewang.cloud/web/embed.js" defer></script>
<p class="caption">來信交流：6m@jeromewang.cloud
(個股買賣問題不予回覆；內容若於月誌公開引用，一律匿名)。</p>"""
    head = f"""
<div class="kicker">月誌 {r['issue']}</div>
<h1>{int(r['ym'][:4])} 年 {int(r['ym'][5:7])} 月</h1>
<p class="sub">{seq}</p>
<p class="caption mono">發佈 {c.get('published', '—')} ・結算至 {c.get('data_through', r['date'])}(月底收盤選股、次一交易日開盤結算) ・永久網址 /{r['ym']}</p>"""
    body = head + holds + score + events + nxt + review + brake + mailbag + comments
    err = c.get('errata')
    body += f'<p class="caption">本期勘誤：{err if err else "尚無"}</p>'
    title = f'{r["issue"]} {r["ym"]}|6M 動能月誌'
    return page(title, 'journal', body, root=root, desc=c.get('summary', ''))


def archive_page(vis):
    body = """
<div class="kicker">月誌</div>
<h1>全部月誌</h1>"""
    official = [r for r in vis if r['official']]
    test = [r for r in vis if not r['official']]
    body += (f'<p class="sub">正式 {len(official)} 期，暖身 {len(test)} 期。'
             '每期網址永久，發佈後不修改。</p>')
    def rows_of(rs, dim=False):
        out = ''
        for r in reversed(rs):
            c = load_content(r['ym']) or {}
            out += (f'<tr{" class=dim" if dim else ""}><td class="mono">{r["issue"]}</td>'
                    f'<td><a class="mono" href="{r["ym"]}.html">/{r["ym"]}</a></td>'
                    f'<td class="{cls(r["full"])}">{pct(r["full"])}</td>'
                    f'<td class="{cls(r["bench"])}">{pct(r["bench"])}</td>'
                    f'<td>{r["vol_w"]*100:.0f}%</td>'
                    f'<td class="zh" style="text-align:left">{c.get("summary", "")}</td></tr>')
        return out
    hdr = ('<tr><th>期數</th><th>月份</th><th>全倉</th><th>等權池</th>'
           '<th>倉位</th><th style="text-align:left">摘要</th></tr>')
    years = sorted({r['ym'][:4] for r in official}, reverse=True)
    for y in years:
        body += f'<h3 class="mono" style="color:var(--seal)">{y}</h3>'
        body += f'<div class="tbl"><table>{hdr}{rows_of([r for r in official if r["ym"][:4] == y])}</table></div>'
    if test:
        body += ('<p class="caption mono" style="margin-top:2rem">2026-09 ~ 12 暖身，不計入</p>'
                 f'<div class="tbl"><table>{hdr}{rows_of(test, dim=True)}</table></div>')
    return page('全部月誌|6M 動能月誌', 'journal', body, root='../')


# ---------- 關於 ----------

def about_page(vis):
    errata_rows = ''
    n_err = 0
    for r in vis:
        c = load_content(r['ym']) or {}
        if c.get('errata'):
            for e in c['errata']:
                n_err += 1
                errata_rows += (f'<tr><td class="mono">{e["date"]}</td>'
                                f'<td class="mono">/{r["ym"]}</td>'
                                f'<td class="zh" style="text-align:left">{e["wrong"]}</td>'
                                f'<td class="zh" style="text-align:left">{e["fix"]}</td></tr>')
    errata_tbl = (f'<div class="tbl"><table><tr><th>日期</th><th>頁面</th>'
                  f'<th style="text-align:left">錯誤內容</th>'
                  f'<th style="text-align:left">更正內容</th></tr>{errata_rows}</table></div>'
                  if errata_rows else '<p class="caption">尚無勘誤。有錯會記在這裡，永久累積。</p>')
    body = f"""
<div class="kicker">關於</div>
<h1>這是一份實驗紀錄，不是投資建議。</h1>

{eyebrow('01', '作者定調')}
<p>這個網站是我個人研究紀錄的公開摘要。</p>
<p>6M 動能策略是一場十年計畫型實驗：2027-01-01 起算，2036-12 結束，每月結算一次，
結果釘在首頁的十年牆上。2026-09 ~ 12 為執行測試期，照常對帳，不計入十年。</p>
<p>策略參數不揭露。公開的是結果、口徑和錯誤。數字唯一來源是權威程式與官方 CSV;
發佈後不靜默修改，錯誤一律公開勘誤。</p>

{eyebrow('02', '免責聲明')}
<div class="note">本網站內容為個人投資紀錄與研究，不構成投資建議，
不構成任何證券之要約、要約之引誘或推介；作者持有文中提及之標的；
過往績效不代表未來表現。</div>

{eyebrow('03', '持倉利益揭露')}
<p>我以自有資金依本策略實際下單，持有月誌中提及的標的。</p>
<p>名單一律於交易完成後揭露，並標注「作者已持有」。實際持倉比例依每期
「下月建議倉位」執行，實際帳戶與模型線的差異見各期對帳表。</p>

{eyebrow('04', '不提供個別諮詢')}
<p>本站不提供個別諮詢，不回覆個股問題，不收費，不招攬。</p>
<p>來信交流：<span class="mono">6m@jeromewang.cloud</span>。
個股買賣問題不予回覆；值得公開討論的來信，徵得同意或匿名後於月誌引用。</p>

<span id="errata"></span>
{eyebrow('05', '勘誤總表', f'共 {n_err} 筆，永久累積')}
{errata_tbl}

{eyebrow('06', '資料下載')}
<p>官方 CSV 是全站數字的原始數列，每月隨月誌更新。</p>
<div class="tbl"><table>
<tr><th>欄位</th><th style="text-align:left">內容</th></tr>
<tr><td class="mono">date</td><td class="zh" style="text-align:left">月底日期</td></tr>
<tr><td class="mono">full</td><td class="zh" style="text-align:left">全倉線當月報酬</td></tr>
<tr><td class="mono">actual</td><td class="zh" style="text-align:left">實際線當月報酬</td></tr>
<tr><td class="mono">bench</td><td class="zh" style="text-align:left">等權含息池當月報酬</td></tr>
<tr><td class="mono">vol_w</td><td class="zh" style="text-align:left">當月倉位係數</td></tr>
</table></div>
<p><a class="mono" href="6m_monthly.csv">6m_monthly.csv ↓</a>
<span class="caption mono"> 更新至 {DATA_END}</span></p>
<div class="note">頁面數字與 CSV 不符時，以 CSV 重算為準，並列入勘誤。</div>"""
    return page('關於|6M 動能月誌', 'about', body)


# ---------- 體檢表 ----------

def factsheet_page():
    src = CHECKUP_SRC if CHECKUP_SRC.exists() else ROOT / 'data' / 'momentum-checkup.html'
    html = src.read_text(encoding='utf-8')
    # 快取一份進 repo，部署機可離線重建
    (ROOT / 'data' / 'momentum-checkup.html').write_text(html, encoding='utf-8')
    m = re.search(r'(<style>.*?</style>)', html, re.S)
    style = m.group(1)
    body_m = re.search(r'(<div class="wrap">.*)', html, re.S)
    content = body_m.group(1)
    # 原稿的 .wrap 窄欄與自有樣式照用；外殼只供導覽與頁尾
    body = style + content + f'<div class="wrap" style="padding-top:0">{footer()}</div>'
    return page('6M動能體檢表', 'factsheet', body, bare=True)


# ---------- RSS ----------

def rss(vis):
    items = ''
    for r in reversed(vis):
        c = load_content(r['ym']) or {}
        pub = c.get('published', r['date'])
        items += f"""
<item>
  <title>{r['issue']} {r['ym']} 全倉 {pct(r['full'])}</title>
  <link>{SITE_URL}/journal/{r['ym']}.html</link>
  <guid>{SITE_URL}/journal/{r['ym']}.html</guid>
  <description>{c.get('summary', '')}。全倉 {pct(r['full'])}，等權池 {pct(r['bench'])}。</description>
  <pubDate>{pub}</pubDate>
</item>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>6M 動能月誌</title>
<link>{SITE_URL}</link>
<description>一場十年實驗的公開實驗室筆記</description>{items}
</channel></rss>"""


# ---------- 主流程 ----------

def build():
    global DATA_END
    rows = load_rows()
    vis = site_rows(rows)
    _lc = load_content(vis[-1]['ym']) or {}
    DATA_END = _lc.get('data_through', rows[-1]['date'])
    bs = brake_series(rows)
    latest = vis[-1]
    nw = next_weight(rows)

    OUT.mkdir(exist_ok=True)
    (OUT / 'journal').mkdir(exist_ok=True)
    shutil.copytree(ROOT / 'assets', OUT / 'assets', dirs_exist_ok=True)
    shutil.copy(ROOT / 'data' / '6m_monthly.csv', OUT / '6m_monthly.csv')

    hero = """
<div class="kicker">6M 動能策略 十年實盤公開紀錄</div>
<h1>一場十年實驗的公開實驗室筆記。</h1>
<p class="sub">2027-01-01 起算，十年，120 個月。每結算一個月，就在牆上釘一格，好壞都留著。</p>"""
    body = (hero + wall_html(vis) + three_tiles(latest, nw) + cum_chart(vis)
            + eyebrow('04', '煞車儀表',
                      f'{vis[max(0, len(vis)-BRAKE_WIN)]["ym"]} ~ {latest["ym"]}')
            + brake_block(bs[latest['ym']], '') + recent_html(vis))
    (OUT / 'index.html').write_text(
        page('6M 動能月誌', 'home', body, desc='一場十年實驗的公開實驗室筆記'),
        encoding='utf-8')

    for r in vis:
        (OUT / 'journal' / f'{r["ym"]}.html').write_text(
            journal_page(r, vis, bs, rows), encoding='utf-8')
    (OUT / 'journal' / 'index.html').write_text(archive_page(vis), encoding='utf-8')
    (OUT / 'about.html').write_text(about_page(vis), encoding='utf-8')
    (OUT / 'factsheet.html').write_text(factsheet_page(), encoding='utf-8')
    (OUT / 'feed.xml').write_text(rss(vis), encoding='utf-8')
    print(f'完成：{len(vis)} 期月誌 + 首頁/總覽/關於/體檢表/RSS;'
          f'最新 {latest["issue"]}，煞車 {bs[latest["ym"]]:+.1f}pp，下月倉位 {nw*100:.1f}%')


if __name__ == '__main__':
    build()
