#!/usr/bin/env python3
"""
BankOS - Full Dashboard Generator
Produces: index.html + 5 deep-dive pages
Design: Robinhood/Revolut level - Glassmorphism, Sparklines, Animations
"""

import json, sys, subprocess
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "investment-learning" / "scripts"))
from tracker_unified import get_portfolio_data, fetch_all_prices, SYMBOL_MAP, AGOROT_STOCKS

VENV_PYTHON = Path(__file__).parent.parent / "investment-learning" / ".venv-tracker" / "bin" / "python"
OUT_DIR = Path(__file__).parent

PORTFOLIO_META = {
    "SOLID":           {"slug":"turtle",     "emoji":"🐢","color":"#6366f1","gradient":"from-indigo-600 to-indigo-900"},
    "AGGRESSIVE":      {"slug":"lion",       "emoji":"🦁","color":"#8b5cf6","gradient":"from-violet-600 to-violet-900"},
    "SUPER-AGGRESSIVE":{"slug":"rocket",     "emoji":"🚀","color":"#ec4899","gradient":"from-pink-600 to-pink-900"},
    "SPECULATIVE":     {"slug":"target",     "emoji":"🎯","color":"#f43f5e","gradient":"from-rose-600 to-rose-900"},
    "CREATIVE":        {"slug":"canvas",     "emoji":"🎨","color":"#f59e0b","gradient":"from-amber-500 to-amber-800"},
}

# ─────────────────────────────────────────────
# Historical prices (1W sparkline)
# ─────────────────────────────────────────────
def fetch_weekly_history(yahoo_symbols: list[str]) -> dict:
    """Returns {yahoo_symbol: [list of 7 closing prices]}"""
    try:
        import yfinance as yf
        result = {}
        for sym in yahoo_symbols:
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="7d", interval="1d")
                if hist.empty:
                    result[sym] = []
                    continue
                prices = [round(float(v), 4) for v in hist["Close"].tolist()]
                # Agorot fix
                if sym.endswith(".TA") and prices and prices[0] > 1000:
                    prices = [round(p/100, 4) for p in prices]
                result[sym] = prices
            except:
                result[sym] = []
        return result
    except:
        return {}

def week_change_pct(history: list) -> float | None:
    if len(history) >= 2:
        start, end = history[0], history[-1]
        if start > 0:
            return round((end/start - 1)*100, 2)
    return None

# ─────────────────────────────────────────────
# Net P/L helpers
# ─────────────────────────────────────────────
def net_pnl(buy, current, shares):
    gross = (current - buy) * shares
    fees  = (buy * shares + current * shares) * 0.001
    tax   = gross * 0.25 if gross > 0 else 0
    return gross - fees - tax

def fmt_ils(v, sign=False):
    s = f"₪{abs(v):,.0f}"
    if sign: s = ("+" if v >= 0 else "−") + s
    return s

# ─────────────────────────────────────────────
# Shared CSS / head
# ─────────────────────────────────────────────
HEAD = """<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>
  body{font-family:'Assistant',sans-serif;background:#0f172a;color:#f1f5f9;-webkit-font-smoothing:antialiased}
  .glass{background:rgba(30,41,59,.6);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.08)}
  .card-hover{transition:transform .25s,box-shadow .25s}
  .card-hover:hover{transform:translateY(-4px);box-shadow:0 20px 40px rgba(0,0,0,.4)}
  @keyframes fade-up{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
  .fade-up{animation:fade-up .5s ease both}
  .fade-up:nth-child(2){animation-delay:.07s}.fade-up:nth-child(3){animation-delay:.14s}
  .fade-up:nth-child(4){animation-delay:.21s}.fade-up:nth-child(5){animation-delay:.28s}
  @keyframes count-up{from{opacity:0}to{opacity:1}} .count{animation:count-up .8s ease}
</style></head>"""

NAV_BACK = """<a href="index.html" class="inline-flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-6 transition-colors">
  <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
  חזרה לתיקים
</a>"""

# ─────────────────────────────────────────────
# INDEX page
# ─────────────────────────────────────────────
def build_index(portfolios_data, total, timestamp, all_history):
    cards = ""
    for i, p in enumerate(portfolios_data):
        m = PORTFOLIO_META[p['name']]
        pct = p['netReturnPct']
        color_cls = "text-emerald-400" if pct >= 0 else "text-red-400"
        badge_cls = "bg-emerald-500/15 text-emerald-400" if pct >= 0 else "bg-red-500/15 text-red-400"
        arrow = "▲" if pct >= 0 else "▼"

        # Sparkline data (portfolio-wide: sum of position values per day)
        spark_data = _portfolio_sparkline(p, all_history)
        spark_color = "#10b981" if pct >= 0 else "#f43f5e"
        spark_id = f"spark{i}"

        cards += f"""
<a href="{m['slug']}.html" class="glass rounded-2xl p-5 card-hover fade-up block">
  <div class="flex justify-between items-start mb-4">
    <div>
      <div class="text-2xl mb-1">{m['emoji']}</div>
      <h3 class="font-bold text-white text-base leading-tight">{p['name']}</h3>
      <p class="text-slate-500 text-xs">{p['nickname']}</p>
    </div>
    <span class="{badge_cls} text-xs font-bold px-3 py-1 rounded-full">{arrow} {abs(pct):.2f}%</span>
  </div>
  <p class="text-3xl font-extrabold count mb-1">{fmt_ils(p['totalValue'])}</p>
  <p class="{color_cls} text-sm font-semibold mb-4">{fmt_ils(p['netPnL'], sign=True)} נטו</p>
  <div style="height:44px"><canvas id="{spark_id}"></canvas></div>
</a>
<script>
(function(){{
  var d={json.dumps(spark_data)};
  new Chart(document.getElementById('{spark_id}'),{{
    type:'line',data:{{datasets:[{{data:d,borderColor:'{spark_color}',borderWidth:2,
    pointRadius:0,fill:true,backgroundColor:'{spark_color}22',tension:.4}}]}},
    options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{display:false}},y:{{display:false}}}},
    plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}}}}
  }});
}})();
</script>"""

    total_pct = total['netReturnPct']
    total_arrow = "▲" if total_pct >= 0 else "▼"
    total_cls = "text-emerald-400" if total_pct >= 0 else "text-red-400"

    return f"""<!DOCTYPE html><html lang="he" dir="rtl">
<title>BankOS — תיקי נועם 2026</title>{HEAD}
<body class="min-h-screen p-4 pb-24">
<header class="text-center pt-6 mb-8">
  <div class="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-4 py-1 text-xs text-emerald-400 mb-3">
    <span class="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>LIVE
  </div>
  <h1 class="text-3xl font-extrabold text-white tracking-tight">BankOS</h1>
  <p class="text-slate-500 text-sm">תיקי נועם · פברואר 2026 · עודכן {timestamp}</p>
</header>

<div class="glass rounded-3xl p-6 mb-8 text-center border-b-4 {'border-emerald-500' if total_pct>=0 else 'border-red-500'}">
  <p class="text-slate-400 text-sm mb-1">שווי כולל — נטו</p>
  <p class="text-5xl font-extrabold count">{fmt_ils(total['totalValue'])}</p>
  <p class="{total_cls} font-bold text-lg mt-2">{total_arrow} {fmt_ils(total['netPnL'],sign=True)} ({total_pct:+.2f}%)</p>
  <div class="flex justify-center gap-3 mt-4 text-xs text-slate-500">
    <span class="bg-slate-800/50 px-3 py-1 rounded-full">💸 עמלות {fmt_ils(total['fees'])}</span>
    <span class="bg-slate-800/50 px-3 py-1 rounded-full">🏛️ מס {fmt_ils(total['tax'])}</span>
  </div>
</div>

<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">{cards}</div>

<nav class="fixed bottom-0 inset-x-0 glass h-14 flex justify-around items-center border-t border-slate-700/40">
  <span class="text-blue-400 text-sm font-bold">📊 תיקים</span>
  <button onclick="location.reload()" class="text-slate-500 text-sm">🔄 רענן</button>
  <span class="text-slate-600 text-xs">{timestamp}</span>
</nav>
</body></html>"""

def _portfolio_sparkline(p, all_history):
    """Return list of daily total values for the portfolio (last 7 days)"""
    days = 7
    result = [0.0] * days
    for pos in p.get('_raw_positions', []):
        sym_orig = pos.get('symbol','')
        yahoo = _orig_to_yahoo(sym_orig)
        if not yahoo:
            continue
        hist = all_history.get(yahoo, [])
        if len(hist) == 0:
            # flat at current value
            val = pos.get('buyPrice', 0) * pos.get('shares', 0)
            for d in range(days):
                result[d] += val
        else:
            # Pad/trim to exactly 7 entries
            h = (hist[-days:] if len(hist) >= days else [hist[0]]*(days-len(hist)) + hist)
            for d, price in enumerate(h):
                result[d] += price * pos.get('shares', 0)
    # Add cash as flat
    cash = p.get('cash', 0)
    result = [round(v + cash, 0) for v in result]
    return result

def _orig_to_yahoo(sym):
    from tracker_unified import SYMBOL_MAP
    return SYMBOL_MAP.get(sym)

# ─────────────────────────────────────────────
# DEEP-DIVE page per portfolio
# ─────────────────────────────────────────────
def build_deep(portfolio_raw, portfolio_data, all_history, portfolio_json):
    name = portfolio_raw['name']
    m = PORTFOLIO_META[name]
    p = portfolio_data
    prices_now = fetch_all_prices()
    today = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Holdings rows
    rows_html = ""
    pie_labels, pie_vals, pie_colors = [], [], []
    PALETTE = ["#6366f1","#8b5cf6","#ec4899","#f43f5e","#f59e0b","#10b981","#0ea5e9","#a855f7","#d946ef","#f97316"]

    for i, pos in enumerate(portfolio_raw['positions']):
        sym = pos['symbol']
        if sym.startswith('BONDS:') or sym.startswith('LEVERAGE:') or sym.startswith('CRYPTO:') or 'DEFSMALL' in sym or 'REIT' in sym or 'POLI-PR' in sym:
            continue
        shares = pos.get('shares', 0)
        if shares == 0:
            continue
        buy_p  = pos.get('buyPrice', 0)
        cur_p  = prices_now.get(sym, buy_p)
        value  = shares * cur_p
        np_val = net_pnl(buy_p, cur_p, shares)
        np_pct = (np_val / (buy_p * shares) * 100) if buy_p > 0 else 0

        yahoo = _orig_to_yahoo(sym)
        hist  = all_history.get(yahoo, [])
        wk_pct = week_change_pct(hist)
        wk_str = f"{wk_pct:+.1f}%" if wk_pct is not None else "—"
        wk_cls = "text-emerald-400" if (wk_pct or 0) >= 0 else "text-red-400"

        pnl_cls = "text-emerald-400" if np_pct >= 0 else "text-red-400"
        short_sym = sym.split(":")[-1]

        rows_html += f"""
<tr class="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors">
  <td class="py-3 pr-3 font-bold text-sm text-white">{short_sym}</td>
  <td class="py-3 text-slate-400 text-sm">{shares:.1f}</td>
  <td class="py-3 text-slate-300 text-sm">{fmt_ils(cur_p)}</td>
  <td class="py-3 font-semibold text-sm">{fmt_ils(value)}</td>
  <td class="py-3 text-sm {pnl_cls} font-bold">{fmt_ils(np_val,sign=True)}<br><span class="text-xs">{np_pct:+.1f}%</span></td>
  <td class="py-3 text-sm {wk_cls} font-semibold">{wk_str}</td>
</tr>"""

        color = PALETTE[i % len(PALETTE)]
        pie_labels.append(short_sym)
        pie_vals.append(round(value))
        pie_colors.append(color)

    # Cash row in pie
    cash = portfolio_raw.get('cash', 0)
    if cash > 0:
        pie_labels.append("מזומן")
        pie_vals.append(round(cash))
        pie_colors.append("#475569")

    pct = p['netReturnPct']
    color_cls = "text-emerald-400" if pct >= 0 else "text-red-400"
    border_cls = "border-emerald-500" if pct >= 0 else "border-red-500"

    return f"""<!DOCTYPE html><html lang="he" dir="rtl">
<title>BankOS — {m['emoji']} {name}</title>{HEAD}
<body class="min-h-screen p-4 pb-24">
<div class="max-w-2xl mx-auto">
  {NAV_BACK}

  <!-- Hero -->
  <div class="glass rounded-3xl p-6 mb-6 text-center border-b-4 {border_cls}">
    <div class="text-5xl mb-2">{m['emoji']}</div>
    <h1 class="text-2xl font-extrabold text-white">{name}</h1>
    <p class="text-slate-400 text-sm mb-4">{p['nickname']}</p>
    <p class="text-5xl font-extrabold count">{fmt_ils(p['totalValue'])}</p>
    <p class="{color_cls} font-bold text-lg mt-1">{fmt_ils(p['netPnL'],sign=True)} נטו ({pct:+.2f}%)</p>
    <div class="flex justify-center gap-3 mt-4 text-xs text-slate-500">
      <span class="bg-slate-800/50 px-3 py-1 rounded-full">💸 {fmt_ils(p['fees'])}</span>
      <span class="bg-slate-800/50 px-3 py-1 rounded-full">🏛️ {fmt_ils(p['tax'])}</span>
      <span class="bg-slate-800/50 px-3 py-1 rounded-full">מזומן {fmt_ils(cash)}</span>
    </div>
  </div>

  <!-- Asset Allocation -->
  <div class="glass rounded-2xl p-5 mb-6">
    <h2 class="font-bold text-slate-200 mb-4 text-base">Asset Allocation</h2>
    <div class="flex items-center justify-center" style="height:220px">
      <canvas id="pieChart"></canvas>
    </div>
  </div>

  <!-- Holdings Table -->
  <div class="glass rounded-2xl p-5 mb-6 overflow-x-auto">
    <h2 class="font-bold text-slate-200 mb-4 text-base">Holdings</h2>
    <table class="w-full text-right min-w-[460px]">
      <thead><tr class="text-slate-500 text-xs border-b border-slate-700/50">
        <th class="pb-2 pr-3">סימבול</th><th class="pb-2">יחידות</th>
        <th class="pb-2">מחיר</th><th class="pb-2">שווי</th>
        <th class="pb-2">P/L נטו</th><th class="pb-2">1W</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>

  <p class="text-center text-xs text-slate-600 mb-8">עודכן {today} · 25 מניות · net after 25% tax + 0.2% fees</p>
</div>

<nav class="fixed bottom-0 inset-x-0 glass h-14 flex justify-around items-center border-t border-slate-700/40">
  <a href="index.html" class="text-slate-500 text-sm">◀ ראשי</a>
  <span class="text-white text-sm font-bold">{m['emoji']} {name}</span>
  <button onclick="location.reload()" class="text-slate-500 text-sm">🔄</button>
</nav>

<script>
new Chart(document.getElementById('pieChart'),{{
  type:'doughnut',
  data:{{
    labels:{json.dumps(pie_labels, ensure_ascii=False)},
    datasets:[{{data:{json.dumps(pie_vals)},backgroundColor:{json.dumps(pie_colors)},borderWidth:0,hoverOffset:8}}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'60%',
    plugins:{{legend:{{display:true,position:'bottom',labels:{{color:'#94a3b8',font:{{size:11,family:'Assistant'}},padding:12}}}},
    tooltip:{{callbacks:{{label:c=>'₪'+c.parsed.toLocaleString()}}}}}}
  }}
}});
</script>
</body></html>"""

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print(f"\n{'='*64}")
    print(f"🚀 BankOS Full Generator — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*64}\n")

    # 1. Fetch data
    print("📡 Fetching portfolio data…")
    data = get_portfolio_data()
    print(f"✅ {data['pricesCount']} prices fetched")

    # 2. Load raw portfolios for deep-dive pages
    raw_json = Path(__file__).parent.parent / "investment-learning" / "portfolios-5way.json"
    raw_data = json.loads(raw_json.read_text(encoding='utf-8'))

    # Attach raw positions to performance dicts
    raw_by_name = {p['name']: p for p in raw_data['portfolios']}
    for p in data['portfolios']:
        p['_raw_positions'] = raw_by_name[p['name']]['positions']

    # 3. Fetch 1W history
    print("📈 Fetching 7-day history…")
    all_yahoo = list(set(v for v in SYMBOL_MAP.values() if v))
    all_history = fetch_weekly_history(all_yahoo)
    print(f"✅ History for {sum(1 for h in all_history.values() if h)} symbols")

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

    # 4. Build index
    print("🎨 Building index.html…")
    index_html = build_index(data['portfolios'], data['total'], timestamp, all_history)
    (OUT_DIR / "index.html").write_text(index_html, encoding='utf-8')
    print(f"   ✅ index.html ({len(index_html):,} bytes)")

    # 5. Build deep-dive pages
    for p_perf in data['portfolios']:
        name = p_perf['name']
        m = PORTFOLIO_META[name]
        print(f"🎨 Building {m['slug']}.html…")
        raw_p = raw_by_name[name]
        deep_html = build_deep(raw_p, p_perf, all_history, raw_json)
        (OUT_DIR / f"{m['slug']}.html").write_text(deep_html, encoding='utf-8')
        print(f"   ✅ {m['slug']}.html ({len(deep_html):,} bytes)")

    # 6. Git push
    print("\n📤 Pushing to GitHub…")
    for cmd in [
        ["git", "-C", str(OUT_DIR), "add", "-A"],
        ["git", "-C", str(OUT_DIR), "commit", "-m",
         f"Live Update {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
        ["git", "-C", str(OUT_DIR), "push"],
    ]:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if "nothing to commit" in r.stdout:
            print("   ⏭️  Nothing changed")
            break
        if r.returncode != 0 and "nothing to commit" not in r.stderr:
            print(f"   ⚠️  {r.stderr[:120]}")

    print("   ✅ Pushed!")
    print(f"\n🌐 Live: https://noamm-opencalw.github.io/investment-dashboard/")
    print(f"{'='*64}\n")

if __name__ == "__main__":
    main()
