#!/usr/bin/env python3
"""
BankOS — Full Dashboard Generator v3
Private Banking level: Thesis tooltips, Sector tags, Rankings, Days counter
"""

import json, sys, subprocess
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent.parent / "investment-learning" / "scripts"))
from tracker_unified import get_portfolio_data, fetch_all_prices, SYMBOL_MAP

OUT_DIR   = Path(__file__).parent
RAW_JSON  = Path(__file__).parent.parent / "investment-learning" / "portfolios-5way.json"
DAILY_DIR = Path(__file__).parent.parent / "investment-learning" / "daily"
DAILY_DIR.mkdir(exist_ok=True)

EXPERIMENT_END = date(2026, 3, 19)

PORTFOLIO_META = {
    "SOLID":            {"slug": "turtle",  "emoji": "🐢", "color": "#6366f1", "heb": "שמרני"},
    "AGGRESSIVE":       {"slug": "lion",    "emoji": "🦁", "color": "#8b5cf6", "heb": "אגרסיבי"},
    "SUPER-AGGRESSIVE": {"slug": "rocket",  "emoji": "🚀", "color": "#ec4899", "heb": "סופר-אגרסיבי"},
    "SPECULATIVE":      {"slug": "target",  "emoji": "🎯", "color": "#f43f5e", "heb": "ספקולטיבי"},
    "CREATIVE":         {"slug": "canvas",  "emoji": "🎨", "color": "#f59e0b", "heb": "קריאטיבי"},
}

# Sector mapping (manual, based on TASE knowledge)
SECTORS = {
    "TLV:POLI":  "בנקאות",   "TLV:LUMI":  "בנקאות",   "TLV:HAPO":  "בנקאות",
    "TLV:MZTF":  "בנקאות",   "TLV:IGLD":  "בנקאות",
    "TLV:PHOE":  "ביטוח",    "TLV:HARL":  "ביטוח",    "TLV:MELN":  "ביטוח",
    "TLV:ESLT":  "ביטחון",   "TLV:ELTA":  "ביטחון",   "TLV:ELBIT": "ביטחון",
    "TLV:ELEC":  "אנרגיה",   "TLV:NWMD":  "אנרגיה",   "TLV:LPLI":  "אנרגיה",
    "TLV:NXSN":  "טכנולוגיה","TLV:ARYT":  "טכנולוגיה","TLV:MTDS":  "טכנולוגיה",
    "TLV:BIGA":  "נדל\"ן",   "TLV:AMOT":  "נדל\"ן",   "TLV:ISCN":  "נדל\"ן",
    "TLV:MORE":  "קמעונאות", "TLV:FTAL":  "תיירות",   "TLV:SAE":   "תיירות",
    "TLV:BIG":   "קמעונאות", "TLV:SPEN":  "קמעונאות",
}

SKIP_PREFIXES = ("BONDS:", "LEVERAGE:", "CRYPTO:", "TLV:DEFSMALL", "TLV:REIT", "TLV:POLI-PR")

# ─── SVG icons (Lucide) ───────────────────────────────────────────────────────
ICONS = {
    "percent":      '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="9" cy="9" r="2"/><circle cx="15" cy="15" r="2"/><line x1="17" y1="7" x2="7" y2="17"/></svg>',
    "wallet":       '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 12V8H6a2 2 0 0 1 0-4h14v4"/><path d="M20 12v4H6a2 2 0 0 0 0 4h14v-4"/></svg>',
    "trending-up":  '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    "trending-dn":  '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>',
    "arrow-left":   '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>',
    "refresh":      '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
    "chevron-right":'<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>',
    "info":         '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    "calendar":     '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    "award":        '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/></svg>',
}
def icon(name, cls="w-4 h-4"):
    return ICONS.get(name, "").replace("{c}", cls)

# ─── Finance ──────────────────────────────────────────────────────────────────
def net_withdrawal(gross: float, cost_basis: float) -> float:
    """What you'd receive if you sold everything today (after sell fee + capital gains tax)."""
    gain     = gross - cost_basis
    sell_fee = gross * 0.001
    cgt      = max(0.0, gain) * 0.25
    return gross - sell_fee - cgt

def week_change_pct(hist):
    if len(hist) >= 2 and hist[0] > 0:
        return round((hist[-1] / hist[0] - 1) * 100, 2)
    return None

def days_left():
    return max(0, (EXPERIMENT_END - date.today()).days)

# ─── History ──────────────────────────────────────────────────────────────────
def fetch_weekly_history():
    try:
        import yfinance as yf
        out = {}
        for sym in set(v for v in SYMBOL_MAP.values() if v):
            try:
                hist = yf.Ticker(sym).history(period="7d", interval="1d")
                if hist.empty:
                    out[sym] = []; continue
                prices = [round(float(v), 4) for v in hist["Close"].tolist()]
                if sym.endswith(".TA") and prices and prices[0] > 500:
                    prices = [round(p/100, 4) for p in prices]
                out[sym] = prices
            except:
                out[sym] = []
        return out
    except:
        return {}

def sparkline_data(raw_portfolio, all_history, days=7):
    totals = [0.0] * days
    for pos in raw_portfolio["positions"]:
        sym = pos["symbol"]
        if any(sym.startswith(p) for p in SKIP_PREFIXES): continue
        shares = pos.get("shares", 0)
        if not shares: continue
        yahoo = SYMBOL_MAP.get(sym)
        hist  = all_history.get(yahoo, []) if yahoo else []
        if not hist:
            v = pos.get("buyPrice", 0) * shares
            for d in range(days): totals[d] += v
        else:
            h = hist[-days:] if len(hist) >= days else [hist[0]] * (days - len(hist)) + hist
            for d, price in enumerate(h): totals[d] += price * shares
    cash = raw_portfolio.get("cash", 0)
    return [round(v + cash) for v in totals]

# ─── Shared <head> ────────────────────────────────────────────────────────────
def head(title):
    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box}}
  body{{font-family:'Assistant',sans-serif;background:#0c1220;color:#e2e8f0;-webkit-font-smoothing:antialiased}}
  .glass{{background:rgba(15,23,42,.75);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(148,163,184,.1)}}
  .card{{background:rgba(22,33,55,.6);backdrop-filter:blur(10px);border:1px solid rgba(148,163,184,.07)}}
  @keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
  .rise{{animation:rise .38s ease both}}
  .rise:nth-child(1){{animation-delay:0s}}.rise:nth-child(2){{animation-delay:.06s}}
  .rise:nth-child(3){{animation-delay:.12s}}.rise:nth-child(4){{animation-delay:.18s}}
  .rise:nth-child(5){{animation-delay:.24s}}
  .lift{{transition:transform .18s,box-shadow .18s}}
  .lift:hover{{transform:translateY(-3px);box-shadow:0 20px 48px rgba(0,0,0,.5)}}
  hr{{border-color:rgba(148,163,184,.1)}}
  .tag{{display:inline-block;font-size:11px;padding:2px 8px;border-radius:99px;font-weight:600}}
  .thesis-row{{display:none;background:rgba(15,23,42,.6)}}
  .thesis-row.open{{display:table-row}}
</style>
</head>"""

# ─── INDEX ────────────────────────────────────────────────────────────────────
def build_index(portfolios, total, all_history, raw_by_name):
    now  = datetime.now()
    ts   = now.strftime("%d/%m/%Y %H:%M")
    dleft = days_left()

    # Rank portfolios by net P/L
    ranked = sorted(portfolios, key=lambda p: p["netPnL"], reverse=True)
    rank_map = {p["name"]: i+1 for i, p in enumerate(ranked)}

    # Overall totals
    base = 500_000
    gross = total["totalValue"]
    nw    = net_withdrawal(gross, base)
    gain  = gross - base
    pct   = gain / base * 100
    sign  = "+" if gain >= 0 else "−"
    vc    = "text-emerald-400" if gain >= 0 else "text-red-400"
    bc    = "border-emerald-500" if gain >= 0 else "border-red-500"

    # Best / Worst
    best  = ranked[0]
    worst = ranked[-1]

    cards = ""
    for i, p in enumerate(portfolios):
        m    = PORTFOLIO_META[p["name"]]
        raw  = raw_by_name[p["name"]]
        rank = rank_map[p["name"]]
        p_gross = p["totalValue"]
        p_nw    = net_withdrawal(p_gross, 100_000)
        p_gain  = p_gross - 100_000
        p_pct   = p_gain / 100_000 * 100
        p_sign  = "+" if p_gain >= 0 else "−"
        p_vc    = "text-emerald-400" if p_gain >= 0 else "text-red-400"
        p_badge = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" if p_gain >= 0 else "bg-red-500/10 text-red-400 border border-red-500/20"
        spark   = sparkline_data(raw, all_history, 7)
        s_color = "#10b981" if p_gain >= 0 else "#ef4444"
        sid     = f"sp{i}"

        rank_badge = ""
        if rank == 1:
            rank_badge = '<span class="tag bg-amber-500/20 text-amber-400 border border-amber-500/30 mr-1">🥇 מוביל</span>'
        elif rank == len(portfolios):
            rank_badge = '<span class="tag bg-slate-600/30 text-slate-400 border border-slate-600/30 mr-1">מפגר</span>'

        cards += f"""
<a href="{m['slug']}.html" class="card rounded-2xl p-5 lift rise block no-underline">
  <div class="flex justify-between items-start mb-3">
    <div class="flex items-center gap-3">
      <span class="text-2xl">{m['emoji']}</span>
      <div>
        <p class="font-bold text-white text-sm leading-tight">{p['name']}</p>
        <p class="text-slate-500 text-xs">{m['heb']}</p>
      </div>
    </div>
    <div class="text-right">
      {rank_badge}
      <span class="tag {p_badge}">{p_sign}{abs(p_pct):.2f}%</span>
    </div>
  </div>

  <div class="mb-0.5">
    <span class="text-2xl font-extrabold text-white">₪{p_gross:,.0f}</span>
  </div>
  <div class="flex items-baseline gap-1.5 mb-3">
    <span class="text-slate-400 text-xs">בנק:</span>
    <span class="text-slate-300 text-sm font-semibold">₪{p_nw:,.0f}</span>
    <span class="text-slate-600 text-xs">(לאחר מס ועמלה)</span>
  </div>
  <div class="{p_vc} text-xs font-semibold mb-3">{p_sign}₪{abs(p_gain):,.0f} מ-Day 0</div>

  <div style="height:32px"><canvas id="{sid}"></canvas></div>
  <div class="flex justify-between items-center mt-3">
    <span class="text-slate-600 text-xs">{p['positionsCount']} נכסים</span>
    <span class="text-slate-600">{icon('chevron-right','w-3.5 h-3.5')}</span>
  </div>
</a>
<script>(function(){{
  var d={json.dumps(spark)};
  new Chart(document.getElementById('{sid}'),{{
    type:'line',data:{{datasets:[{{data:d,borderColor:'{s_color}',borderWidth:1.5,
      pointRadius:0,fill:true,backgroundColor:'{s_color}15',tension:.4}}]}},
    options:{{responsive:true,maintainAspectRatio:false,animation:false,
      scales:{{x:{{display:false}},y:{{display:false}}}},
      plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}}
    }}
  }});
}})();</script>"""

    return f"""{head('BankOS — תיקי נועם 2026')}
<body class="pb-24 px-4">

<header class="pt-8 pb-5">
  <div class="flex items-center gap-2 mb-2">
    <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
    <span class="text-emerald-400 text-xs font-semibold tracking-widest uppercase">Live</span>
  </div>
  <div class="flex items-start justify-between">
    <div>
      <h1 class="text-2xl font-extrabold text-white">BankOS</h1>
      <p class="text-slate-500 text-xs mt-0.5">עודכן {ts}</p>
    </div>
    <div class="text-right">
      <span class="flex items-center gap-1 text-slate-400 text-xs justify-end">{icon('calendar','w-3.5 h-3.5')} {dleft} ימים לסיום</span>
      <span class="text-slate-600 text-xs">19 מרץ 2026</span>
    </div>
  </div>
</header>

<!-- Total hero -->
<div class="glass rounded-2xl p-5 mb-5 border-r-4 {bc}">
  <p class="text-slate-500 text-xs uppercase tracking-wide mb-2 font-medium">סך הכל — 5 תיקים</p>
  <div class="flex items-baseline gap-2 flex-wrap mb-1">
    <span class="text-4xl font-extrabold text-white">₪{gross:,.0f}</span>
    <span class="text-slate-400 text-sm">שווי שוק</span>
  </div>
  <div class="flex items-baseline gap-1.5 mb-2">
    <span class="text-slate-400 text-xs">לאחר מכירת הכל:</span>
    <span class="text-slate-200 font-bold">₪{nw:,.0f}</span>
    <span class="text-slate-600 text-xs">(מס 25% + עמלה 0.1%)</span>
  </div>
  <p class="{vc} text-sm font-semibold">{sign}₪{abs(gain):,.0f} · {sign}{abs(pct):.2f}% מ-Day 0</p>

  <hr class="my-3">
  <div class="grid grid-cols-3 gap-3 text-xs text-slate-500">
    <div class="flex items-center gap-1">{icon('percent','w-3.5 h-3.5')} עמלות ₪{total['fees']:,.0f}</div>
    <div class="flex items-center gap-1">{icon('trending-up','w-3.5 h-3.5')} מס ₪{total['tax']:,.0f}</div>
    <div class="flex items-center gap-1">{icon('wallet','w-3.5 h-3.5')} base ₪500K</div>
  </div>
</div>

<!-- Best/Worst strip -->
<div class="grid grid-cols-2 gap-3 mb-5">
  <div class="card rounded-xl p-3 border-r-2 border-emerald-500">
    <p class="text-slate-500 text-xs mb-1">🏆 מוביל</p>
    <p class="text-white font-bold text-sm">{best['name']}</p>
    <p class="text-emerald-400 text-xs">{best['netReturnPct']:+.2f}%</p>
  </div>
  <div class="card rounded-xl p-3 border-r-2 border-red-500">
    <p class="text-slate-500 text-xs mb-1">📉 מפגר</p>
    <p class="text-white font-bold text-sm">{worst['name']}</p>
    <p class="text-red-400 text-xs">{worst['netReturnPct']:+.2f}%</p>
  </div>
</div>

<!-- Cards -->
<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
{cards}
</div>

<!-- Legend -->
<div class="card rounded-xl p-4 mt-5 text-xs text-slate-500 leading-relaxed">
  <p class="font-semibold text-slate-400 mb-2">{icon('info','w-3.5 h-3.5 inline-block ml-1')} מה המספרים אומרים</p>
  <p><span class="text-white font-semibold">₪X,XXX (שווי שוק)</span> — מחיר כל הנכסים + מזומן כרגע</p>
  <p class="mt-1"><span class="text-white font-semibold">בנק: ₪X,XXX</span> — מה ייכנס לחשבון אם תמכור הכל היום</p>
  <p class="mt-1">ניכויים: מס רווחי הון 25% (על רווח בלבד) + עמלת מכירה 0.1%</p>
  <p class="mt-1 text-slate-600">ביום 0: בנק = שווי שוק − ₪100 עמלה = ₪99,900 ✓</p>
</div>

<nav class="fixed bottom-0 inset-x-0 glass border-t h-14 flex items-center justify-between px-6">
  <span class="text-white text-sm font-bold">📊 תיקים</span>
  <button onclick="location.reload()" class="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors">
    {icon('refresh','w-4 h-4')} רענן
  </button>
</nav>
</body></html>"""


# ─── DEEP-DIVE ────────────────────────────────────────────────────────────────
def build_deep(raw_portfolio, perf, all_history):
    name   = raw_portfolio["name"]
    m      = PORTFOLIO_META[name]
    now    = datetime.now().strftime("%d/%m/%Y %H:%M")
    prices = fetch_all_prices()
    cash   = raw_portfolio.get("cash", 0)
    dleft  = days_left()

    p_gross = perf["totalValue"]
    p_nw    = net_withdrawal(p_gross, 100_000)
    p_gain  = p_gross - 100_000
    p_pct   = p_gain / 100_000 * 100
    p_sign  = "+" if p_gain >= 0 else "−"
    vc      = "text-emerald-400" if p_gain >= 0 else "text-red-400"
    bc      = "border-emerald-500" if p_gain >= 0 else "border-red-500"

    # Holdings
    rows = ""
    pie_l, pie_v, pie_c = [], [], []
    sector_totals = {}
    PALETTE = ["#6366f1","#8b5cf6","#ec4899","#f43f5e","#f59e0b",
               "#10b981","#0ea5e9","#a855f7","#d946ef","#f97316","#84cc16","#14b8a6"]
    idx = 0
    best_pos = ("", -999)
    worst_pos = ("", 999)

    for pos in raw_portfolio["positions"]:
        sym = pos["symbol"]
        if any(sym.startswith(p) for p in SKIP_PREFIXES): continue
        shares = pos.get("shares", 0)
        if not shares: continue

        buy_p  = pos.get("buyPrice", 0)
        cur_p  = prices.get(sym, buy_p)
        val    = shares * cur_p
        gain   = (cur_p - buy_p) * shares
        sell_f = val * 0.001
        cgt    = max(0, gain) * 0.25
        net_p  = gain - sell_f - cgt
        net_pct = (net_p / (buy_p * shares) * 100) if buy_p * shares > 0 else 0

        yahoo  = SYMBOL_MAP.get(sym)
        hist   = all_history.get(yahoo, []) if yahoo else []
        wk_pct = week_change_pct(hist)
        wk_str = f"{wk_pct:+.1f}%" if wk_pct is not None else "—"
        wk_cls = "text-emerald-400" if (wk_pct or 0) >= 0 else "text-red-400"
        np_cls = "text-emerald-400" if net_pct >= 0 else "text-red-400"

        sector = SECTORS.get(sym, "אחר")
        thesis = pos.get("thesis", "")
        short  = sym.split(":")[-1].replace(".TA","")
        row_id = f"row_{idx}"

        # Track best/worst
        if wk_pct is not None:
            if wk_pct > best_pos[1]: best_pos = (short, wk_pct)
            if wk_pct < worst_pos[1]: worst_pos = (short, wk_pct)

        # Sector aggregation
        sector_totals[sector] = sector_totals.get(sector, 0) + val

        rows += f"""<tr class="border-b border-slate-700/20 hover:bg-slate-800/20 cursor-pointer transition-colors"
     onclick="document.getElementById('{row_id}').classList.toggle('open')">
  <td class="py-3 pr-3">
    <div class="font-bold text-sm text-white leading-none">{short}</div>
    <div class="text-xs text-slate-500 mt-0.5">{sector}</div>
  </td>
  <td class="py-3 text-slate-400 text-sm">{shares:.1f}</td>
  <td class="py-3 text-slate-300 text-sm">₪{cur_p:,.2f}</td>
  <td class="py-3 text-white text-sm font-semibold">₪{val:,.0f}</td>
  <td class="py-3 text-sm {np_cls}"><b>{net_pct:+.1f}%</b><br><span class="text-xs opacity-60">₪{net_p:+,.0f}</span></td>
  <td class="py-3 text-sm {wk_cls} font-semibold">{wk_str}</td>
  <td class="py-3 text-slate-600 text-xs">{icon('chevron-right','w-3 h-3')}</td>
</tr>
<tr id="{row_id}" class="thesis-row">
  <td colspan="7" class="px-4 py-3 text-sm text-slate-300 leading-relaxed">
    <span class="text-slate-500 font-semibold">📌 למה נבחר:</span> {thesis or "—"}
  </td>
</tr>"""

        color = PALETTE[idx % len(PALETTE)]
        pie_l.append(short); pie_v.append(round(val)); pie_c.append(color)
        idx += 1

    # Add cash to pie
    if cash > 0:
        sector_totals["מזומן"] = cash
        pie_l.append("מזומן"); pie_v.append(round(cash)); pie_c.append("#334155")

    # Sector pie data
    sec_labels = list(sector_totals.keys())
    sec_values = [round(v) for v in sector_totals.values()]
    SEC_COLORS  = ["#6366f1","#8b5cf6","#ec4899","#f43f5e","#f59e0b","#10b981","#0ea5e9","#334155"]

    return f"""{head(f'BankOS — {m["emoji"]} {name}')}
<body class="pb-24">
<div class="max-w-xl mx-auto px-4">

  <!-- Back -->
  <div class="pt-6 pb-3">
    <a href="index.html" class="inline-flex items-center gap-2 text-slate-500 hover:text-white text-sm transition-colors">
      {icon('arrow-left','w-4 h-4')} חזרה
    </a>
  </div>

  <!-- Hero -->
  <div class="glass rounded-2xl p-5 mb-5 border-r-4 {bc}">
    <div class="flex items-center gap-3 mb-4">
      <span class="text-4xl">{m['emoji']}</span>
      <div>
        <h1 class="text-xl font-extrabold text-white">{name}</h1>
        <p class="text-slate-400 text-sm">{m['heb']} · {dleft} ימים לסיום</p>
      </div>
    </div>

    <div class="mb-0.5">
      <span class="text-3xl font-extrabold text-white">₪{p_gross:,.0f}</span>
      <span class="text-slate-500 text-sm mr-2">שווי שוק</span>
    </div>
    <div class="flex items-baseline gap-1.5 mb-2">
      <span class="text-slate-400 text-xs">לאחר מכירה:</span>
      <span class="text-slate-200 font-bold text-lg">₪{p_nw:,.0f}</span>
    </div>
    <p class="{vc} text-sm font-semibold">{p_sign}₪{abs(p_gain):,.0f} · {p_sign}{abs(p_pct):.2f}% מ-Day 0</p>

    <hr class="my-3">
    <div class="grid grid-cols-3 gap-2 text-xs text-slate-500">
      <div>{icon('percent','w-3 h-3 inline ml-1')} ₪{perf['fees']:,.0f} עמלות</div>
      <div>{icon('trending-up','w-3 h-3 inline ml-1')} ₪{perf['tax']:,.0f} מס</div>
      <div>{icon('wallet','w-3 h-3 inline ml-1')} ₪{cash:,.0f} מזומן</div>
    </div>
  </div>

  <!-- Best/Worst this week -->
  {'<div class="grid grid-cols-2 gap-3 mb-5">' +
   f'<div class="card rounded-xl p-3 border-r-2 border-emerald-500"><p class="text-slate-500 text-xs mb-1">🏆 שבוע</p><p class="text-white font-bold text-sm">{best_pos[0]}</p><p class="text-emerald-400 text-xs">{best_pos[1]:+.1f}%</p></div>' +
   f'<div class="card rounded-xl p-3 border-r-2 border-red-500"><p class="text-slate-500 text-xs mb-1">📉 שבוע</p><p class="text-white font-bold text-sm">{worst_pos[0]}</p><p class="text-red-400 text-xs">{worst_pos[1]:+.1f}%</p></div>'
   + '</div>'
   if best_pos[0] and worst_pos[0] and best_pos[0] != worst_pos[0] else ''}

  <!-- Charts row -->
  <div class="grid grid-cols-2 gap-3 mb-5">
    <div class="card rounded-2xl p-4">
      <h2 class="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3">פיזור נכסים</h2>
      <div style="height:160px"><canvas id="pie1"></canvas></div>
    </div>
    <div class="card rounded-2xl p-4">
      <h2 class="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3">סקטורים</h2>
      <div style="height:160px"><canvas id="pie2"></canvas></div>
    </div>
  </div>

  <!-- Holdings Table -->
  <div class="card rounded-2xl p-4 mb-5 overflow-x-auto">
    <h2 class="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3">
      אחזקות
      <span class="text-slate-600 font-normal normal-case mr-2">לחץ על שורה לראות סיבת הבחירה</span>
    </h2>
    <table class="w-full text-right" style="min-width:420px">
      <thead>
        <tr class="text-slate-500 text-xs border-b border-slate-700/30">
          <th class="pb-2 pr-3">נכס</th>
          <th class="pb-2">יחידות</th>
          <th class="pb-2">מחיר</th>
          <th class="pb-2">שווי</th>
          <th class="pb-2">P/L נטו</th>
          <th class="pb-2">1W</th>
          <th class="pb-2"></th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>

  <p class="text-center text-slate-600 text-xs mb-8">
    עודכן {now} · מס 25% על רווח בלבד · עמלה 0.1% קנייה + 0.1% מכירה
  </p>
</div>

<nav class="fixed bottom-0 inset-x-0 glass border-t h-14 flex items-center justify-between px-6">
  <a href="index.html" class="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors">
    {icon('arrow-left','w-4 h-4')} ראשי
  </a>
  <span class="text-white text-sm font-semibold">{m['emoji']} {name}</span>
  <button onclick="location.reload()" class="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors">
    {icon('refresh','w-4 h-4')}
  </button>
</nav>

<script>
// Asset allocation pie
new Chart(document.getElementById('pie1'),{{
  type:'doughnut',
  data:{{labels:{json.dumps(pie_l,ensure_ascii=False)},
    datasets:[{{data:{json.dumps(pie_v)},backgroundColor:{json.dumps(pie_c)},borderWidth:0,hoverOffset:5}}]}},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'62%',
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>'₪'+c.parsed.toLocaleString()}}}}}}
  }}
}});
// Sector pie
new Chart(document.getElementById('pie2'),{{
  type:'doughnut',
  data:{{labels:{json.dumps(sec_labels,ensure_ascii=False)},
    datasets:[{{data:{json.dumps(sec_values)},backgroundColor:{json.dumps(SEC_COLORS[:len(sec_labels)])},borderWidth:0,hoverOffset:5}}]}},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'62%',
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>c.label+': ₪'+c.parsed.toLocaleString()}}}}}}
  }}
}});
</script>
</body></html>"""


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'─'*54}")
    print(f"  BankOS v3  ·  {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'─'*54}\n")

    print("  Fetching prices …")
    data = get_portfolio_data()
    print(f"  ✓ {data['pricesCount']} prices")

    raw_data    = json.loads(RAW_JSON.read_text(encoding="utf-8"))
    raw_by_name = {p["name"]: p for p in raw_data["portfolios"]}

    print("  Fetching 7-day history …")
    all_history = fetch_weekly_history()
    print(f"  ✓ history for {sum(1 for h in all_history.values() if h)} symbols")

    now = datetime.now()

    # Index
    print("  Building index.html …")
    html = build_index(data["portfolios"], data["total"], all_history, raw_by_name)
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"  ✓ {len(html):,} bytes")

    # Deep pages
    for p_perf in data["portfolios"]:
        m = PORTFOLIO_META[p_perf["name"]]
        print(f"  Building {m['slug']}.html …")
        html = build_deep(raw_by_name[p_perf["name"]], p_perf, all_history)
        (OUT_DIR / f"{m['slug']}.html").write_text(html, encoding="utf-8")
        print(f"  ✓ {len(html):,} bytes")

    # Daily snapshot
    snap = DAILY_DIR / f"{now.strftime('%Y-%m-%d')}-snapshot.txt"
    lines = [f"BankOS {now.strftime('%Y-%m-%d %H:%M')}",
             f"Total: ₪{data['total']['totalValue']:,.2f}", ""]
    for p in data["portfolios"]:
        lines.append(f"  {p['name']:20s} ₪{p['totalValue']:>10,.2f}  {p['netReturnPct']:+.2f}%")
    snap.write_text("\n".join(lines), encoding="utf-8")

    # Push
    print("\n  Pushing to GitHub …")
    for cmd in [
        ["git", "-C", str(OUT_DIR), "add", "-A"],
        ["git", "-C", str(OUT_DIR), "commit", "-m", f"Live {now.strftime('%Y-%m-%d %H:%M')}"],
        ["git", "-C", str(OUT_DIR), "push"],
    ]:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if "nothing to commit" in (r.stdout + r.stderr):
            print("  ↳ nothing changed"); break
    else:
        if r.returncode == 0:
            print("  ✓ pushed")
        else:
            print(f"  ✗ {r.stderr[:80]}")

    print(f"\n  https://noamm-opencalw.github.io/investment-dashboard/")
    print(f"{'─'*54}\n")

if __name__ == "__main__":
    main()
