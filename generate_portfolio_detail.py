#!/usr/bin/env python3
"""
Portfolio Detail Page Generator
Creates dedicated detail pages for each portfolio with:
- Category pie chart
- Detailed holdings table
- 7-day performance chart
- Back button to dashboard
"""

import json
from pathlib import Path
from datetime import datetime

def generate_detail_page(portfolio_id, portfolio_data, all_portfolios):
    """Generate a detailed portfolio page"""
    
    meta = {
        "SOLID": {"slug": "turtle", "emoji": "🐢", "heb": "שמרני", "name": "תיק Solid"},
        "AGGRESSIVE": {"slug": "lion", "emoji": "🦁", "heb": "אגרסיבי", "name": "תיק Aggressive"},
        "SUPER-AGGRESSIVE": {"slug": "rocket", "emoji": "🚀", "heb": "סופר-אגרסיבי", "name": "תיק Super-Aggressive"},
        "SPECULATIVE": {"slug": "target", "emoji": "🎯", "heb": "ספקולטיבי", "name": "תיק Speculative"},
        "CREATIVE": {"slug": "canvas", "emoji": "🎨", "heb": "קריאטיבי", "name": "תיק Creative"},
    }
    
    portfolio_meta = meta.get(portfolio_id, {})
    portfolio_name = portfolio_meta.get("name", portfolio_id)
    emoji = portfolio_meta.get("emoji", "📊")
    
    # Extract data
    net_value = portfolio_data.get("net_value", 0)
    performance_pct = portfolio_data.get("performance_pct", 0)
    holdings = portfolio_data.get("holdings", [])
    
    # Calculate categories
    categories = {}
    for holding in holdings:
        category = holding.get("sector", "אחר")
        value = holding.get("value", 0)
        categories[category] = categories.get(category, 0) + value
    
    # Sort holdings by value
    sorted_holdings = sorted(holdings, key=lambda x: x.get("value", 0), reverse=True)
    
    # Performance indicator
    perf_class = "text-green-400" if performance_pct > 0 else "text-red-400"
    perf_arrow = "↗" if performance_pct > 0 else "↘"
    
    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{portfolio_name} - פרטים מלאים</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Heebo', sans-serif;
        }}
        .glass {{
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(148, 163, 184, 0.1);
        }}
        .stat-card {{
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(148, 163, 184, 0.1);
            transition: all 0.3s ease;
        }}
        .stat-card:hover {{
            background: rgba(30, 41, 59, 0.6);
            border-color: rgba(148, 163, 184, 0.2);
        }}
    </style>
</head>
<body class="min-h-screen text-slate-50 p-4 md:p-8">
    
    <!-- Back Button -->
    <div class="max-w-7xl mx-auto mb-6">
        <a href="index.html" class="inline-flex items-center gap-2 px-4 py-2 glass rounded-lg hover:bg-slate-700/50 transition">
            <span>←</span>
            <span>חזרה לדשבורד</span>
        </a>
    </div>
    
    <!-- Header -->
    <div class="max-w-7xl mx-auto glass rounded-2xl p-6 md:p-8 mb-6">
        <div class="flex items-center justify-between flex-wrap gap-4">
            <div>
                <h1 class="text-3xl md:text-4xl font-bold mb-2">
                    {emoji} {portfolio_name}
                </h1>
                <p class="text-slate-400">עדכון אחרון: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
            </div>
            <div class="text-left">
                <div class="text-4xl md:text-5xl font-bold {perf_class}">
                    {perf_arrow} {performance_pct:+.2f}%
                </div>
            </div>
        </div>
    </div>
    
    <!-- Summary Cards -->
    <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="stat-card rounded-xl p-6">
            <div class="text-slate-400 text-sm mb-2">סה"כ נכסים נטו</div>
            <div class="text-3xl font-bold">₪{net_value:,.0f}</div>
        </div>
        <div class="stat-card rounded-xl p-6">
            <div class="text-slate-400 text-sm mb-2">תשואה כוללת</div>
            <div class="text-3xl font-bold {perf_class}">{performance_pct:+.2f}%</div>
        </div>
        <div class="stat-card rounded-xl p-6">
            <div class="text-slate-400 text-sm mb-2">מניות בתיק</div>
            <div class="text-3xl font-bold">{len(holdings)}</div>
        </div>
    </div>
    
    <!-- Charts Row -->
    <div class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <!-- Category Breakdown -->
        <div class="glass rounded-2xl p-6">
            <h2 class="text-xl font-bold mb-4">חלוקה לפי תחומים</h2>
            <canvas id="categoryChart"></canvas>
        </div>
        
        <!-- 7-Day Performance (placeholder) -->
        <div class="glass rounded-2xl p-6">
            <h2 class="text-xl font-bold mb-4">ביצועים - 7 ימים אחרונים</h2>
            <div class="text-center text-slate-400 py-12">
                גרף ביצועים בפיתוח
            </div>
        </div>
    </div>
    
    <!-- Holdings Table -->
    <div class="max-w-7xl mx-auto glass rounded-2xl p-6 mb-6">
        <h2 class="text-2xl font-bold mb-6">מניות בתיק</h2>
        <div class="overflow-x-auto">
            <table class="w-full">
                <thead>
                    <tr class="border-b border-slate-700">
                        <th class="text-right py-3 px-4">סימול</th>
                        <th class="text-right py-3 px-4">שם החברה</th>
                        <th class="text-right py-3 px-4">תחום</th>
                        <th class="text-right py-3 px-4">כמות</th>
                        <th class="text-right py-3 px-4">מחיר</th>
                        <th class="text-right py-3 px-4">שווי</th>
                        <th class="text-right py-3 px-4">% מהתיק</th>
                        <th class="text-right py-3 px-4">תשואה</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Add holdings rows
    for holding in sorted_holdings:
        symbol = holding.get("symbol", "")
        name = holding.get("name", symbol)
        sector = holding.get("sector", "אחר")
        qty = holding.get("quantity", 0)
        price = holding.get("price", 0)
        value = holding.get("value", 0)
        pct_of_portfolio = (value / net_value * 100) if net_value > 0 else 0
        return_pct = holding.get("return_pct", 0)
        return_class = "text-green-400" if return_pct > 0 else "text-red-400"
        
        html += f"""
                    <tr class="border-b border-slate-800 hover:bg-slate-800/30">
                        <td class="py-3 px-4 font-mono">{symbol}</td>
                        <td class="py-3 px-4">{name}</td>
                        <td class="py-3 px-4 text-slate-400">{sector}</td>
                        <td class="py-3 px-4">{qty:.0f}</td>
                        <td class="py-3 px-4">₪{price:.2f}</td>
                        <td class="py-3 px-4 font-bold">₪{value:,.0f}</td>
                        <td class="py-3 px-4">{pct_of_portfolio:.1f}%</td>
                        <td class="py-3 px-4 {return_class} font-bold">{return_pct:+.1f}%</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Action Buttons -->
    <div class="max-w-7xl mx-auto flex gap-4 justify-center mb-8">
        <button onclick="window.print()" class="px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition">
            🖨️ הדפס דוח
        </button>
        <button onclick="exportToCSV()" class="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg transition">
            📊 ייצוא לExcel
        </button>
    </div>
    
    <script>
        // Category Pie Chart
        const categoryData = {
"""
    
    # Add category data for chart
    category_labels = []
    category_values = []
    for cat, val in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        category_labels.append(cat)
        category_values.append(val)
    
    html += f"""
            labels: {json.dumps(category_labels)},
            datasets: [{{
                data: {json.dumps(category_values)},
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(139, 92, 246, 0.8)',
                    'rgba(236, 72, 153, 0.8)',
                ],
                borderColor: 'rgba(30, 41, 59, 1)',
                borderWidth: 2
            }}]
        }};
        
        const categoryChart = new Chart(
            document.getElementById('categoryChart'),
            {{
                type: 'pie',
                data: categoryData,
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'bottom',
                            labels: {{
                                color: '#f1f5f9',
                                font: {{ size: 14 }}
                            }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return context.label + ': ₪' + value.toLocaleString('he-IL') + ' (' + percentage + '%)';
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        );
        
        // Export to CSV
        function exportToCSV() {{
            const rows = [
                ['סימול', 'שם החברה', 'תחום', 'כמות', 'מחיר', 'שווי', '% מהתיק', 'תשואה']
            ];
"""
    
    # Add holdings data for CSV export
    for holding in sorted_holdings:
        html += f"""
            rows.push([
                '{holding.get("symbol", "")}',
                '{holding.get("name", "")}',
                '{holding.get("sector", "")}',
                {holding.get("quantity", 0)},
                {holding.get("price", 0)},
                {holding.get("value", 0)},
                {(holding.get("value", 0) / net_value * 100) if net_value > 0 else 0:.1f},
                {holding.get("return_pct", 0):.1f}
            ]);
"""
    
    html += """
            const csvContent = rows.map(row => row.join(',')).join('\\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = '""" + portfolio_id.lower() + """_holdings.csv';
            link.click();
        }
    </script>
</body>
</html>
"""
    
    return html


if __name__ == "__main__":
    # Example usage
    print("Portfolio detail page generator ready")
