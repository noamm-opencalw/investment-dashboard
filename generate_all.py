#!/usr/bin/env python3
"""
BankOS — Full Dashboard Generator v2
Private Banking level UI: clean typography, Lucide SVG icons, Gross (Net) display
"""

import json, sys, subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "investment-learning" / "scripts"))
from tracker_unified import get_portfolio_data, fetch_all_prices, SYMBOL_MAP

OUT_DIR   = Path(__file__).parent
RAW_JSON  = Path(__file__).parent.parent / "investment-learning" / "portfolios-5way.json"
DAILY_DIR = Path(__file__).parent.parent / "investment-learning" / "daily"
DAILY_DIR.mkdir(exist_ok=True)

PORTFOLIO_META = {
    "SOLID":            {"slug": "turtle",  "emoji": "🐢", "color": "#6366f1"},
    "AGGRESSIVE":       {"slug": "lion",    "emoji": "🦁", "color": "#8b5cf6"},
    "SUPER-AGGRESSIVE": {"slug": "rocket",  "emoji": "🚀", "color": "#ec4899"},
    "SPECULATIVE":      {"slug": "target",  "emoji": "🎯", "color": "#f43f5e"},
    "CREATIVE":         {"slug": "canvas",  "emoji": "🎨", "color": "#f59e0b"},
}

SKIP_PREFIXES = ("BONDS:", "LEVERAGE:", "CRYPTO:", "TLV:DEFSMALL", "TLV:REIT", "TLV:POLI-PR")

# ─── SVG icons (Lucide style) ─────────────────────────────────────────────────
def icon(name, cls="w-4 h-4"):
    icons = {
        "percent":     '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="9" cy="9" r="2"/><circle cx="15" cy="15" r="2"/><line x1="17" y1="7" x2="7" y2="17"/></svg>',
        "wallet":      '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M16 12h.01"/></svg>',
        "trending":    '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
        "arrow-left":  '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>',
        "refresh":     '<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
        "chevron-right":'<svg class="{c}" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>',
    }
    return icons.get(name, "").replace("{c}", cls)

# ─── Financial helpers ────────────────────────────────────────────────────────
def calc_net_withdrawal(gross_value: float, cost_basis: float) -> float:
    """What you'd actually receive selling everything today."""
    gain        = gross_value - cost_basis
    sell_fee    = gross_value * 0.001          # 0.1% sell commission
    capital_tax = max(0, gain) * 0.25          # 25% on gains only
    return gross_value - sell_fee - capital_tax

def week_change_pct(history: list) -> float | None:
    if len(history) >= 2 and history[0] > 0:
        return round((history[-1] / history[0] - 1) * 100, 2)
    return None

def fetch_weekly_history(symbols: list) -> dict:
    try:
        import yfinance as yf
        out = {}
        for sym in symbols:
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

# ─── Shared head ─────────────────────────────────────────────────────────────
HEAD = lambda title: f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box}}
  body{{font-family:'Assistant',sans-serif;background:#0c1220;color:#e2e8f0;-webkit-font-smoothing:antialiased;min-height:100vh}}
  .glass{{background:rgba(15,23,42,.7);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(148,163,184,.1)}}
  .glass-card{{background:rgba(30,41,59,.45);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid rgba(148,163,184,.08)}}
  @keyframes rise{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:none}}}}
  .rise{{animation:rise .4s ease both}}
  .rise:nth-child(1){{animation-delay:.00s}}.rise:nth-child(2){{animation-delay:.06s}}
  .rise:nth-child(3){{animation-delay:.12s}}.rise:nth-child(4){{animation-delay:.18s}}
  .rise:nth-child(5){{animation-delay:.24s}}
  .hover-lift{{transition:transform .2s,box-shadow .2s}}
  .hover-lift:hover{{transform:translateY(-3px);box-shadow:0 16px 40px rgba(0,0,0,.45)}}
  .divider{{border-color:rgba(148,163,184,.1)}}
</style>
</head>"""

# ─── Index page ───────────────────────────────────────────────────────────────
def build_index(portfolios, total, now, all_history, raw_by_name):
    ts = now.strftime("%d/%m/%Y %H:%M")

    # Total gross + net withdrawal
    all_prices = fetch_all_prices()
    total_cost  = 100_000 * 5   # day 0 baseline
    total_gross = total["totalValue"]
    total_net   = calc_net_withdrawal(total_gross, total_cost)
    total_gain  = total_gross - total_cost
    total_pct   = (total_gain / total_cost * 100)

    sign = "+" if total_gain >= 0 else "−"
    val_color = "text-emerald-400" if total_gain >= 0 else "text-red-400"

    # Portfolio cards
    cards_html = ""
    for i, p in enumerate(portfolios):
        m = PORTFOLIO_META[p["name"]]
        raw = raw_by_name[p["name"]]

        # Calc gross / net for this portfolio
        p_cost   = 100_000
        p_gross  = p["totalValue"]
        p_net    = calc_net_withdrawal(p_gross, p_cost)
        p_gain   = p_gross - p_cost
        p_pct    = (p_gain / p_cost * 100)
        p_sign   = "+" if p_gain >= 0 else "−"
        p_vcls   = "text-emerald-400" if p_gain >= 0 else "text-red-400"
        p_bcls   = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" if p_gain >= 0 else "bg-red-500/10 text-red-400 border border-red-500/20"

        # Sparkline
        spark = _sparkline_data(raw, all_history, 7)
        spark_color = "#10b981" if p_gain >= 0 else "#ef4444"
        sid = f"sp{i}"

        cards_html += f"""
<a href="{m['slug']}.html" class="glass-card rounded-2xl p-5 hover-lift rise block no-underline">
  <div class="flex justify-between items-start mb-4">
    <div class="flex items-center gap-3">
      <span class="text-2xl">{m['emoji']}</span>
      <div>
        <p class="font-bold text-white text-sm leading-none">{p['name']}</p>
        <p class="text-slate-500 text-xs mt-0.5">{p['nickname']}</p>
      </div>
    </div>
    <span class="text-xs font-bold px-2.5 py-1 rounded-full {p_bcls}">{p_sign}{abs(p_pct):.2f}%</span>
  </div>

  <div class="mb-1">
    <span class="text-2xl font-extrabold text-white">₪{p_gross:,.0f}</span>
    <span class="text-slate-400 text-sm mr-1">(₪{p_net:,.0f})</span>
  </div>
  <p class="{p_vcls} text-xs font-semibold mb-4">{p_sign}₪{abs(p_gain):,.0f} {p_sign}{abs(p_pct):.2f}%</p>

  <div style="height:36px;"><canvas id="{sid}"></canvas></div>
  <div class="flex justify-between items-center mt-3">
    <span class="text-slate-600 text-xs">{p['positionsCount']} נכסים</span>
    <span class="text-slate-600">{icon('chevron-right','w-3.5 h-3.5')}</span>
  </div>
</a>
<script>
(function(){{
  var d={json.dumps(spark)};
  new Chart(document.getElementById('{sid}'),{{
    type:'line',
    data:{{datasets:[{{data:d,borderColor:'{spark_color}',borderWidth:1.5,
      pointRadius:0,fill:true,backgroundColor:'{spark_color}18',tension:.45}}]}},
    options:{{responsive:true,maintainAspectRatio:false,animation:false,
      scales:{{x:{{display:false}},y:{{display:false}}}},
      plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}}}}
  }});
}})();
</script>"""

    return f"""{HEAD('BankOS — תיקי נועם 2026')}
<body class="pb-20">

<!-- Header -->
<header class="px-5 pt-8 pb-6">
  <div class="flex items-center gap-2 mb-3">
    <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
    <span class="text-emerald-400 text-xs tracking-widest font-semibold uppercase">Live · Day 0</span>
  </div>
  <h1 class="text-2xl font-extrabold text-white tracking-tight">BankOS</h1>
  <p class="text-slate-500 text-xs mt-1">עודכן {ts} · net after tax &amp; fees</p>
</header>

<!-- Total hero -->
<div class="mx-4 mb-6 glass rounded-2xl p-5">
  <p class="text-slate-400 text-xs mb-2 uppercase tracking-wide font-medium">סה"כ תיקים</p>
  <div class="flex items-baseline gap-2 flex-wrap">
    <span class="text-4xl font-extrabold text-white">₪{total_gross:,.0f}</span>
    <span class="text-slate-400 text-base">(₪{total_net:,.0f} נטו)</span>
  </div>
  <p class="{val_color} text-sm font-semibold mt-1">{sign}₪{abs(total_gain):,.0f} · {sign}{abs(total_pct):.2f}%</p>

  <div class="divider border-t mt-4 pt-4 flex gap-4 text-xs text-slate-500">
    <span class="flex items-center gap-1.5">{icon('percent','w-3.5 h-3.5')} עמלות ₪{total['fees']:,.0f}</span>
    <span class="flex items-center gap-1.5">{icon('trending','w-3.5 h-3.5')} מס ₪{total['tax']:,.0f}</span>
    <span class="flex items-center gap-1.5">{icon('wallet','w-3.5 h-3.5')} ₪500,000 base</span>
  </div>
</div>

<!-- Portfolio cards -->
<div class="px-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
  {cards_html}
</div>

<!-- Footer note -->
<p class="text-center text-slate-600 text-xs mt-6 mb-2">
  ₪X,XXX = שווי שוק · (₪X,XXX) = לאחר מס 25% + עמלה 0.1%
</p>

<!-- Bottom nav -->
<nav class="fixed bottom-0 inset-x-0 glass border-t divider h-14 flex items-center justify-between px-6">
  <span class="text-white text-sm font-bold">📊 תיקים</span>
  <button onclick="location.reload()" class="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors">
    {icon('refresh','w-4 h-4')} רענן
  </button>
</nav>
</body></html>"""


# ─── Deep-dive page ───────────────────────────────────────────────────────────
def build_deep(raw_portfolio, perf, all_history):
    name  = raw_portfolio["name"]
    m     = PORTFOLIO_META[name]
    now   = datetime.now().strftime("%d/%m/%Y %H:%M")
    prices = fetch_all_prices()
    cash   = raw_portfolio.get("cash", 0)

    # Calc totals
    cost_basis = 100_000
    p_gross = perf["totalValue"]
    p_net   = calc_net_withdrawal(p_gross, cost_basis)
    p_gain  = p_gross - cost_basis
    p_pct   = (p_gain / cost_basis * 100)
    p_sign  = "+" if p_gain >= 0 else "−"
    vcls    = "text-emerald-400" if p_gain >= 0 else "text-red-400"
    bcls    = "border-emerald-500" if p_gain >= 0 else "border-red-500"

    # Holdings + pie
    rows, pie_l, pie_v, pie_c = "", [], [], []
    PALETTE = ["#6366f1","#8b5cf6","#ec4899","#f43f5e","#f59e0b","#10b981","#0ea5e9","#a855f7","#d946ef","#f97316","#84cc16","#14b8a6"]

    idx = 0
    for pos in raw_portfolio["positions"]:
        sym = pos["symbol"]
        if any(sym.startswith(p) for p in SKIP_PREFIXES):
            continue
        shares = pos.get("shares", 0)
        if shares == 0:
            continue

        buy_p  = pos.get("buyPrice", 0)
        cur_p  = prices.get(sym, buy_p)
        val    = shares * cur_p
        gain   = (cur_p - buy_p) * shares
        sell_fee = val * 0.001
        tax_c  = max(0, gain) * 0.25
        net_p  = gain - sell_fee - tax_c
        net_pct = (net_p / (buy_p * shares) * 100) if buy_p * shares > 0 else 0

        yahoo = SYMBOL_MAP.get(sym)
        hist  = all_history.get(yahoo, []) if yahoo else []
        wk_pct = week_change_pct(hist)
        wk_str = f"{wk_pct:+.1f}%" if wk_pct is not None else "—"
        wk_cls = "text-emerald-400" if (wk_pct or 0) >= 0 else "text-red-400"
        np_cls = "text-emerald-400" if net_pct >= 0 else "text-red-400"

        short = sym.split(":")[-1].replace(".TA","")

        rows += f"""<tr class="border-b divider hover:bg-slate-800/30 transition-colors">
  <td class="py-3 pr-3 font-bold text-sm text-white">{short}</td>
  <td class="py-3 text-slate-400 text-sm text-left">{shares:.1f}</td>
  <td class="py-3 text-slate-300 text-sm text-left">₪{cur_p:,.2f}</td>
  <td class="py-3 text-white text-sm font-semibold text-left">₪{val:,.0f}</td>
  <td class="py-3 text-sm text-left {np_cls}"><span class="font-semibold">{net_pct:+.1f}%</span><br><span class="text-xs opacity-70">₪{net_p:+,.0f}</span></td>
  <td class="py-3 text-sm text-left {wk_cls} font-semibold">{wk_str}</td>
</tr>"""

        color = PALETTE[idx % len(PALETTE)]
        pie_l.append(short); pie_v.append(round(val)); pie_c.append(color)
        idx += 1

    if cash > 0:
        pie_l.append("מזומן"); pie_v.append(round(cash)); pie_c.append("#475569")

    return f"""{HEAD(f'BankOS — {m["emoji"]} {name}')}
<body class="pb-20">

<div class="max-w-xl mx-auto px-4">

  <!-- Back -->
  <div class="pt-6 pb-4">
    <a href="index.html" class="inline-flex items-center gap-2 text-slate-400 hover:text-white text-sm transition-colors">
      {icon('arrow-left','w-4 h-4')} חזרה לתיקים
    </a>
  </div>

  <!-- Hero -->
  <div class="glass-card rounded-2xl p-6 mb-5 border-r-4 {bcls}">
    <div class="flex items-center gap-3 mb-4">
      <span class="text-4xl">{m['emoji']}</span>
      <div>
        <h1 class="text-xl font-extrabold text-white">{name}</h1>
        <p class="text-slate-400 text-sm">{perf['nickname']}</p>
      </div>
    </div>
    <div class="flex items-baseline gap-2 flex-wrap mb-1">
      <span class="text-3xl font-extrabold text-white">₪{p_gross:,.0f}</span>
      <span class="text-slate-400">(₪{p_net:,.0f} נטו)</span>
    </div>
    <p class="{vcls} text-sm font-semibold">{p_sign}₪{abs(p_gain):,.0f} · {p_sign}{abs(p_pct):.2f}%</p>
    <div class="divider border-t mt-4 pt-4 grid grid-cols-3 gap-2 text-xs text-slate-500">
      <span class="flex items-center gap-1">{icon('percent','w-3 h-3')} ₪{perf['fees']:,.0f}</span>
      <span class="flex items-center gap-1">{icon('trending','w-3 h-3')} ₪{perf['tax']:,.0f}</span>
      <span class="flex items-center gap-1">{icon('wallet','w-3 h-3')} ₪{cash:,.0f}</span>
    </div>
  </div>

  <!-- Asset Allocation -->
  <div class="glass-card rounded-2xl p-5 mb-5">
    <h2 class="text-sm font-bold text-slate-300 uppercase tracking-wide mb-4">Asset Allocation</h2>
    <div class="flex items-center justify-center" style="height:200px">
      <canvas id="pie"></canvas>
    </div>
  </div>

  <!-- Holdings Table -->
  <div class="glass-card rounded-2xl p-5 mb-5 overflow-x-auto">
    <h2 class="text-sm font-bold text-slate-300 uppercase tracking-wide mb-4">Holdings</h2>
    <table class="w-full text-right" style="min-width:440px">
      <thead>
        <tr class="text-slate-500 text-xs border-b divider">
          <th class="pb-2 pr-3 text-right">סימבול</th>
          <th class="pb-2 text-left">יחידות</th>
          <th class="pb-2 text-left">מחיר</th>
          <th class="pb-2 text-left">שווי</th>
          <th class="pb-2 text-left">P/L נטו</th>
          <th class="pb-2 text-left">1W</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    {'<p class="text-slate-600 text-xs mt-3">+ מזומן ₪' + f"{cash:,.0f}</p>" if cash > 0 else ''}
  </div>

  <p class="text-center text-slate-600 text-xs mb-8">עודכן {now} · Day 0 Baseline</p>
</div>

<!-- Bottom nav -->
<nav class="fixed bottom-0 inset-x-0 glass border-t divider h-14 flex items-center justify-between px-6">
  <a href="index.html" class="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors">
    {icon('arrow-left','w-4 h-4')} ראשי
  </a>
  <span class="text-white text-sm font-semibold">{m['emoji']} {name}</span>
  <button onclick="location.reload()" class="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors">
    {icon('refresh','w-4 h-4')}
  </button>
</nav>

<script>
new Chart(document.getElementById('pie'), {{
  type: 'doughnut',
  data: {{
    labels: {json.dumps(pie_l, ensure_ascii=False)},
    datasets: [{{ data: {json.dumps(pie_v)}, backgroundColor: {json.dumps(pie_c)}, borderWidth: 0, hoverOffset: 6 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false, cutout: '62%',
    plugins: {{
      legend: {{ display: true, position: 'bottom',
        labels: {{ color: '#94a3b8', font: {{ size: 11, family: 'Assistant' }}, padding: 14 }} }},
      tooltip: {{ callbacks: {{ label: c => '₪' + c.parsed.toLocaleString() }} }}
    }}
  }}
}});
</script>
</body></html>"""


# ─── Sparkline helper ─────────────────────────────────────────────────────────
def _sparkline_data(raw_portfolio, all_history, days=7):
    totals = [0.0] * days
    for pos in raw_portfolio["positions"]:
        sym = pos["symbol"]
        if any(sym.startswith(p) for p in SKIP_PREFIXES): continue
        shares = pos.get("shares", 0)
        if shares == 0: continue
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


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'─'*56}")
    print(f"  BankOS Generator v2  ·  {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'─'*56}\n")

    print("  Fetching prices …")
    data = get_portfolio_data()
    print(f"  ✓ {data['pricesCount']} prices")

    raw_data   = json.loads(RAW_JSON.read_text(encoding="utf-8"))
    raw_by_name = {p["name"]: p for p in raw_data["portfolios"]}
    for p in data["portfolios"]:
        p["_raw_positions"] = raw_by_name[p["name"]]["positions"]

    print("  Fetching 7-day history …")
    all_yahoo   = list(set(v for v in SYMBOL_MAP.values() if v))
    all_history = {}
    try:
        import yfinance as yf
        for sym in all_yahoo:
            try:
                hist = yf.Ticker(sym).history(period="7d", interval="1d")
                if not hist.empty:
                    prices = [round(float(v), 4) for v in hist["Close"].tolist()]
                    if sym.endswith(".TA") and prices and prices[0] > 500:
                        prices = [round(p/100, 4) for p in prices]
                    all_history[sym] = prices
                else:
                    all_history[sym] = []
            except:
                all_history[sym] = []
    except:
        pass
    print(f"  ✓ history for {sum(1 for h in all_history.values() if h)} symbols")

    now = datetime.now()
    ts  = now.strftime("%d/%m/%Y %H:%M")

    # Build index
    print("  Building index.html …")
    idx = build_index(data["portfolios"], data["total"], now, all_history, raw_by_name)
    (OUT_DIR / "index.html").write_text(idx, encoding="utf-8")
    print(f"  ✓ index.html ({len(idx):,} bytes)")

    # Build deep-dive pages
    for p_perf in data["portfolios"]:
        name = p_perf["name"]
        m    = PORTFOLIO_META[name]
        print(f"  Building {m['slug']}.html …")
        html = build_deep(raw_by_name[name], p_perf, all_history)
        (OUT_DIR / f"{m['slug']}.html").write_text(html, encoding="utf-8")
        print(f"  ✓ {m['slug']}.html ({len(html):,} bytes)")

    # Save daily snapshot
    snap = DAILY_DIR / f"{now.strftime('%Y-%m-%d')}-snapshot.txt"
    lines = [f"BankOS Snapshot — {ts}", f"Total: ₪{data['total']['totalValue']:,.2f}", ""]
    for p in data["portfolios"]:
        lines.append(f"{p['name']:20s} ₪{p['totalValue']:>12,.2f}  net {p['netReturnPct']:+.2f}%")
    snap.write_text("\n".join(lines), encoding="utf-8")

    # Git push
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
            print(f"  ✗ push error: {r.stderr[:100]}")

    print(f"\n  Live → https://noamm-opencalw.github.io/investment-dashboard/")
    print(f"{'─'*56}\n")

if __name__ == "__main__":
    main()
