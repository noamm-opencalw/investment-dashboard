#!/usr/bin/env python3
"""
Investment Dashboard Generator
Fetches live data → generates index.html → pushes to GitHub → Netlify deploys
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add tracker to path
sys.path.insert(0, str(Path(__file__).parent.parent / "investment-learning" / "scripts"))

def get_portfolio_data():
    """Get data from unified tracker"""
    from tracker_unified import get_portfolio_data
    return get_portfolio_data()

def generate_html(data):
    """Generate full index.html with real data"""
    
    now = datetime.now()
    timestamp = now.strftime("%d/%m/%Y %H:%M")
    
    portfolios = data['portfolios']
    total = data['total']
    
    emojis = {
        'SOLID': '🐢', 'AGGRESSIVE': '🦁',
        'SUPER-AGGRESSIVE': '🚀', 'SPECULATIVE': '🎯', 'CREATIVE': '🎨'
    }
    colors = {
        'SOLID': '#6366f1', 'AGGRESSIVE': '#8b5cf6',
        'SUPER-AGGRESSIVE': '#ec4899', 'SPECULATIVE': '#f43f5e', 'CREATIVE': '#f59e0b'
    }
    
    # Portfolio cards HTML
    cards_html = ""
    chart_labels = []
    chart_values = []
    chart_colors = []
    
    for p in portfolios:
        emoji = emojis.get(p['name'], '📊')
        color = colors.get(p['name'], '#6366f1')
        is_positive = p['netPnL'] >= 0
        card_border = 'border-emerald-500' if is_positive else 'border-red-500'
        pnl_color = 'text-emerald-400' if is_positive else 'text-red-400'
        badge_color = 'bg-emerald-500/20 text-emerald-400' if is_positive else 'bg-red-500/20 text-red-400'
        arrow = '▲' if is_positive else '▼'
        abs_pct = abs(p['netReturnPct'])
        abs_pnl = abs(p['netPnL'])
        
        cards_html += f"""
        <div class="glass rounded-2xl p-5 shadow-lg border-r-4 {card_border} transition-transform duration-300 hover:-translate-y-1">
            <div class="flex justify-between items-start mb-3">
                <div>
                    <h3 class="text-white font-bold text-base">{p['name']}</h3>
                    <p class="text-xs text-slate-400">{p['nickname']}</p>
                </div>
                <span class="text-3xl">{emoji}</span>
            </div>
            
            <p class="text-3xl font-extrabold text-white mb-1">₪{p['totalValue']:,.0f}</p>
            <p class="text-xs text-slate-500 mb-3">{p['positionsCount']} מניות נעקבות</p>
            
            <div class="flex justify-between items-center">
                <div>
                    <p class="text-xs text-slate-400">Net P/L</p>
                    <p class="{pnl_color} font-bold">₪{p['netPnL']:+,.0f}</p>
                </div>
                <span class="{badge_color} px-3 py-1 rounded-full text-sm font-bold">
                    {arrow} {abs_pct:.2f}%
                </span>
            </div>
            
            <div class="mt-3 pt-3 border-t border-slate-700/50 text-xs text-slate-500 flex justify-between">
                <span>💸 עמלות: ₪{p['fees']:,.0f}</span>
                <span>🏛️ מס: ₪{p['tax']:,.0f}</span>
            </div>
        </div>"""
        
        chart_labels.append(p['name'])
        chart_values.append(round(p['totalValue']))
        chart_colors.append(color)
    
    # Total header
    total_pnl = total['netPnL']
    total_pct = total['netReturnPct']
    is_total_pos = total_pnl >= 0
    total_border = 'border-emerald-500' if is_total_pos else 'border-red-500'
    total_color = 'text-emerald-400' if is_total_pos else 'text-red-400'
    total_arrow = '▲' if is_total_pos else '▼'
    
    # Historical data for line chart (from snapshots)
    snapshots_dir = Path(__file__).parent.parent / "investment-learning" / "daily"
    history_labels = []
    history_values = []
    
    if snapshots_dir.exists():
        for snap_file in sorted(snapshots_dir.glob("*.txt"))[-14:]:
            try:
                content = snap_file.read_text()
                for line in content.split('\n'):
                    if 'Total Value:' in line and '₪' in line:
                        val_str = line.split('₪')[1].replace(',', '').strip()
                        val = float(val_str)
                        date_str = snap_file.stem[:10]
                        history_labels.append(date_str)
                        history_values.append(round(val))
                        break
            except:
                pass
    
    if not history_values:
        history_labels = [datetime.now().strftime("%Y-%m-%d")]
        history_values = [round(total['totalValue'])]
    
    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BankOS — תיקי השקעות נועם 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Assistant', sans-serif; background-color: #0f172a; color: #f8fafc; }}
        .glass {{
            background: rgba(30, 41, 59, 0.65);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 60%);
        }}
        @keyframes pulse-slow {{ 0%,100%{{opacity:1}} 50%{{opacity:.6}} }}
        .live-dot {{ animation: pulse-slow 2s infinite; }}
    </style>
</head>
<body class="min-h-screen gradient-bg p-4 pb-24">
    
    <!-- Header -->
    <header class="mb-6 text-center pt-4">
        <div class="flex items-center justify-center gap-2 mb-1">
            <div class="live-dot w-2 h-2 bg-emerald-400 rounded-full"></div>
            <span class="text-xs text-emerald-400 font-semibold tracking-widest uppercase">Live</span>
        </div>
        <h1 class="text-2xl font-extrabold text-blue-400 tracking-tight">BankOS — תיקי נועם</h1>
        <p class="text-slate-500 text-xs mt-1">עודכן: {timestamp} • {data['pricesCount']} מניות • net performance</p>
    </header>

    <!-- Total Value Hero Card -->
    <div class="glass rounded-3xl p-6 mb-6 text-center shadow-2xl border-b-4 {total_border}">
        <p class="text-slate-400 text-sm mb-1">שווי תיק כולל (נטו)</p>
        <div class="text-5xl font-extrabold tracking-tight my-2">₪{total['totalValue']:,.0f}</div>
        <div class="{total_color} font-bold text-lg">
            {total_arrow} ₪{abs(total_pnl):,.0f} ({total_pct:+.2f}%)
        </div>
        <div class="flex justify-center gap-4 mt-4 text-xs text-slate-500">
            <span class="bg-slate-800/60 px-3 py-1 rounded-full">💸 עמלות ₪{total['fees']:,.0f}</span>
            <span class="bg-slate-800/60 px-3 py-1 rounded-full">🏛️ מס ₪{total['tax']:,.0f}</span>
            <span class="bg-slate-800/60 px-3 py-1 rounded-full">📉 ברוטו {total['grossReturnPct']:+.2f}%</span>
        </div>
    </div>

    <!-- Portfolio Cards Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        {cards_html}
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        
        <!-- Doughnut Chart -->
        <div class="glass rounded-2xl p-5 shadow-xl">
            <h3 class="text-slate-300 font-bold text-sm mb-4 text-center">התפלגות תיקים</h3>
            <div style="height:220px; position:relative;">
                <canvas id="doughnutChart"></canvas>
            </div>
        </div>
        
        <!-- Line Chart -->
        <div class="glass rounded-2xl p-5 shadow-xl">
            <h3 class="text-slate-300 font-bold text-sm mb-4 text-center">שינוי שווי לאורך זמן</h3>
            <div style="height:220px; position:relative;">
                <canvas id="lineChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Bottom Nav -->
    <nav class="fixed bottom-0 left-0 right-0 glass h-16 flex justify-around items-center border-t border-slate-700/50 z-10">
        <button class="flex flex-col items-center text-blue-400">
            <span class="text-lg">📊</span>
            <span class="text-xs font-semibold">תיקים</span>
        </button>
        <button class="flex flex-col items-center text-slate-500" onclick="location.reload()">
            <span class="text-lg">🔄</span>
            <span class="text-xs">רענן</span>
        </button>
        <button class="flex flex-col items-center text-slate-500">
            <span class="text-lg">📈</span>
            <span class="text-xs">היסטוריה</span>
        </button>
    </nav>

    <script>
        const COLORS = {json.dumps(chart_colors)};
        
        // Doughnut Chart
        new Chart(document.getElementById('doughnutChart'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(chart_labels)},
                datasets: [{{
                    data: {json.dumps(chart_values)},
                    backgroundColor: COLORS,
                    borderWidth: 0,
                    hoverOffset: 8
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                cutout: '65%',
                plugins: {{
                    legend: {{
                        display: true, position: 'bottom',
                        labels: {{ color: '#94a3b8', font: {{ size: 11, family: 'Assistant' }}, padding: 10 }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: ctx => ctx.label + ': ₪' + ctx.parsed.toLocaleString()
                        }}
                    }}
                }}
            }}
        }});
        
        // Line Chart
        new Chart(document.getElementById('lineChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(history_labels)},
                datasets: [{{
                    label: 'שווי תיק',
                    data: {json.dumps(history_values)},
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59,130,246,0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#3b82f6',
                    pointRadius: 4
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: ctx => '₪' + ctx.parsed.y.toLocaleString()
                        }}
                    }}
                }},
                scales: {{
                    x: {{ ticks: {{ color: '#64748b', font: {{ size: 10 }} }}, grid: {{ display: false }} }},
                    y: {{ ticks: {{ color: '#64748b', font: {{ size: 10 }}, callback: v => '₪' + (v/1000).toFixed(0) + 'K' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    return html

def push_to_github():
    """git add, commit, push"""
    dashboard_dir = Path(__file__).parent
    
    result = subprocess.run(
        ["git", "add", "-A"],
        cwd=dashboard_dir, capture_output=True, text=True
    )
    
    result = subprocess.run(
        ["git", "commit", "-m", f"Live Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
        cwd=dashboard_dir, capture_output=True, text=True
    )
    
    if "nothing to commit" in result.stdout:
        print("⏭️  Nothing changed, skipping push")
        return True
    
    result = subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=dashboard_dir, capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print("✅ Pushed to GitHub!")
        return True
    else:
        print(f"❌ Push failed: {result.stderr}")
        return False

def main():
    print(f"\n{'='*60}")
    print(f"🚀 Investment Dashboard Generator - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    # 1. Fetch data
    print("\n📡 Fetching portfolio data...")
    data = get_portfolio_data()
    print(f"✅ Got data: {data['pricesCount']} prices")
    
    # 2. Generate HTML
    print("🎨 Generating dashboard HTML...")
    html = generate_html(data)
    
    output_path = Path(__file__).parent / "index.html"
    output_path.write_text(html, encoding='utf-8')
    print(f"✅ Saved: {output_path} ({len(html):,} bytes)")
    
    # 3. Push to GitHub
    print("📤 Pushing to GitHub...")
    push_to_github()
    
    print(f"\n✅ Dashboard updated!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
