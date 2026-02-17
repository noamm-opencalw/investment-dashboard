#!/usr/bin/env python3
"""
BankOS — Full Dashboard Generator v4
Senior FinTech Product Designer Protocol:
  1. Whitespace  2. 3-Level Typography  3. Functional Color
  4. Glassmorphism  5. Affordance  6. Progressive Disclosure (Rule of 5)
  7. Net-Only Principle
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
    "SOLID":            {"slug":"turtle", "emoji":"🐢","heb":"שמרני"},
    "AGGRESSIVE":       {"slug":"lion",   "emoji":"🦁","heb":"אגרסיבי"},
    "SUPER-AGGRESSIVE": {"slug":"rocket", "emoji":"🚀","heb":"סופר-אגרסיבי"},
    "SPECULATIVE":      {"slug":"target", "emoji":"🎯","heb":"ספקולטיבי"},
    "CREATIVE":         {"slug":"canvas", "emoji":"🎨","heb":"קריאטיבי"},
}

SECTORS = {
    "TLV:POLI":"בנקאות","TLV:LUMI":"בנקאות","TLV:HAPO":"בנקאות","TLV:MZTF":"בנקאות","TLV:IGLD":"בנקאות",
    "TLV:PHOE":"ביטוח","TLV:HARL":"ביטוח","TLV:MELN":"ביטוח",
    "TLV:ESLT":"ביטחון","TLV:ELTA":"ביטחון",
    "TLV:ELEC":"אנרגיה","TLV:NWMD":"אנרגיה","TLV:LPLI":"אנרגיה",
    "TLV:NXSN":"טכנולוגיה","TLV:ARYT":"טכנולוגיה","TLV:MTDS":"טכנולוגיה",
    "TLV:BIGA":"נדל\"ן","TLV:AMOT":"נדל\"ן","TLV:ISCN":"נדל\"ן",
    "TLV:MORE":"קמעונאות","TLV:BIG":"קמעונאות","TLV:SPEN":"קמעונאות",
    "TLV:FTAL":"תיירות","TLV:SAE":"תיירות",
}

SKIP = ("BONDS:","LEVERAGE:","CRYPTO:","TLV:DEFSMALL","TLV:REIT","TLV:POLI-PR")

# ─── עברית פשוטה למה הנכס נבחר ────────────────────────────────────────────────
THESIS_HEB = {
    # SOLID
    "TLV:POLI":  "הבנק הגדול בישראל — יציב, מחלק דיבידנד, לא מפתיע אבל לא ירד",
    "TLV:LUMI":  "בנק לאומי — עבר לדיגיטל מהר מהמתחרים. שווי שוק חצה 100 מיליארד",
    "TLV:ELEC":  "חברת חשמל — מונופול ממשלתי. כל בית בישראל משלם להם. דיבידנד יציב",
    "TLV:BEZQ":  "בזק — תשתית תקשורת בלתי נמנעת. מחלקת 7%+ דיבידנד בשנה",
    "TLV:HARL":  "חראל ביטוח — עלה 151% ב-2025. נשמר גם כאן כ'עוגן' בטיח",
    "ETF:GOLD":  "זהב — ריפוד אם הכל ירד. לא מרוויחים ממנו, אבל מגן מפני הפתעות",
    # AGGRESSIVE
    "TLV:PHOE":  "פניקס — מוביל הביטוח בישראל. עלה 165% ב-2025 כי משקיעים זרים גילו אותו",
    "TLV:ESLT":  "אלביט — ביקוש עולמי לנשק הישראלי. תורים ארוכים, רווחים עולים. מחיר גבוה — סיכון",
    "TLV:DEDRL": "ניומד אנרגיה — גז ישראלי. מגזר האנרגיה עלה 77% ב-2025, עדיין מפגר מול ביטוח",
    "TLV:NXTV":  "נקסטוויזן — מצלמות ייצוב לרחפנים. עלה 253% ב-2025. קיבלה עסקה של 77 מיליון דולר",
    "TLV:NWMD":  "ניומד — חיפוש גז בים התיכון. ספין-אוף של דלק, פוטנציאל ייצוא לאירופה",
    "TLV:TRPZ":  "טרפז אנרגיה — עלה 238% ב-2025, אחד הכוכבים של ת\"א 90",
    "NASDAQ:QQQ":"נאסד\"ק 100 — חשיפה לטכנולוגיה האמריקאית (אפל, מיקרוסופט, אנבידיה). גם מגן מטבע",
    # SUPER-AGGRESSIVE
    "TLV:ARYT":  "ארייט — יצרן פיוזים וחומרי נפץ. עלה 408% ב-2025. מאז 7/10 — 2,212%(!)",
    "TLV:MORE":  "מור — בית השקעות. עלה 302% ב-2025. מנהל כסף של כולם ורוצה יותר",
    "TLV:MTDS":  "מיתדס — בנקאות השקעות. עלה 293% ב-2025. מובל על ידי שוק הון פועם",
    "TLV:RATI":  "ג'נרג'י — חיפוש גז, סיכון גבוה. אם ימצאו → קפיצה. אם לא → ירידה",
    "TLV:ENOG":  "אנוג'י — גז ים תיכוני, ישראל. פוטנציאל ייצוא לאירופה אחרי המלחמה",
    # SPECULATIVE
    "TLV:FTHL":  "פאתאל מלונות — הפסקת האש = תיירות חוזרת. קנה עכשיו, מכור כשהשגרירות תיפתח מחדש",
    # CREATIVE
    "TLV:AZRG":  "אזריאלי — נדל\"ן עלה רק 24% ב-2025 כשהשוק עלה 51%. כשהריבית תרד → קפיצה",
    "TLV:BIG":   "ביג קניונים — שנואים אחרי המלחמה, אבל מבקרים חוזרים. מחיר זול",
    "TLV:SHFR":  "שופרסל — סופרמרקט. סקטור הצריכה ירד 41.7% ב-2025. אנשים חייבים לאכול",
    "NASDAQ:TEVA":"תבע — בין ת\"א לנאסד\"ק. כולם שונאים, אבל אולי זול מדי? פארמה ג'נרית = דיבידנד",
    "NASDAQ:CHKP":"צ'ק פוינט — אבטחת סייבר. כולם שונאים טק ישראלי. אנליסטים הורידו — אבל אולי בדיוק לכן?",
}

def get_thesis(sym: str, pos: dict) -> str:
    """Return Hebrew thesis, fallback to English original."""
    return THESIS_HEB.get(sym) or pos.get("thesis") or "—"

# ─── SVG Icons ────────────────────────────────────────────────────────────────
def svg(name, cls="w-4 h-4 inline-block"):
    d = {
        "percent":    "M9 9h.01M15 15h.01M9 6a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm10 6a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm-12.5 6l10-10",
        "wallet":     "M3 9h18V7a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4H3m14 2h.01",
        "trend-up":   "M23 6 13.5 15.5 8.5 10.5 1 18M17 6h6v6",
        "arrow-left": "M19 12H5M12 5l-7 7 7 7",
        "refresh":    "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15",
        "chevron":    "M9 18l6-6-6-6",
        "calendar":   "M3 4h18v18H3zM16 2v4M8 2v4M3 10h18",
        "info":       "M12 8v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z",
    }
    return f'<svg class="{cls}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="{d.get(name,"")}"/></svg>'

# ─── Finance ──────────────────────────────────────────────────────────────────
def net_withdrawal(gross: float, cost_basis: float) -> float:
    """After 0.1% sell fee + 25% CGT on gains only."""
    gain = gross - cost_basis
    return gross - gross * 0.001 - max(0.0, gain) * 0.25

def days_left():
    return max(0, (EXPERIMENT_END - date.today()).days)

def week_chg(hist):
    if len(hist) >= 2 and hist[0] > 0:
        return round((hist[-1]/hist[0]-1)*100, 2)
    return None

# ─── History ──────────────────────────────────────────────────────────────────
def fetch_history():
    try:
        import yfinance as yf
        out = {}
        for sym in set(v for v in SYMBOL_MAP.values() if v):
            try:
                h = yf.Ticker(sym).history(period="7d",interval="1d")
                if h.empty: out[sym]=[]; continue
                p=[round(float(v),4) for v in h["Close"].tolist()]
                if sym.endswith(".TA") and p and p[0]>500: p=[round(x/100,4) for x in p]
                out[sym]=p
            except: out[sym]=[]
        return out
    except: return {}

def sparkline(raw_p, hist, days=7):
    tots=[0.0]*days
    for pos in raw_p["positions"]:
        sym=pos["symbol"]
        if any(sym.startswith(s) for s in SKIP): continue
        sh=pos.get("shares",0)
        if not sh: continue
        y=SYMBOL_MAP.get(sym)
        h=hist.get(y,[]) if y else []
        if not h:
            v=pos.get("buyPrice",0)*sh
            for d in range(days): tots[d]+=v
        else:
            hh=h[-days:] if len(h)>=days else [h[0]]*(days-len(h))+h
            for d,price in enumerate(hh): tots[d]+=price*sh
    c=raw_p.get("cash",0)
    return [round(v+c) for v in tots]

# ─── Shared CSS (implements all 7 principles) ─────────────────────────────────
SHARED_CSS = """
  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  body{font-family:'Assistant',sans-serif;background:#0a0f1e;color:#e2e8f0;
       -webkit-font-smoothing:antialiased;min-height:100vh}

  /* Principle 4 — Glassmorphism */
  .base{background:#0a0f1e}
  .glass{background:rgba(255,255,255,.04);backdrop-filter:blur(16px);
         -webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.08)}
  .glass-deep{background:rgba(255,255,255,.02);backdrop-filter:blur(10px);
              border:1px solid rgba(255,255,255,.06)}

  /* Principle 5 — Affordance */
  .tappable{transition:transform .2s cubic-bezier(.34,1.56,.64,1),box-shadow .2s;
            cursor:pointer;-webkit-user-select:none;user-select:none}
  .tappable:hover{transform:scale(1.02);box-shadow:0 20px 60px rgba(0,0,0,.5)}
  .tappable:active{transform:scale(.97)}

  /* Principle 1 — Whitespace */
  .section{padding:1.5rem}

  /* Principle 2 — Typography scale */
  .l1{font-size:2.8rem;font-weight:800;line-height:1;letter-spacing:-.03em;color:#fff}
  .l1-lg{font-size:3.5rem;font-weight:800;line-height:1;letter-spacing:-.04em;color:#fff}
  .l2{font-size:.85rem;color:#94a3b8;font-weight:500}
  .l3{font-size:.72rem;color:#475569;font-style:italic}

  /* Principle 3 — Status colors only */
  .pos{color:#34d399}  /* emerald-400 */
  .neg{color:#fb7185}  /* rose-400 */
  .pos-bg{background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.2)}
  .neg-bg{background:rgba(251,113,133,.1);border:1px solid rgba(251,113,133,.2)}
  .pos-border{border-right:3px solid #34d399}
  .neg-border{border-right:3px solid #fb7185}

  /* Animations */
  @keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
  .rise{animation:rise .35s ease both}
  .rise:nth-child(1){animation-delay:0s}  .rise:nth-child(2){animation-delay:.05s}
  .rise:nth-child(3){animation-delay:.1s} .rise:nth-child(4){animation-delay:.15s}
  .rise:nth-child(5){animation-delay:.2s}

  /* Thesis panel */
  .thesis{display:none;background:rgba(0,0,0,.3)}
  .thesis.open{display:block}

  /* iPhone 17 Pro — Safe areas & fluid type */
  body{padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}
  .l1{font-size:clamp(2rem,8vw,3rem);font-weight:800;line-height:1;letter-spacing:-.04em;color:#fff}
  .l1-lg{font-size:clamp(2.4rem,10vw,3.5rem);font-weight:800;line-height:1;letter-spacing:-.05em;color:#fff}
  /* Tap targets — Apple HIG 44pt min */
  .tappable{min-height:44px}
  /* Momentum scroll */
  .scroll-x{overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
  .scroll-x::-webkit-scrollbar{display:none}
"""

def doc_head(title):
    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,minimum-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#080d1a">
<title>{title}</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>{SHARED_CSS}</style>
</head>"""

# ─── INDEX PAGE ───────────────────────────────────────────────────────────────
def build_index(portfolios, total, history, raw_by_name):
    now  = datetime.now()
    ts   = now.strftime("%d/%m/%Y %H:%M")
    dl   = days_left()

    base  = 500_000
    gross = total["totalValue"]
    nw    = net_withdrawal(gross, base)
    gain  = gross - base
    pct   = gain / base * 100
    glyph = "▲" if gain>=0 else "▼"
    vcls  = "pos" if gain>=0 else "neg"
    bcls  = "pos-border" if gain>=0 else "neg-border"

    # Rank
    ranked = sorted(portfolios, key=lambda p: p["totalValue"], reverse=True)
    rank   = {p["name"]: i+1 for i,p in enumerate(ranked)}

    cards = ""
    for i, p in enumerate(portfolios):
        m     = PORTFOLIO_META[p["name"]]
        raw   = raw_by_name[p["name"]]
        pg    = p["totalValue"]
        pnw   = net_withdrawal(pg, 100_000)
        pgain = pg - 100_000
        ppct  = pgain / 100_000 * 100
        pglyph= "▲" if pgain>=0 else "▼"
        pv    = "pos" if pgain>=0 else "neg"
        pb    = "pos-border" if pgain>=0 else "neg-border"
        pbg   = "pos-bg" if pgain>=0 else "neg-bg"
        sc    = "#34d399" if pgain>=0 else "#fb7185"
        sid   = f"s{i}"
        sp    = sparkline(raw, history)
        rk    = rank[p["name"]]
        medal = ("🥇" if rk==1 else "🥈" if rk==2 else "🥉" if rk==3 else f"#{rk}")

        cards += f"""
<a href="{m['slug']}.html" class="glass rounded-2xl tappable rise block no-underline {pb}" style="padding:1.4rem">
  <div class="flex justify-between items-start mb-5">
    <div class="flex items-center gap-3">
      <span style="font-size:1.6rem;line-height:1">{m['emoji']}</span>
      <div>
        <div style="font-size:.95rem;font-weight:700;color:#fff;line-height:1.2">{p['name']}</div>
        <div class="l3">{m['heb']} · {medal}</div>
      </div>
    </div>
    <span class="l3 {pbg}" style="padding:3px 10px;border-radius:999px;font-style:normal;font-weight:700;font-size:.75rem">
      {pglyph} {abs(ppct):.2f}%
    </span>
  </div>

  <!-- L1: Net value = THE number -->
  <div style="margin-bottom:.25rem">
    <div class="l1" style="font-size:2.2rem">₪{pnw:,.0f}</div>
    <div class="l2" style="margin-top:.2rem">לאחר מס ועמלה</div>
  </div>

  <!-- L2: Gross as secondary -->
  <div class="l3" style="margin-top:.3rem;margin-bottom:1rem">
    שווי שוק: ₪{pg:,.0f}
    &nbsp;·&nbsp;
    <span class="{pv}">{pglyph} ₪{abs(pgain):,.0f}</span> מ-Day&nbsp;0
  </div>

  <!-- Sparkline -->
  <div style="height:30px"><canvas id="{sid}"></canvas></div>
</a>
<script>(function(){{
  new Chart(document.getElementById('{sid}'),{{
    type:'line',
    data:{{datasets:[{{data:{json.dumps(sp)},borderColor:'{sc}',borderWidth:1.5,
      pointRadius:0,fill:true,backgroundColor:'{sc}12',tension:.4}}]}},
    options:{{responsive:true,maintainAspectRatio:false,animation:false,
      scales:{{x:{{display:false}},y:{{display:false}}}},
      plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}}}}
  }});
}})();</script>"""

    # Rule of 5: exactly 5 critical numbers on index
    # 1. Total net withdrawal  2. Total gross  3. Gain amount  4. Gain %  5. Days left
    return f"""{doc_head('BankOS — תיקי נועם 2026')}
<body style="padding-bottom:5rem">

<div style="max-width:520px;margin:0 auto;padding:1.5rem 1rem">

  <!-- L3 header strip -->
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.8rem;padding-top:.5rem">
    <div style="display:flex;align-items:center;gap:.5rem">
      <span style="width:7px;height:7px;background:#34d399;border-radius:50%;display:inline-block;animation:pulse 2s infinite"></span>
      <span class="l3" style="font-style:normal;letter-spacing:.06em;font-weight:600;color:#34d399">LIVE</span>
    </div>
    <div class="l3">{svg('calendar','w-3 h-3 inline-block mr-1 align-middle')}{dl} ימים · 19.3.2026</div>
  </div>

  <!-- Hero — 5 critical numbers ONLY (Principle 6) -->
  <div class="glass {bcls}" style="padding:1.8rem;margin-bottom:1.5rem;border-radius:1.2rem">
    <div class="l2" style="margin-bottom:.6rem">יהיה בחשבונך אם תמכור הכל היום</div>
    <div class="l1-lg" style="margin-bottom:.3rem">₪{nw:,.0f}</div>  <!-- [1] Net -->
    <div class="l3" style="margin-bottom:1.2rem">שווי שוק: ₪{gross:,.0f}</div>  <!-- [2] Gross -->

    <div class="flex items-center gap-3 flex-wrap">
      <span class="{vcls}" style="font-size:1.1rem;font-weight:700">  <!-- [3] Gain -->
        {glyph} ₪{abs(gain):,.0f}
      </span>
      <span class="{vcls} {pbg if gain>=0 else 'neg-bg'}" style="padding:2px 10px;border-radius:999px;font-weight:700;font-size:.85rem">  <!-- [4] % -->
        {glyph} {abs(pct):.2f}%
      </span>
      <span class="l3">{dl} ימים לסיום</span>  <!-- [5] Days -->
    </div>

    <div style="border-top:1px solid rgba(255,255,255,.06);margin-top:1rem;padding-top:.8rem">
      <div class="l3">
        {svg('percent','w-3 h-3 inline-block align-middle mr-1')} עמלות ₪{total['fees']:,.0f}
        &nbsp;&nbsp;
        {svg('trend-up','w-3 h-3 inline-block align-middle mr-1')} מס ₪{total['tax']:,.0f}
        &nbsp;&nbsp;
        {svg('wallet','w-3 h-3 inline-block align-middle mr-1')} בסיס ₪500K
      </div>
    </div>
  </div>

  <!-- Portfolio cards -->
  <div style="display:flex;flex-direction:column;gap:.75rem">
    {cards}
  </div>

  <!-- Legend box -->
  <div class="glass-deep" style="margin-top:1.2rem;padding:1rem 1.2rem;border-radius:1rem">
    <div class="l3" style="line-height:1.9;color:#64748b">
      {svg('info','w-3 h-3 inline-block align-middle mr-1')}
      <strong style="color:#94a3b8">₪X,XXX (נטו)</strong> = מה ייכנס לחשבון לאחר מכירה ·
      מס 25% <em>על רווח בלבד</em> · עמלת מכירה 0.1% · ביום 0: הפרש של ₪100 בלבד
    </div>
  </div>

  <div class="l3" style="text-align:center;margin-top:1rem">עודכן {ts}</div>
</div>

<!-- Bottom nav -->
<nav class="glass" style="position:fixed;bottom:0;left:0;right:0;height:3.5rem;
  display:flex;justify-content:space-between;align-items:center;padding:0 1.5rem;
  border-top:1px solid rgba(255,255,255,.06)">
  <span style="color:#fff;font-weight:700;font-size:.9rem">📊 BankOS</span>
  <button onclick="location.reload()" class="l2 tappable" style="display:flex;align-items:center;gap:.4rem;padding:.4rem .8rem;border-radius:.5rem">
    {svg('refresh','w-4 h-4')} רענן
  </button>
</nav>

<style>@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}</style>
</body></html>"""


# ─── DEEP-DIVE PAGE ───────────────────────────────────────────────────────────
def build_deep(raw_p, perf, history):
    name  = raw_p["name"]
    m     = PORTFOLIO_META[name]
    now   = datetime.now().strftime("%d/%m/%Y %H:%M")
    dl    = days_left()
    prices= fetch_all_prices()
    cash  = raw_p.get("cash", 0)

    pg    = perf["totalValue"]
    pnw   = net_withdrawal(pg, 100_000)
    pgain = pg - 100_000
    ppct  = pgain / 100_000 * 100
    glyph = "▲" if pgain>=0 else "▼"
    vc    = "pos" if pgain>=0 else "neg"
    bc    = "pos-border" if pgain>=0 else "neg-border"
    vbg   = "pos-bg" if pgain>=0 else "neg-bg"

    # Holdings as mobile cards (Principle 6 — no wide table on mobile)
    cards_html = ""
    pie_l, pie_v, pie_c = [], [], []
    sec_totals = {}
    PAL = ["#6366f1","#8b5cf6","#ec4899","#f43f5e","#f59e0b",
           "#10b981","#0ea5e9","#a855f7","#f97316","#14b8a6","#d946ef","#84cc16"]

    best  = ("", -999.0)
    worst = ("", 999.0)
    idx   = 0

    for pos in raw_p["positions"]:
        sym = pos["symbol"]
        if any(sym.startswith(s) for s in SKIP): continue
        sh  = pos.get("shares", 0)
        if not sh: continue

        bp  = pos.get("buyPrice", 0)
        cp  = prices.get(sym, bp)
        val = sh * cp
        g   = (cp - bp) * sh
        nv  = g - val*0.001 - max(0,g)*0.25
        npct= (nv/(bp*sh)*100) if bp*sh>0 else 0

        yh   = SYMBOL_MAP.get(sym)
        hist = history.get(yh,[]) if yh else []
        wkp  = week_chg(hist)
        wks  = f"{wkp:+.1f}%" if wkp is not None else "—"
        wvc  = "pos" if (wkp or 0)>=0 else "neg"
        nvc  = "pos" if npct>=0 else "neg"

        sector  = SECTORS.get(sym, "אחר")
        thesis  = get_thesis(sym, pos)
        short   = sym.split(":")[-1].replace(".TA","")
        tid     = f"t{idx}"

        if wkp is not None:
            if wkp > best[1]:  best  = (short, wkp)
            if wkp < worst[1]: worst = (short, wkp)

        sec_totals[sector] = sec_totals.get(sector,0) + val

        # FIX: Day 0 — all stocks show -0.1% (buy fee). Show "Day 0" badge instead of misleading red
        is_day0  = abs(npct) < 0.15 and abs(npct) > 0
        badge_txt = "Day 0" if is_day0 else f"{npct:+.1f}%"
        pnl_color = "#94a3b8" if is_day0 else ("#34d399" if npct >= 0 else "#fb7185")
        pnl_bg    = "rgba(148,163,184,.08)" if is_day0 else ("rgba(52,211,153,.1)" if npct>=0 else "rgba(251,113,133,.1)")
        pnl_bdr   = "rgba(148,163,184,.2)" if is_day0 else ("rgba(52,211,153,.25)" if npct>=0 else "rgba(251,113,133,.25)")
        wk_color  = "#34d399" if (wkp or 0) >= 0 else "#fb7185"
        border_l  = "#334155" if is_day0 else ("#34d399" if npct >= 0 else "#fb7185")

        # FIX: RTL+numbers — wrap all numeric values in dir=ltr spans
        cards_html += f"""
<div class="tappable" onclick="var t=document.getElementById('{tid}');t.classList.toggle('open')"
  style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
         border-right:3px solid {border_l};border-radius:1rem;
         padding:1.2rem 1.3rem 1rem;margin-bottom:.65rem">

  <!-- Row 1: Name + badge -->
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.6rem">
    <div>
      <span style="font-weight:800;color:#f1f5f9;font-size:1rem">{short}</span>
      <span style="font-size:.72rem;color:#475569;margin-right:.4rem"> · {sector}</span>
    </div>
    <span dir="ltr" style="font-size:.76rem;font-weight:700;color:{pnl_color};
      background:{pnl_bg};border:1px solid {pnl_bdr};
      padding:2px 10px;border-radius:999px;white-space:nowrap">{badge_txt}</span>
  </div>

  <!-- Row 2: Value (L1) + week change -->
  <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.35rem">
    <span style="font-size:1.2rem;font-weight:700;color:#fff" dir="ltr">₪{val:,.0f}</span>
    <div style="text-align:left">
      <span style="font-size:.73rem;color:#475569">שבוע </span>
      <span dir="ltr" style="font-size:.82rem;font-weight:600;color:{wk_color}">{wks}</span>
    </div>
  </div>

  <!-- Row 3: Meta (L3) — each label+number in own span, direction per segment -->
  <div style="display:flex;justify-content:space-between;margin-top:.4rem;padding-top:.3rem;border-top:1px solid rgba(255,255,255,.04)">
    <div>
      <span style="font-size:.68rem;color:#475569">יח' </span>
      <span dir="ltr" style="font-size:.7rem;color:#94a3b8;font-variant-numeric:tabular-nums">{sh:.0f}</span>
    </div>
    <div>
      <span style="font-size:.68rem;color:#475569">מחיר </span>
      <span dir="ltr" style="font-size:.7rem;color:#94a3b8">₪{cp:,.1f}</span>
    </div>
    <div>
      <span style="font-size:.68rem;color:#475569">נטו </span>
      <span dir="ltr" style="font-size:.7rem;color:{pnl_color}">₪{nv:+,.0f}</span>
    </div>
  </div>

  <!-- Thesis — expandable, hidden by default -->
  <div id="{tid}" class="thesis" style="margin-top:.85rem;padding:.8rem;
       background:rgba(0,0,0,.3);border-radius:.65rem;border:1px solid rgba(99,102,241,.2)">
    <div style="font-size:.68rem;color:#6366f1;font-weight:700;letter-spacing:.05em;margin-bottom:.3rem">📌 למה נבחר</div>
    <div style="font-size:.82rem;color:#94a3b8;line-height:1.7">{thesis}</div>
  </div>
</div>"""

        c = PAL[idx%len(PAL)]
        pie_l.append(short); pie_v.append(round(val)); pie_c.append(c)
        idx += 1

    if cash > 0:
        sec_totals["מזומן"] = cash
        pie_l.append("מזומן"); pie_v.append(round(cash)); pie_c.append("#334155")

    sl = list(sec_totals.keys())
    sv = [round(v) for v in sec_totals.values()]
    sc = ["#6366f1","#8b5cf6","#ec4899","#f43f5e","#f59e0b","#10b981","#0ea5e9","#334155"]

    # Bar Chart Rule — computed BEFORE f-string (no escaping needed)
    def _chart_html(cid, lid, labels, use_donut):
        if use_donut:
            return (f'<div class="glass-deep" style="padding:1.1rem 1.2rem;border-radius:1rem;margin-bottom:.7rem">'
                    f'<div style="font-size:.7rem;font-weight:600;color:#64748b;letter-spacing:.04em;margin-bottom:.8rem">'
                    f'{"פיזור נכסים" if cid=="c1" else "פיזור סקטורים"}</div>'
                    f'<div style="display:grid;grid-template-columns:140px 1fr;gap:1rem;align-items:center">'
                    f'<div style="height:140px"><canvas id="{cid}"></canvas></div>'
                    f'<div id="{lid}" style="display:flex;flex-direction:column;gap:.4rem"></div>'
                    f'</div></div>')
        else:
            h = max(120, len(labels) * 26)
            return (f'<div class="glass-deep" style="padding:1.1rem 1.2rem;border-radius:1rem;margin-bottom:.7rem">'
                    f'<div style="font-size:.7rem;font-weight:600;color:#64748b;letter-spacing:.04em;margin-bottom:.8rem">'
                    f'{"פיזור נכסים" if cid=="c1" else "פיזור סקטורים"}</div>'
                    f'<div style="height:{h}px"><canvas id="{cid}"></canvas></div>'
                    f'</div>')

    _chart_html_c1 = _chart_html("c1", "leg1", pie_l, len(pie_l) <= 5)
    _chart_html_c2 = _chart_html("c2", "leg2", sl, len(sl) <= 5)

    bw_html = ""
    if best[0] and worst[0] and best[0] != worst[0]:
        bw_html = f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:.6rem;margin-bottom:1.2rem">
  <div class="glass-deep pos-border" style="padding:.9rem 1rem;border-radius:.9rem;min-height:70px">
    <div style="font-size:.68rem;color:#475569;margin-bottom:.3rem">🏆 הכי חזק השבוע</div>
    <div style="font-weight:700;color:#fff;font-size:.95rem">{best[0]}</div>
    <div dir="ltr" class="pos" style="font-weight:700;font-size:.85rem;margin-top:.15rem">{best[1]:+.1f}%</div>
  </div>
  <div class="glass-deep neg-border" style="padding:.9rem 1rem;border-radius:.9rem;min-height:70px">
    <div style="font-size:.68rem;color:#475569;margin-bottom:.3rem">📉 הכי חלש השבוע</div>
    <div style="font-weight:700;color:#fff;font-size:.95rem">{worst[0]}</div>
    <div dir="ltr" class="neg" style="font-weight:700;font-size:.85rem;margin-top:.15rem">{worst[1]:+.1f}%</div>
  </div>
</div>"""

    return f"""{doc_head(f'BankOS — {m["emoji"]} {name}')}
<body style="padding-bottom:1rem"><!-- sticky nav is in-flow, no padding needed -->
<div style="max-width:520px;margin:0 auto;padding:1rem">

  <!-- Back -->
  <div style="padding:.8rem 0 1rem">
    <a href="index.html" class="tappable" style="display:inline-flex;align-items:center;gap:.4rem;color:#64748b;text-decoration:none;font-size:.85rem;padding:.3rem .5rem;border-radius:.4rem">
      {svg('arrow-left','w-4 h-4')} חזרה
    </a>
  </div>

  <!-- Hero (Rule of 5: net, gross, gain₪, gain%, days) -->
  <div class="glass {bc}" style="padding:1.6rem;border-radius:1.2rem;margin-bottom:1.2rem">
    <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1.2rem">
      <span style="font-size:2.5rem;line-height:1">{m['emoji']}</span>
      <div>
        <div style="font-weight:800;color:#fff;font-size:1.1rem">{name}</div>
        <div class="l3">{m['heb']} · {dl} ימים לסיום</div>
      </div>
    </div>

    <div class="l2" style="margin-bottom:.3rem">יהיה בחשבונך אם תמכור הכל היום</div>
    <div class="l1" style="margin-bottom:.2rem">₪{pnw:,.0f}</div>
    <div class="l3" style="margin-bottom:.9rem">שווי שוק: ₪{pg:,.0f}</div>

    <div style="display:flex;align-items:center;gap:.7rem;flex-wrap:wrap">
      <!-- FIX: Day 0 hero — show neutral badge, not false red -->
      {f'<span dir="ltr" class="{vc}" style="font-weight:700;font-size:1.05rem">{glyph} ₪{abs(pgain):,.0f}</span><span dir="ltr" class="{vc} {vbg}" style="padding:3px 10px;border-radius:999px;font-weight:700;font-size:.78rem">{glyph} {abs(ppct):.2f}%</span>' if abs(pgain) > 150 else '<span style="font-size:.82rem;color:#64748b;background:rgba(148,163,184,.08);border:1px solid rgba(148,163,184,.15);padding:3px 12px;border-radius:999px">Day 0 · Baseline</span>'}
    </div>

    <div style="border-top:1px solid rgba(255,255,255,.06);margin-top:1rem;padding-top:.7rem">
      <div class="l3">
        {svg('percent','w-3 h-3 inline-block align-middle')} ₪{perf['fees']:,.0f}
        &nbsp; {svg('trend-up','w-3 h-3 inline-block align-middle')} ₪{perf['tax']:,.0f}
        &nbsp; {svg('wallet','w-3 h-3 inline-block align-middle')} מזומן ₪{cash:,.0f}
      </div>
    </div>
  </div>

  {bw_html}

  <!-- Charts: Bar Chart Rule (computed before f-string) -->
  {_chart_html_c1}
  {_chart_html_c2}

  <!-- Holdings cards (mobile-first, no table) -->
  <div class="l3" style="margin-bottom:.7rem;font-style:normal;font-weight:600;color:#64748b;padding-right:.2rem">
    {svg('info','w-3 h-3 inline-block align-middle mr-1')}אחזקות · לחץ להרחבה
  </div>
  {cards_html}

  <div class="l3" style="text-align:center;margin-top:1rem">עודכן {now}</div>
</div>

<!-- FIX #5: no bottom nav on detail pages — back button is already at top -->
<div style="display:flex;justify-content:center;gap:1.5rem;padding:1.5rem 0 2rem">
  <a href="index.html" class="tappable" style="display:inline-flex;align-items:center;gap:.4rem;
     background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
     color:#94a3b8;text-decoration:none;padding:.5rem 1.2rem;border-radius:.6rem;font-size:.85rem">
    {svg('arrow-left','w-4 h-4')} חזרה לתיקים
  </a>
  <button onclick="location.reload()" class="tappable" style="display:inline-flex;align-items:center;gap:.4rem;
     background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
     color:#94a3b8;padding:.5rem 1rem;border-radius:.6rem;font-size:.85rem">
    {svg('refresh','w-4 h-4')} רענן
  </button>
</div>

<script>
// Bar Chart Rule: donut ≤5, horizontal bar >5
function makeLegend(id,labels,colors,values){{
  var el=document.getElementById(id); if(!el)return;
  var tot=values.reduce((a,b)=>a+b,0);
  labels.forEach((l,i)=>{{
    var pct=tot>0?Math.round(values[i]/tot*100):0;
    var d=document.createElement('div');
    d.style.cssText='display:flex;align-items:center;gap:6px;direction:rtl';
    d.innerHTML='<span style="width:8px;height:8px;border-radius:2px;background:'+colors[i]+';flex-shrink:0"></span>'+
      '<span style="font-size:.75rem;color:#94a3b8;flex:1">'+l+'</span>'+
      '<span style="font-size:.72rem;color:#475569">'+pct+'%</span>';
    el.appendChild(d);
  }});
}}
function renderChart(id,labels,values,colors,legendId){{
  var canvas=document.getElementById(id);
  if(!canvas)return;
  if(labels.length<=5){{
    // Donut — beautiful for few items
    new Chart(canvas,{{type:'doughnut',
      data:{{labels,datasets:[{{data:values,backgroundColor:colors,borderWidth:0,hoverOffset:6}}]}},
      options:{{responsive:true,maintainAspectRatio:false,cutout:'65%',
        plugins:{{legend:{{display:false}},
          tooltip:{{callbacks:{{label:c=>c.label+' ₪'+c.parsed.toLocaleString()}}}}}}
      }}
    }});
    if(legendId)makeLegend(legendId,labels,colors,values);
  }}else{{
    // Horizontal Bar — clear for many items
    new Chart(canvas,{{type:'bar',
      data:{{
        labels:labels,
        datasets:[{{data:values,backgroundColor:colors,borderWidth:0,borderRadius:4}}]
      }},
      options:{{
        indexAxis:'y',responsive:true,maintainAspectRatio:false,
        plugins:{{legend:{{display:false}},
          tooltip:{{callbacks:{{label:c=>'₪'+c.parsed.x.toLocaleString()}}}}
        }},
        scales:{{
          x:{{display:false,grid:{{display:false}}}},
          y:{{
            ticks:{{color:'#94a3b8',font:{{size:11,family:'Assistant'}}}},
            grid:{{display:false}},border:{{display:false}}
          }}
        }}
      }}
    }});
  }}
}}
renderChart('c1',{json.dumps(pie_l,ensure_ascii=False)},{json.dumps(pie_v)},{json.dumps(pie_c)},'leg1');
renderChart('c2',{json.dumps(sl,ensure_ascii=False)},{json.dumps(sv)},{json.dumps(sc[:len(sl)])},'leg2');
</script>
</body></html>"""


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'─'*52}")
    print(f"  BankOS v4 (Senior FinTech)  ·  {datetime.now().strftime('%H:%M')}")
    print(f"{'─'*52}")

    data      = get_portfolio_data()
    raw_data  = json.loads(RAW_JSON.read_text(encoding="utf-8"))
    raw_by    = {p["name"]: p for p in raw_data["portfolios"]}
    history   = fetch_history()
    now       = datetime.now()

    print(f"  prices={data['pricesCount']}  history={sum(1 for h in history.values() if h)}")

    (OUT_DIR / "index.html").write_text(
        build_index(data["portfolios"], data["total"], history, raw_by), encoding="utf-8")
    print("  ✓ index.html")

    for p in data["portfolios"]:
        m = PORTFOLIO_META[p["name"]]
        html = build_deep(raw_by[p["name"]], p, history)
        (OUT_DIR / f"{m['slug']}.html").write_text(html, encoding="utf-8")
        print(f"  ✓ {m['slug']}.html")

    # Snapshot
    snap = DAILY_DIR / f"{now.strftime('%Y-%m-%d')}-snapshot.txt"
    lines = [f"BankOS {now.strftime('%Y-%m-%d %H:%M')}",
             f"Total gross: ₪{data['total']['totalValue']:,.2f}",
             f"Total net:   ₪{net_withdrawal(data['total']['totalValue'],500_000):,.2f}", ""]
    for p in data["portfolios"]:
        nw = net_withdrawal(p["totalValue"], 100_000)
        lines.append(f"  {p['name']:20s}  gross ₪{p['totalValue']:>10,.2f}  net ₪{nw:>10,.2f}  {p['netReturnPct']:+.2f}%")
    snap.write_text("\n".join(lines), encoding="utf-8")

    # Push
    for cmd in [
        ["git","-C",str(OUT_DIR),"add","-A"],
        ["git","-C",str(OUT_DIR),"commit","-m",f"v4 {now.strftime('%Y-%m-%d %H:%M')}"],
        ["git","-C",str(OUT_DIR),"push"],
    ]:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if "nothing to commit" in (r.stdout+r.stderr): print("  ↳ nothing changed"); break
    else:
        print(f"  {'✓ pushed' if r.returncode==0 else '✗ '+r.stderr[:60]}")

    print(f"\n  https://noamm-opencalw.github.io/investment-dashboard/")
    print(f"{'─'*52}\n")

if __name__ == "__main__":
    main()
