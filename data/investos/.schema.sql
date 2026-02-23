-- InvestOS Database Schema
-- SQLite with WAL mode for concurrent agent writes

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- תיקים
CREATE TABLE IF NOT EXISTS portfolios (
    id          TEXT PRIMARY KEY,  -- 'solid', 'aggressive', etc.
    name        TEXT NOT NULL,
    emoji       TEXT,
    strategy    TEXT,
    description TEXT,
    initial_capital REAL NOT NULL DEFAULT 100000,
    target_30d_pct  REAL,
    benchmark   TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- נכסים נוכחיים
CREATE TABLE IF NOT EXISTS positions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id    TEXT NOT NULL REFERENCES portfolios(id),
    ticker          TEXT NOT NULL,
    name            TEXT,
    asset_type      TEXT,  -- 'stock','index','bond','crypto','cash'
    sector          TEXT,
    quantity        REAL DEFAULT 0,
    avg_cost        REAL DEFAULT 0,   -- עלות ממוצעת ליחידה
    current_price   REAL,
    updated_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(portfolio_id, ticker)
);

-- היסטוריית עסקאות
CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id    TEXT NOT NULL REFERENCES portfolios(id),
    ticker          TEXT NOT NULL,
    action          TEXT NOT NULL,   -- 'buy','sell','dividend'
    quantity        REAL NOT NULL,
    price           REAL NOT NULL,
    gross_amount    REAL NOT NULL,   -- quantity × price
    fee             REAL DEFAULT 0,
    tax             REAL DEFAULT 0,  -- חישוב Ledger: profit × 0.25
    net_amount      REAL,            -- gross - tax - fee
    notes           TEXT,
    executed_by     TEXT DEFAULT 'virtual',
    approved_by     TEXT,            -- 'noam' (חובה לפני ביצוע)
    executed_at     TEXT DEFAULT (datetime('now'))
);

-- סנפשוט יומי לגרפים
CREATE TABLE IF NOT EXISTS daily_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id    TEXT NOT NULL REFERENCES portfolios(id),
    date            TEXT NOT NULL,
    gross_value     REAL NOT NULL,
    net_value       REAL NOT NULL,
    daily_change_pct REAL DEFAULT 0,
    benchmark_value REAL,  -- ערך בנצ'מרק לאותו יום
    notes           TEXT,
    UNIQUE(portfolio_id, date)
);

-- תובנות סוכנים (Vibe/Synergy/Trader)
CREATE TABLE IF NOT EXISTS insights (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent       TEXT NOT NULL,
    level       TEXT DEFAULT 'info',  -- 'info','warn','alert'
    portfolio_id TEXT REFERENCES portfolios(id),  -- NULL = system-wide
    text        TEXT NOT NULL,
    action_taken TEXT,
    confidence  REAL,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- אסטרטגיות ו-Backtest
CREATE TABLE IF NOT EXISTS strategies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id    TEXT NOT NULL REFERENCES portfolios(id),
    name            TEXT NOT NULL,
    type            TEXT,  -- 'passive','ai_active','balanced'
    status          TEXT DEFAULT 'proposed',  -- 'proposed','backtesting','approved','active','rejected'
    backtest_return_pct REAL,
    backtest_sharpe     REAL,
    backtest_max_drawdown REAL,
    approved_by     TEXT,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Views שימושיים ל-Ledger
CREATE VIEW IF NOT EXISTS v_portfolio_summary AS
SELECT
    p.id, p.name, p.emoji, p.strategy,
    p.initial_capital,
    COALESCE(SUM(pos.quantity * pos.current_price), p.initial_capital) AS gross_value,
    COALESCE(SUM(t.fee), 0) AS total_fees,
    COALESCE(SUM(t.tax), 0) AS total_tax
FROM portfolios p
LEFT JOIN positions pos ON pos.portfolio_id = p.id
LEFT JOIN transactions t ON t.portfolio_id = p.id
GROUP BY p.id;

CREATE VIEW IF NOT EXISTS v_ledger_report AS
SELECT
    portfolio_id,
    strftime('%Y-%m', executed_at) AS month,
    COUNT(*) AS trade_count,
    SUM(gross_amount) AS total_gross,
    SUM(fee) AS total_fees,
    SUM(tax) AS total_tax,
    SUM(net_amount) AS total_net
FROM transactions
WHERE action IN ('buy','sell')
GROUP BY portfolio_id, month;
