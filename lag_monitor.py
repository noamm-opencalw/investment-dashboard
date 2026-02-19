#!/usr/bin/env python3
"""
Lag Monitor — BankOS API Performance Tracker
מודד זמן תגובה לכל stock symbol, מזהה bottlenecks, שומר לog
"""

import time
import json
import statistics
import subprocess
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("/tmp/bankos_lag_log.json")
ALERT_THRESHOLD_MS = 3000  # מעל 3 שניות = בעיה

def measure_single(symbol: str) -> dict:
    """מודד זמן תגובה עבור symbol אחד"""
    start = time.perf_counter()
    
    try:
        # בדיקה ישירה דרך yfinance (בתוך venv)
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        data = ticker.fast_info
        _ = data.last_price  # force fetch
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "symbol": symbol,
            "elapsed_ms": round(elapsed_ms, 1),
            "status": "ok",
            "alert": elapsed_ms > ALERT_THRESHOLD_MS
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "symbol": symbol,
            "elapsed_ms": round(elapsed_ms, 1),
            "status": "error",
            "error": str(e),
            "alert": True
        }

def run_full_profile(symbols: list) -> dict:
    """מריץ profile מלא על כל הסימבולים"""
    results = []
    
    print(f"\n🔍 BankOS Lag Monitor — {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)
    
    # שלב 1: מדידת כל symbol בנפרד
    for sym in symbols:
        result = measure_single(sym)
        results.append(result)
        
        status_icon = "✅" if result["status"] == "ok" else "❌"
        alert_icon = " ⚠️ SLOW" if result.get("alert") else ""
        print(f"{status_icon} {sym:<12} {result['elapsed_ms']:>8.1f}ms{alert_icon}")
    
    # שלב 2: סטטיסטיקות
    ok_results = [r for r in results if r["status"] == "ok"]
    times = [r["elapsed_ms"] for r in ok_results]
    
    stats = {}
    if times:
        stats = {
            "min_ms": round(min(times), 1),
            "max_ms": round(max(times), 1),
            "avg_ms": round(statistics.mean(times), 1),
            "median_ms": round(statistics.median(times), 1),
            "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 1),
            "slowest": max(ok_results, key=lambda x: x["elapsed_ms"])["symbol"],
            "failed": [r["symbol"] for r in results if r["status"] == "error"],
            "alerts": [r["symbol"] for r in results if r.get("alert")]
        }
        
        print("\n📊 Summary:")
        print(f"   avg={stats['avg_ms']}ms | p95={stats['p95_ms']}ms | max={stats['max_ms']}ms")
        if stats["alerts"]:
            print(f"   ⚠️  Slow symbols: {', '.join(stats['alerts'])}")
        if stats["failed"]:
            print(f"   ❌ Failed: {', '.join(stats['failed'])}")
        
        # שלב 3: אבחון אוטומטי
        if stats["avg_ms"] > 5000:
            print("\n🚨 ROOT CAUSE: Yahoo Finance API slow — consider:")
            print("   • Batch request במקום serial (ThreadPoolExecutor)")
            print("   • Cache results for 5-min window")
            print("   • Fallback to TASE Maya API for Israeli stocks")
        elif stats["p95_ms"] > 3000:
            print("\n⚠️  Outlier symbols slow — consider async fetching")
    
    # שלב 4: שמירת log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "stats": stats
    }
    
    # קריאת log קיים
    history = []
    if LOG_FILE.exists():
        try:
            history = json.loads(LOG_FILE.read_text())
        except:
            history = []
    
    history.append(log_entry)
    history = history[-50:]  # שמור רק 50 ריצות אחרונות
    LOG_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False))
    
    print(f"\n📁 Log saved: {LOG_FILE}")
    return log_entry

def check_venv_issue():
    """בודקת אם הסקריפט רץ בלי venv - הבעיה שמצאנו!"""
    try:
        import yfinance
        return {"venv_ok": True}
    except ImportError:
        return {
            "venv_ok": False, 
            "fix": "cd /projects/investment-dashboard && source .venv-invest/bin/activate"
        }

if __name__ == "__main__":
    # בדיקת venv ראשית
    venv_check = check_venv_issue()
    if not venv_check["venv_ok"]:
        print("❌ CRITICAL: yfinance לא מותקן בסביבה הנוכחית!")
        print(f"   Fix: {venv_check['fix']}")
        exit(1)
    
    # סימבולים מ-BankOS (כל 5 התיקים)
    SYMBOLS = [
        # SOLID
        "QQQ", "GLD",
        # AGGRESSIVE  
        "ESLT.TA", "PHOE.TA", "HARL.TA",
        # SUPER-AGG
        "NXSN.TA", "ARYT.TA",
        # SPECULATIVE
        "BIG.TA", "FTAL.TA",
        # CREATIVE
        "AZRG.TA", "SAE.TA"
    ]
    
    run_full_profile(SYMBOLS)
