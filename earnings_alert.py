#!/usr/bin/env python3
"""
BankOS Earnings Alert
מתריע ב-Telegram כשמניות בתיקים עומדות לדווח תוצאות
רץ כל בוקר בשעה 08:30
"""

import json
import os
import sys
from datetime import datetime, timedelta
import pytz

# ── הגדרות ──────────────────────────────────────────────
PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__),
                              '../investment-learning/portfolios-5way.json')

ALERT_DAYS_AHEAD = 7   # התרעה עד X ימים קדימה
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '671957209')
TZ = pytz.timezone('Asia/Jerusalem')

# מיפוי: symbol מהJSON → Yahoo Finance ticker
SYMBOL_MAP = {
    'TLV:HARL':  'HARL.TA',
    'TLV:PHOE':  'PHOE.TA',
    'TLV:BIG':   'BIG.TA',
    'TLV:ESLT':  'ESLT.TA',
    'TLV:AZRG':  'AZRG.TA',
    'TLV:LUMI':  'LUMI.TA',
    'TLV:NXTV':  'NXTV.TA',
    'TLV:ARYT':  'ARYT.TA',
    'TLV:DEDRL': 'DEDRL.TA',
    'TLV:NWMD':  'NWMD.TA',
    'TLV:RATI':  'RATI.TA',
    'TLV:FTHL':  'FTAL.TA',
    'TLV:MORE':  'MORE.TA',
    'TLV:MTDS':  'MTDS.TA',
    'TLV:SHFR':  'SAE.TA',
    'TLV:TRPZ':  'TRPZ.TA',
    'TLV:NICE':  'NICE.TA',
    'TLV:ENOG':  'ENOG.TA',
    'NASDAQ:CHKP': 'CHKP',
    'NASDAQ:TEVA': 'TEVA',
    'NASDAQ:QQQ':  'QQQ',
}

EMOJI = {
    'today':    '🚨',
    'tomorrow': '⚠️',
    'soon':     '📅',
}

# ── פונקציות ──────────────────────────────────────────────
def load_portfolios():
    """טוען את כל המניות מהתיקים + לאיזה תיק כל מניה שייכת"""
    with open(PORTFOLIO_FILE) as f:
        data = json.load(f)

    stocks = {}  # symbol → {name, portfolios: []}
    for p in data['portfolios']:
        for pos in p.get('positions', []):
            sym = pos.get('yahooSymbol') or pos.get('symbol', '')
            if not sym or sym.startswith('BONDS:') or sym.startswith('CRYPTO:') \
               or sym.startswith('LEVERAGE:') or 'TBD' in sym or 'REIT' in sym:
                continue
            name = pos.get('name', sym)
            if sym not in stocks:
                stocks[sym] = {'name': name, 'portfolios': []}
            stocks[sym]['portfolios'].append(p['name'])
    return stocks

def get_earnings_date(yahoo_symbol):
    """מחזיר תאריך הדו"ח הבא, או None אם לא ידוע"""
    import signal

    def handler(signum, frame):
        raise TimeoutError()

    try:
        import yfinance as yf
        from datetime import datetime
        import pytz

        signal.signal(signal.SIGALRM, handler)
        signal.alarm(8)  # timeout של 8 שניות לכל מניה

        ticker = yf.Ticker(yahoo_symbol)
        ed = ticker.earnings_dates
        signal.alarm(0)

        if ed is None or len(ed) == 0:
            return None
        today = datetime.now(pytz.utc)
        future = ed[ed.index > today]
        if len(future) == 0:
            return None
        return future.index[-1]
    except (Exception, TimeoutError):
        signal.alarm(0)
        return None

def days_until(dt):
    """כמה ימים עד תאריך נתון (מהיום)"""
    today = datetime.now(TZ).date()
    target = dt.date() if hasattr(dt, 'date') else dt
    return (target - today).days

def send_telegram(message):
    """שולח הודעה ב-Telegram"""
    import urllib.request
    import urllib.parse

    if not TELEGRAM_TOKEN:
        print("⚠️  TELEGRAM_TOKEN לא מוגדר — מדפיס במקום שולח:")
        print(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }).encode()

    try:
        urllib.request.urlopen(url, payload, timeout=10)
        print("✅ הודעה נשלחה ב-Telegram")
    except Exception as e:
        print(f"❌ שגיאת Telegram: {e}")

def format_alert(upcoming):
    """בונה הודעת Telegram"""
    today_str = datetime.now(TZ).strftime('%d/%m/%Y')
    lines = [f"<b>📊 BankOS — Earnings Alert | {today_str}</b>\n"]

    for item in upcoming:
        d = item['days']
        sym = item['yahoo_symbol']
        name = item['name']
        portfolios = ', '.join(item['portfolios'])
        date_str = item['date'].strftime('%d/%m/%Y')

        if d == 0:
            label = f"{EMOJI['today']} <b>היום!</b>"
        elif d == 1:
            label = f"{EMOJI['tomorrow']} מחר"
        else:
            label = f"{EMOJI['soon']} בעוד {d} ימים ({date_str})"

        lines.append(f"{label} — <b>{name}</b> ({sym})")
        lines.append(f"   תיקים: {portfolios}\n")

    lines.append("─────────────────")
    lines.append(f"<a href='https://noamm-opencalw.github.io/investment-dashboard/'>פתח BankOS</a>")
    return '\n'.join(lines)

# ── ריצה ראשית ────────────────────────────────────────────
def main():
    print(f"🔍 BankOS Earnings Alert — {datetime.now(TZ).strftime('%d/%m/%Y %H:%M')}")

    stocks = load_portfolios()
    print(f"📋 {len(stocks)} מניות בתיקים")

    upcoming = []

    for sym, info in stocks.items():
        yahoo_sym = SYMBOL_MAP.get(sym, sym.split(':')[-1])
        print(f"  בודק {yahoo_sym}...", end=' ', flush=True)

        earnings_dt = get_earnings_date(yahoo_sym)
        if earnings_dt is None:
            print("אין תאריך")
            continue

        d = days_until(earnings_dt)
        if 0 <= d <= ALERT_DAYS_AHEAD:
            print(f"🎯 בעוד {d} ימים!")
            upcoming.append({
                'symbol': sym,
                'yahoo_symbol': yahoo_sym,
                'name': info['name'],
                'portfolios': info['portfolios'],
                'date': earnings_dt,
                'days': d,
            })
        else:
            print(f"בעוד {d} ימים (לא בטווח)")

    if not upcoming:
        print("\n✅ אין דו\"חות בשבוע הקרוב")
        return

    # מיון לפי קרבה
    upcoming.sort(key=lambda x: x['days'])

    print(f"\n🚨 נמצאו {len(upcoming)} דו\"חות קרובים:")
    for item in upcoming:
        print(f"  {item['name']}: בעוד {item['days']} ימים")

    message = format_alert(upcoming)
    print("\n── הודעה ──")
    print(message)
    print("──────────")
    send_telegram(message)

if __name__ == '__main__':
    main()
