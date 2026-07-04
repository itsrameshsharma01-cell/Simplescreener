import pandas as pd
import os
from datetime import datetime

def format_val(val, suffix=""):
    if pd.isna(val) or val == "N/A":
        return "<span class='neutral'>-</span>"
    try:
        num = float(val)
        color = "positive" if num > 0 else "negative"
        if suffix == "%":
            return f"<span class='{color}'>{'+' if num > 0 else ''}{num}%</span>"
        return f"{num}{suffix}"
    except:
        return val

def generate_table(dataframe, table_id, is_historical=False):
    html = f"""
            <div class="table-toolbar">
                <div class="export-group">
                    <button class="export-btn" onclick="exportCSV('{table_id}')" title="Download CSV">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        CSV
                    </button>
                    <button class="export-btn" onclick="exportTradingView('{table_id}')" title="Export TradingView Watchlist">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                        TradingView
                    </button>
                    <button class="export-btn" onclick="exportText('{table_id}')" title="Copy as Text">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                        Copy
                    </button>
                </div>
                <span class="stock-count" id="count-{table_id}"></span>
            </div>
            <div style="overflow-x: auto;">
            <table id="{table_id}">
                <thead>
                    <tr>
                        <th class="th-star"></th>
                        <th onclick="sortTable('{table_id}', 1)">Symbol</th>
                        <th onclick="sortTable('{table_id}', 2)">Sector</th>
                        <th onclick="sortTable('{table_id}', 3)">Sect Rank</th>
                        <th onclick="sortTable('{table_id}', 4)">RS Score</th>
                        <th onclick="sortTable('{table_id}', 5)">CMP</th>
                        <th onclick="sortTable('{table_id}', 6)">Dist 10EMA</th>
                        <th onclick="sortTable('{table_id}', 7)">MCap (Cr)</th>
                        <th onclick="sortTable('{table_id}', 8)">QoQ EPS</th>
                        <th onclick="sortTable('{table_id}', 9)">QoQ Sales</th>
                        <th onclick="sortTable('{table_id}', 10)">D/E Ratio</th>
                        <th onclick="sortTable('{table_id}', 11)">Free Float</th>
                    </tr>
                </thead>
                <tbody>
    """
    for _, row in dataframe.iterrows():
        symbol = row.get('Symbol', '')
        clean_sym = symbol.replace('.NS', '')
        if is_historical:
            date_attr = f' data-date="{row.get("Date", "")}"'
            row_class = "hist-row"
        else:
            date_attr = ""
            row_class = ""

        price = row.get('Price', 'N/A')
        if pd.isna(price):
            price = 'N/A'

        html += f"""
                    <tr class="{row_class}"{date_attr} data-symbol="{clean_sym}">
                        <td class="star-cell">
                            <button class="star-btn" onclick="toggleFocus('{clean_sym}', this)" title="Add to Focus">☆</button>
                        </td>
                        <td class="symbol">
                            <a href="https://in.tradingview.com/chart/?symbol=NSE:{clean_sym}" target="_blank" class="tv-link" title="Open in TradingView">{clean_sym}</a>
                        </td>
                        <td><span class="badge">{row.get('Sector', 'N/A')}</span></td>
                        <td>{row.get('Sector_Rank', 'N/A')}</td>
                        <td style="font-weight: 600;">{format_val(row.get('RS_Rating', 'N/A'))}</td>
                        <td class="price-cell">{price}</td>
                        <td>{format_val(row.get('Dist_10EMA', 'N/A'), "%")}</td>
                        <td>{format_val(row.get('Market_Cap_Cr', 'N/A'))}</td>
                        <td>{format_val(row.get('QoQ_EPS', 'N/A'), "%")}</td>
                        <td>{format_val(row.get('QoQ_Sales', 'N/A'), "%")}</td>
                        <td>{format_val(row.get('Debt_Equity', 'N/A'))}</td>
                        <td>{format_val(row.get('Free_Float_Pct', 'N/A'), "%")}</td>
                    </tr>
        """
    html += """
                </tbody>
            </table>
            </div>
    """
    return html

def generate_dashboard():
    # 1. Load Daily Data
    daily_csv = "daily_screener_results.csv"
    if os.path.exists(daily_csv):
        df_daily = pd.read_csv(daily_csv)

        if 'RS_Score' in df_daily.columns:
            df_daily['RS_Rating'] = df_daily['RS_Score']
        if 'MarketCap_Cr' in df_daily.columns:
            df_daily['Market_Cap_Cr'] = df_daily['MarketCap_Cr']
        if 'Free_Float' in df_daily.columns:
            df_daily['Free_Float_Pct'] = df_daily['Free_Float']

        daily_watchlist = df_daily[df_daily['Is_Watchlist'] == True]
        daily_breakouts = df_daily[df_daily['Is_Breakout'] == True]
        daily_universe = df_daily
    else:
        df_daily = pd.DataFrame()
        daily_watchlist = pd.DataFrame()
        daily_breakouts = pd.DataFrame()
        daily_universe = pd.DataFrame()

    # 2. Load Historical Data
    hist_csv = "historical_screener_results.csv"
    if os.path.exists(hist_csv):
        df_hist = pd.read_csv(hist_csv)

        hist_all = df_hist.copy()

        if 'RS_Score_On_Date' in hist_all.columns:
            hist_all['RS_Rating'] = hist_all['RS_Score_On_Date']
        if 'Sector_Rank_On_Date' in hist_all.columns:
            hist_all['Sector_Rank'] = hist_all['Sector_Rank_On_Date']
        if 'MarketCap_Cr' in hist_all.columns:
            hist_all['Market_Cap_Cr'] = hist_all['MarketCap_Cr']
        if 'Free_Float' in hist_all.columns:
            hist_all['Free_Float_Pct'] = hist_all['Free_Float']

        unique_dates = sorted(df_hist['Date'].unique(), reverse=True)
    else:
        df_hist = pd.DataFrame()
        hist_all = pd.DataFrame()
        unique_dates = []

    # Get last-updated timestamp from CSV file modification time
    last_updated = "Never"
    if os.path.exists(daily_csv):
        mod_time = os.path.getmtime(daily_csv)
        last_updated = datetime.fromtimestamp(mod_time).strftime("%d %b %Y, %I:%M %p")

    html_content = r"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Elite Screener Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #0b0d17;
                --surface: #151829;
                --surface-hover: #1e2240;
                --surface-alt: #1a1d33;
                --primary: #818cf8;
                --primary-dim: rgba(129,140,248,0.12);
                --accent: #a78bfa;
                --success: #34d399;
                --warning: #fbbf24;
                --danger: #f87171;
                --text-main: #f1f5f9;
                --text-muted: #94a3b8;
                --border: rgba(255, 255, 255, 0.06);
                --sidebar-width: 220px;
                --focus-panel-width: 260px;
                --topbar-height: 52px;
                --gold: #fbbf24;
            }
            * { box-sizing: border-box; }
            body {
                margin: 0; font-family: 'Inter', sans-serif;
                background-color: var(--bg); color: var(--text-main);
                display: flex; flex-direction: column;
                height: 100vh; overflow: hidden; font-size: 0.8rem;
            }

            /* ── Top Bar ── */
            .topbar {
                height: var(--topbar-height);
                background: linear-gradient(135deg, var(--surface) 0%, #1a1040 100%);
                border-bottom: 1px solid var(--border);
                display: flex; align-items: center; padding: 0 1.5rem;
                z-index: 1001; flex-shrink: 0;
            }
            .brand {
                font-size: 1.1rem; font-weight: 700;
                background: linear-gradient(135deg, #818cf8, #c084fc, #f0abfc);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                margin-right: 2rem; white-space: nowrap;
            }
            .top-tabs { display: flex; gap: 0.5rem; }
            .top-tab {
                padding: 0.4rem 1.2rem; border-radius: 6px; cursor: pointer;
                font-weight: 600; font-size: 0.78rem; color: var(--text-muted);
                transition: all 0.25s ease; background: transparent; border: none;
            }
            .top-tab:hover { background: rgba(255,255,255,0.06); color: var(--text-main); }
            .top-tab.active {
                background: var(--primary-dim); color: var(--primary);
                box-shadow: inset 0 0 0 1px rgba(129,140,248,0.3);
            }
            .topbar-right {
                margin-left: auto; display: flex; align-items: center; gap: 0.75rem;
            }
            .focus-toggle-btn {
                padding: 0.4rem 1rem; border-radius: 6px; cursor: pointer;
                font-weight: 600; font-size: 0.78rem; color: var(--gold);
                background: rgba(251,191,36,0.08); border: 1px solid rgba(251,191,36,0.2);
                transition: all 0.25s ease; display: flex; align-items: center; gap: 0.4rem;
            }
            .focus-toggle-btn:hover {
                background: rgba(251,191,36,0.15); border-color: rgba(251,191,36,0.4);
            }
            .focus-badge {
                background: var(--gold); color: #000; font-size: 0.65rem;
                padding: 0.1rem 0.4rem; border-radius: 99px; font-weight: 700;
            }

            /* ── Layout ── */
            .app-container { display: flex; flex: 1; overflow: hidden; }

            .module-container { display: none; width: 100%; height: 100%; }
            .module-container.active { display: flex; }

            /* ── Left Sidebar ── */
            .sidebar {
                width: var(--sidebar-width); min-width: var(--sidebar-width);
                background-color: var(--surface);
                border-right: 1px solid var(--border);
                display: flex; flex-direction: column;
                padding: 1rem 0.75rem;
                transition: all 0.3s ease; overflow-y: auto;
            }
            .sidebar.collapsed { width: 0; min-width: 0; padding: 0; overflow: hidden; border-right: none; }
            .sidebar-header {
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 1rem; padding: 0 0.5rem;
            }
            .sidebar-header span { font-weight: 700; font-size: 0.7rem; color: var(--text-muted); letter-spacing: 0.08em; text-transform: uppercase; }

            .date-picker { margin-bottom: 1.5rem; }
            .date-picker label {
                font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;
                letter-spacing: 0.05em; margin-bottom: 0.4rem; display: block; padding-left: 0.5rem;
            }
            select {
                width: 100%; padding: 0.6rem 0.75rem; font-size: 0.8rem; font-family: 'Inter', sans-serif;
                background-color: var(--bg); color: var(--text-main); border: 1px solid var(--border);
                border-radius: 6px; outline: none; cursor: pointer;
            }
            select:focus { border-color: var(--primary); }

            .nav-item {
                padding: 0.65rem 1rem; margin-bottom: 0.25rem; border-radius: 6px; cursor: pointer;
                font-weight: 500; font-size: 0.78rem; color: var(--text-muted);
                transition: all 0.2s ease; display: flex; align-items: center; gap: 0.6rem;
            }
            .nav-item:hover { background-color: rgba(255,255,255,0.04); color: var(--text-main); }
            .nav-item.active { background-color: var(--primary-dim); color: var(--primary); font-weight: 600; }
            .nav-count {
                margin-left: auto; background: rgba(255,255,255,0.06); color: var(--text-muted);
                font-size: 0.65rem; padding: 0.15rem 0.5rem; border-radius: 99px; font-weight: 600;
            }

            /* ── Right Focus Panel ── */
            .focus-panel {
                width: var(--focus-panel-width); min-width: var(--focus-panel-width);
                background-color: var(--surface);
                border-left: 1px solid var(--border);
                display: flex; flex-direction: column;
                transition: all 0.3s ease; overflow: hidden;
            }
            .focus-panel.collapsed { width: 0; min-width: 0; border-left: none; }
            .focus-panel-header {
                padding: 1rem; border-bottom: 1px solid var(--border);
                display: flex; justify-content: space-between; align-items: center;
            }
            .focus-panel-header h3 {
                margin: 0; font-size: 0.85rem; color: var(--gold);
                display: flex; align-items: center; gap: 0.4rem;
            }
            .focus-panel-actions {
                padding: 0.75rem 1rem; border-bottom: 1px solid var(--border);
                display: flex; gap: 0.4rem; flex-wrap: wrap;
            }
            .focus-export-btn {
                padding: 0.3rem 0.6rem; border-radius: 4px; cursor: pointer;
                font-size: 0.65rem; font-weight: 600; color: var(--text-muted);
                background: rgba(255,255,255,0.04); border: 1px solid var(--border);
                transition: all 0.2s; font-family: 'Inter', sans-serif;
            }
            .focus-export-btn:hover { background: rgba(255,255,255,0.08); color: var(--text-main); }
            .focus-list {
                flex: 1; overflow-y: auto; padding: 0.5rem;
            }
            .focus-item {
                display: flex; align-items: center; justify-content: space-between;
                padding: 0.5rem 0.75rem; margin-bottom: 0.25rem; border-radius: 6px;
                background: rgba(255,255,255,0.02); transition: background 0.2s;
            }
            .focus-item:hover { background: rgba(255,255,255,0.05); }
            .focus-item a {
                color: var(--primary); text-decoration: none; font-weight: 600; font-size: 0.78rem;
            }
            .focus-item a:hover { text-decoration: underline; }
            .focus-remove {
                background: none; border: none; color: var(--danger); cursor: pointer;
                font-size: 0.9rem; padding: 0.2rem; opacity: 0.5; transition: opacity 0.2s;
            }
            .focus-remove:hover { opacity: 1; }
            .focus-empty {
                padding: 2rem 1rem; text-align: center; color: var(--text-muted); font-size: 0.75rem;
            }

            /* ── Main Content ── */
            .main-content { flex: 1; overflow-y: auto; padding: 1.25rem 1.5rem; }
            .header-bar { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
            .toggle-btn {
                background: none; border: none; color: var(--text-muted); cursor: pointer;
                font-size: 1.1rem; padding: 0.4rem; border-radius: 4px;
                display: flex; align-items: center; justify-content: center;
            }
            .toggle-btn:hover { background: rgba(255, 255, 255, 0.08); color: var(--text-main); }

            .view-section { display: none; animation: fadeIn 0.3s ease; }
            .view-section.active { display: block; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

            .card {
                background: var(--surface); border-radius: 10px; padding: 1rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4); border: 1px solid var(--border);
            }
            .card-title {
                font-size: 0.95rem; font-weight: 600; margin-bottom: 0.75rem;
                display: flex; align-items: center; gap: 0.5rem;
            }

            /* ── Table ── */
            .table-toolbar {
                display: flex; align-items: center; justify-content: space-between;
                margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;
            }
            .export-group { display: flex; gap: 0.4rem; }
            .export-btn {
                padding: 0.35rem 0.7rem; border-radius: 5px; cursor: pointer;
                font-size: 0.68rem; font-weight: 600; color: var(--text-muted);
                background: rgba(255,255,255,0.04); border: 1px solid var(--border);
                transition: all 0.2s; display: flex; align-items: center; gap: 0.3rem;
                font-family: 'Inter', sans-serif;
            }
            .export-btn:hover { background: rgba(255,255,255,0.08); color: var(--text-main); border-color: rgba(255,255,255,0.12); }
            .stock-count { font-size: 0.7rem; color: var(--text-muted); font-weight: 500; }

            table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.75rem; }
            th, td { padding: 0.55rem 0.4rem; border-bottom: 1px solid var(--border); white-space: nowrap; }
            th {
                color: var(--text-muted); font-size: 0.65rem; text-transform: uppercase;
                letter-spacing: 0.04em; font-weight: 600; cursor: pointer; user-select: none;
                position: sticky; top: 0; background: var(--surface); z-index: 1;
            }
            th:hover { color: var(--text-main); }
            th:not(.th-star)::after { content: ' \21D5'; font-size: 0.7em; opacity: 0.4; }
            .th-star { width: 30px; cursor: default; }
            tr:hover { background-color: var(--surface-hover); }
            .symbol a { font-weight: 700; color: var(--primary); text-decoration: none; font-size: 0.78rem; }
            .symbol a:hover { text-decoration: underline; color: var(--accent); }
            .price-cell { font-weight: 500; color: var(--text-main); }
            .badge {
                padding: 0.2rem 0.5rem; border-radius: 99px; font-size: 0.62rem; font-weight: 600;
                background: var(--primary-dim); color: var(--primary);
            }
            .positive { color: var(--success); font-weight: 600; }
            .negative { color: var(--warning); font-weight: 600; }
            .neutral { color: var(--text-muted); }
            .hist-row.hidden { display: none !important; }

            /* ── Star Button ── */
            .star-cell { width: 30px; text-align: center; }
            .star-btn {
                background: none; border: none; cursor: pointer; font-size: 1rem;
                color: var(--text-muted); transition: all 0.2s; padding: 0; line-height: 1;
            }
            .star-btn:hover { color: var(--gold); transform: scale(1.2); }
            .star-btn.active { color: var(--gold); }

            /* ── Toast ── */
            .toast {
                position: fixed; bottom: 1.5rem; right: 1.5rem; padding: 0.6rem 1.2rem;
                background: var(--surface); border: 1px solid var(--border);
                border-radius: 8px; color: var(--success); font-size: 0.78rem; font-weight: 500;
                box-shadow: 0 8px 24px rgba(0,0,0,0.5); z-index: 9999;
                opacity: 0; transform: translateY(10px);
                transition: all 0.3s ease; pointer-events: none;
            }
            .toast.show { opacity: 1; transform: translateY(0); }

            /* ── Scrollbar ── */
            ::-webkit-scrollbar { width: 6px; height: 6px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
            ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

            /* ── Refresh Button ── */
            .refresh-btn {
                padding: 0.4rem 1rem; border-radius: 6px; cursor: pointer;
                font-weight: 600; font-size: 0.78rem; color: var(--success);
                background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.2);
                transition: all 0.25s ease; display: flex; align-items: center; gap: 0.4rem;
                font-family: 'Inter', sans-serif;
            }
            .refresh-btn:hover {
                background: rgba(52,211,153,0.15); border-color: rgba(52,211,153,0.4);
            }
            .refresh-btn.loading {
                color: var(--warning); background: rgba(251,191,36,0.08);
                border-color: rgba(251,191,36,0.2); pointer-events: none;
            }
            .refresh-btn .spinner {
                display: none; width: 14px; height: 14px;
                border: 2px solid rgba(251,191,36,0.3); border-top-color: var(--warning);
                border-radius: 50%; animation: spin 0.8s linear infinite;
            }
            .refresh-btn.loading .spinner { display: inline-block; }
            .refresh-btn.loading .refresh-icon { display: none; }
            @keyframes spin { to { transform: rotate(360deg); } }

            .last-updated {
                font-size: 0.68rem; color: var(--text-muted); font-weight: 400;
                display: flex; align-items: center; gap: 0.3rem;
            }
            .last-updated .dot {
                width: 6px; height: 6px; border-radius: 50%; display: inline-block;
            }
            .dot-fresh { background: var(--success); }
            .dot-stale { background: var(--warning); }

            /* ── Refresh Overlay ── */
            .refresh-overlay {
                display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(11,13,23,0.85); z-index: 9998;
                justify-content: center; align-items: center; flex-direction: column;
            }
            .refresh-overlay.active { display: flex; }
            .refresh-overlay-content {
                text-align: center; padding: 2rem;
            }
            .refresh-overlay h2 { color: var(--text-main); font-size: 1.2rem; margin: 1rem 0 0.5rem; }
            .refresh-overlay p { color: var(--text-muted); font-size: 0.8rem; max-width: 400px; }
            .refresh-overlay .big-spinner {
                width: 48px; height: 48px; border: 3px solid var(--border);
                border-top-color: var(--primary); border-radius: 50%;
                animation: spin 1s linear infinite; margin: 0 auto;
            }
            #refreshStatus { margin-top: 1rem; color: var(--text-muted); font-size: 0.75rem; }
        </style>
    </head>
    <body>

        <!-- Top Navigation -->
        <div class="topbar">
            <div class="brand">Elite Screener Pro</div>
            <div class="top-tabs">
                <button class="top-tab active" onclick="switchModule('daily', this)">📊 Daily Scanner</button>
                <button class="top-tab" onclick="switchModule('historical', this)">🕰️ Historical Engine</button>
            </div>
            <div class="topbar-right">
                <span class="last-updated" id="lastUpdated"></span>
                <button class="refresh-btn" id="refreshBtn" onclick="refreshData()" title="Re-fetch market data">
                    <span class="refresh-icon">🔄</span>
                    <span class="spinner"></span>
                    <span class="refresh-label">Refresh Data</span>
                </button>
                <button class="focus-toggle-btn" onclick="toggleFocusPanel()">
                    ⭐ Focus <span class="focus-badge" id="focusBadge">0</span>
                </button>
            </div>
        </div>

        <!-- Refresh Overlay -->
        <div class="refresh-overlay" id="refreshOverlay">
            <div class="refresh-overlay-content">
                <div class="big-spinner"></div>
                <h2>Refreshing Market Data...</h2>
                <p>Downloading latest prices for all stocks, running technical & fundamental scans. This takes 5-8 minutes.</p>
                <div id="refreshStatus">Starting...</div>
            </div>
        </div>

        <div class="app-container">

            <!-- ═══════════ DAILY MODULE ═══════════ -->
            <div id="daily-module" class="module-container active">
                <div class="sidebar" id="daily-sidebar">
                    <div class="sidebar-header">
                        <span>Categories</span>
                        <button class="toggle-btn" onclick="toggleSidebar('daily')" title="Close">✕</button>
                    </div>
    """

    bo_count = len(daily_breakouts) if not daily_breakouts.empty else 0
    wl_count = len(daily_watchlist) if not daily_watchlist.empty else 0
    uni_count = len(daily_universe) if not daily_universe.empty else 0

    html_content += f"""
                    <div class="nav-item active" onclick="switchView('daily-breakouts', this)">
                        <span>🚀</span> Breakouts <span class="nav-count">{bo_count}</span>
                    </div>
                    <div class="nav-item" onclick="switchView('daily-watchlist', this)">
                        <span>🎯</span> Watchlist <span class="nav-count">{wl_count}</span>
                    </div>
                    <div class="nav-item" onclick="switchView('daily-universe', this)">
                        <span>🌌</span> Full Universe <span class="nav-count">{uni_count}</span>
                    </div>
                </div>

                <div class="main-content">
                    <div class="header-bar">
                        <button class="toggle-btn" onclick="toggleSidebar('daily')" id="daily-openBtn" style="display:none; font-size:1.3rem;" title="Open Menu">☰</button>
                        <div>
                            <h1 style="margin:0; font-size:1.25rem;">Daily Market Overview</h1>
                            <p style="color:var(--text-muted); margin:0.15rem 0 0; font-size:0.72rem;">Live technical & fundamental scan</p>
                        </div>
                    </div>

                    <div id="daily-breakouts" class="view-section active">
                        <div class="card">
                            <div class="card-title">🚀 Top Breakouts (Crossed &gt;4% above 10 EMA today)</div>
    """
    html_content += generate_table(daily_breakouts, "dailyBreakoutsTable")
    html_content += """
                        </div>
                    </div>
                    <div id="daily-watchlist" class="view-section">
                        <div class="card">
                            <div class="card-title">🎯 Watchlist (Consolidating within ±4% of 10 EMA)</div>
    """
    html_content += generate_table(daily_watchlist, "dailyWatchlistTable")
    html_content += """
                        </div>
                    </div>
                    <div id="daily-universe" class="view-section">
                        <div class="card">
                            <div class="card-title">🌌 Full Universe (All qualifying stocks)</div>
    """
    html_content += generate_table(daily_universe, "dailyUniverseTable")
    html_content += """
                        </div>
                    </div>
                </div>
            </div>

            <!-- ═══════════ HISTORICAL MODULE ═══════════ -->
            <div id="historical-module" class="module-container">
                <div class="sidebar" id="hist-sidebar">
                    <div class="sidebar-header">
                        <span>Time Travel</span>
                        <button class="toggle-btn" onclick="toggleSidebar('hist')" title="Close">✕</button>
                    </div>
                    <div class="date-picker">
                        <label for="dateSelect">Select Date</label>
                        <select id="dateSelect" onchange="filterHistoricalDate()">
    """
    for d in unique_dates:
        html_content += f'<option value="{d}">{d}</option>\n'

    html_content += """
                        </select>
                    </div>
                    <div class="nav-item active" onclick="switchView('hist-breakouts', this)">
                        <span>🚀</span> Breakouts
                    </div>
                    <div class="nav-item" onclick="switchView('hist-watchlist', this)">
                        <span>🎯</span> Watchlist
                    </div>
                </div>

                <div class="main-content">
                    <div class="header-bar">
                        <button class="toggle-btn" onclick="toggleSidebar('hist')" id="hist-openBtn" style="display:none; font-size:1.3rem;" title="Open Menu">☰</button>
                        <div>
                            <h1 style="margin:0; font-size:1.25rem;" id="displayDate">Historical Data</h1>
                            <p style="color:var(--text-muted); margin:0.15rem 0 0; font-size:0.72rem;">Dynamically calculated for each historical trading day</p>
                        </div>
                    </div>

                    <div id="hist-breakouts" class="view-section active">
                        <div class="card">
                            <div class="card-title">🚀 Breakouts (Crossed &gt;4% above 10 EMA)</div>
    """

    # Split historical data into breakouts and watchlist
    if not hist_all.empty and 'Setup' in hist_all.columns:
        hist_breakouts_df = hist_all[hist_all['Setup'] == 'Breakout']
        hist_watchlist_df = hist_all[hist_all['Setup'] == 'Watchlist']
    else:
        hist_breakouts_df = hist_all
        hist_watchlist_df = pd.DataFrame()

    html_content += generate_table(hist_breakouts_df, "histBreakoutsTable", is_historical=True)
    html_content += """
                        </div>
                    </div>
                    <div id="hist-watchlist" class="view-section">
                        <div class="card">
                            <div class="card-title">🎯 Watchlist (Consolidating within ±4% of 10 EMA)</div>
    """
    html_content += generate_table(hist_watchlist_df, "histWatchlistTable", is_historical=True)
    html_content += r"""
                        </div>
                    </div>
                </div>
            </div>

            <!-- ═══════════ FOCUS PANEL (Right) ═══════════ -->
            <div class="focus-panel collapsed" id="focusPanel">
                <div class="focus-panel-header">
                    <h3>⭐ Stocks in Focus</h3>
                    <button class="toggle-btn" onclick="toggleFocusPanel()" title="Close">✕</button>
                </div>
                <div class="focus-panel-actions">
                    <button class="focus-export-btn" onclick="exportFocusCSV()">📄 CSV</button>
                    <button class="focus-export-btn" onclick="exportFocusTV()">📺 TradingView</button>
                    <button class="focus-export-btn" onclick="exportFocusText()">📋 Copy</button>
                    <button class="focus-export-btn" onclick="clearFocus()" style="color:var(--danger);">🗑️ Clear All</button>
                </div>
                <div class="focus-list" id="focusList">
                    <div class="focus-empty">Click ☆ on any stock to add it here</div>
                </div>
            </div>

        </div>

        <!-- Toast notification -->
        <div class="toast" id="toast"></div>

        <script>
            // ═══════════ Focus List (localStorage) ═══════════
            function getFocusList() {
                try { return JSON.parse(localStorage.getItem('eliteFocusList') || '[]'); }
                catch { return []; }
            }
            function saveFocusList(list) {
                localStorage.setItem('eliteFocusList', JSON.stringify(list));
            }

            function toggleFocus(symbol, btnEl) {
                let list = getFocusList();
                const idx = list.indexOf(symbol);
                if (idx > -1) {
                    list.splice(idx, 1);
                    if (btnEl) { btnEl.classList.remove('active'); btnEl.textContent = '☆'; }
                } else {
                    list.push(symbol);
                    if (btnEl) { btnEl.classList.add('active'); btnEl.textContent = '★'; }
                }
                saveFocusList(list);
                renderFocusPanel();
                updateStarButtons();
            }

            function renderFocusPanel() {
                const list = getFocusList();
                const container = document.getElementById('focusList');
                const badge = document.getElementById('focusBadge');
                badge.textContent = list.length;

                if (list.length === 0) {
                    container.innerHTML = '<div class="focus-empty">Click ☆ on any stock to add it here</div>';
                    return;
                }

                let html = '';
                list.forEach(sym => {
                    html += `<div class="focus-item">
                        <a href="https://in.tradingview.com/chart/?symbol=NSE:${sym}" target="_blank">${sym}</a>
                        <button class="focus-remove" onclick="toggleFocus('${sym}', null)" title="Remove">✕</button>
                    </div>`;
                });
                container.innerHTML = html;
            }

            function updateStarButtons() {
                const list = getFocusList();
                document.querySelectorAll('.star-btn').forEach(btn => {
                    const row = btn.closest('tr');
                    if (!row) return;
                    const sym = row.getAttribute('data-symbol');
                    if (list.includes(sym)) {
                        btn.classList.add('active');
                        btn.textContent = '★';
                    } else {
                        btn.classList.remove('active');
                        btn.textContent = '☆';
                    }
                });
            }

            function toggleFocusPanel() {
                document.getElementById('focusPanel').classList.toggle('collapsed');
            }

            function clearFocus() {
                if (confirm('Remove all stocks from focus list?')) {
                    saveFocusList([]);
                    renderFocusPanel();
                    updateStarButtons();
                }
            }

            // ═══════════ Export Functions ═══════════
            function showToast(msg) {
                const t = document.getElementById('toast');
                t.textContent = msg;
                t.classList.add('show');
                setTimeout(() => t.classList.remove('show'), 2000);
            }

            function getVisibleSymbols(tableId) {
                const table = document.getElementById(tableId);
                if (!table) return [];
                const rows = table.querySelectorAll('tbody tr');
                const symbols = [];
                rows.forEach(row => {
                    if (!row.classList.contains('hidden') && row.style.display !== 'none') {
                        const sym = row.getAttribute('data-symbol');
                        if (sym) symbols.push(sym);
                    }
                });
                return symbols;
            }

            function getVisibleTableData(tableId) {
                const table = document.getElementById(tableId);
                if (!table) return { headers: [], rows: [] };
                const headers = [];
                table.querySelectorAll('thead th').forEach((th, i) => {
                    if (i > 0) headers.push(th.textContent.replace(/[⇕↑↓]/g, '').trim());
                });
                const rows = [];
                table.querySelectorAll('tbody tr').forEach(row => {
                    if (row.classList.contains('hidden') || row.style.display === 'none') return;
                    const cells = [];
                    row.querySelectorAll('td').forEach((td, i) => {
                        if (i > 0) cells.push(td.textContent.trim());
                    });
                    if (cells.length) rows.push(cells);
                });
                return { headers, rows };
            }

            function exportCSV(tableId) {
                const data = getVisibleTableData(tableId);
                if (!data.rows.length) { showToast('No data to export'); return; }
                let csv = data.headers.join(',') + '\n';
                data.rows.forEach(r => {
                    csv += r.map(c => `"${c}"`).join(',') + '\n';
                });
                downloadFile(csv, 'screener_export.csv', 'text/csv');
                showToast('✓ CSV downloaded');
            }

            function exportTradingView(tableId) {
                const symbols = getVisibleSymbols(tableId);
                if (!symbols.length) { showToast('No data to export'); return; }
                const content = symbols.map(s => 'NSE:' + s).join('\n');
                downloadFile(content, 'tradingview_watchlist.txt', 'text/plain');
                showToast('✓ TradingView watchlist downloaded');
            }

            function exportText(tableId) {
                const symbols = getVisibleSymbols(tableId);
                if (!symbols.length) { showToast('No data to export'); return; }
                navigator.clipboard.writeText(symbols.join(', ')).then(() => {
                    showToast('✓ ' + symbols.length + ' symbols copied to clipboard');
                }).catch(() => {
                    // Fallback
                    const content = symbols.join(', ');
                    downloadFile(content, 'symbols.txt', 'text/plain');
                    showToast('✓ Symbols file downloaded');
                });
            }

            // Focus panel exports
            function exportFocusCSV() {
                const list = getFocusList();
                if (!list.length) { showToast('Focus list is empty'); return; }
                downloadFile('Symbol\n' + list.join('\n'), 'focus_list.csv', 'text/csv');
                showToast('✓ Focus list CSV downloaded');
            }
            function exportFocusTV() {
                const list = getFocusList();
                if (!list.length) { showToast('Focus list is empty'); return; }
                downloadFile(list.map(s => 'NSE:' + s).join('\n'), 'focus_tradingview.txt', 'text/plain');
                showToast('✓ Focus TradingView list downloaded');
            }
            function exportFocusText() {
                const list = getFocusList();
                if (!list.length) { showToast('Focus list is empty'); return; }
                navigator.clipboard.writeText(list.join(', ')).then(() => {
                    showToast('✓ ' + list.length + ' focus symbols copied');
                }).catch(() => {
                    downloadFile(list.join(', '), 'focus_symbols.txt', 'text/plain');
                    showToast('✓ Focus symbols downloaded');
                });
            }

            function downloadFile(content, filename, mimeType) {
                const blob = new Blob([content], { type: mimeType });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = filename;
                document.body.appendChild(a); a.click();
                document.body.removeChild(a); URL.revokeObjectURL(url);
            }

            // ═══════════ Module & View Switching ═══════════
            function switchModule(moduleName, tabEl) {
                document.querySelectorAll('.top-tab').forEach(t => t.classList.remove('active'));
                tabEl.classList.add('active');
                document.querySelectorAll('.module-container').forEach(m => m.classList.remove('active'));
                document.getElementById(moduleName + '-module').classList.add('active');
                if (moduleName === 'historical') filterHistoricalDate();
                updateStarButtons();
            }

            function switchView(viewId, element) {
                const sidebar = element.closest('.sidebar');
                sidebar.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                element.classList.add('active');

                const module = element.closest('.module-container') || element.closest('.app-container');
                const mainContent = module.querySelector('.main-content');
                mainContent.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
                document.getElementById(viewId).classList.add('active');
                updateStarButtons();
            }

            // ═══════════ Sidebar Toggle ═══════════
            function toggleSidebar(prefix) {
                const sidebar = document.getElementById(prefix + '-sidebar');
                const openBtn = document.getElementById(prefix + '-openBtn');
                sidebar.classList.toggle('collapsed');
                openBtn.style.display = sidebar.classList.contains('collapsed') ? 'flex' : 'none';
            }

            // ═══════════ Historical Date Filter ═══════════
            function filterHistoricalDate() {
                const select = document.getElementById('dateSelect');
                if (!select || select.options.length === 0) return;
                const selectedDate = select.value;
                document.getElementById('displayDate').textContent = 'Data for ' + selectedDate;
                document.querySelectorAll('.hist-row').forEach(row => {
                    row.classList.toggle('hidden', row.getAttribute('data-date') !== selectedDate);
                });
                updateStarButtons();
            }

            // ═══════════ Sorting ═══════════
            function sortTable(tableId, n) {
                const table = document.getElementById(tableId);
                let switching = true, dir = 'asc', switchcount = 0;
                while (switching) {
                    switching = false;
                    const rows = table.rows;
                    for (let i = 1; i < rows.length - 1; i++) {
                        let shouldSwitch = false;
                        const x = rows[i].getElementsByTagName('TD')[n];
                        const y = rows[i + 1].getElementsByTagName('TD')[n];
                        let xc = (x.textContent || x.innerText).trim();
                        let yc = (y.textContent || y.innerText).trim();

                        if (xc === '-' || xc === 'N/A') xc = dir === 'asc' ? '999999' : '-999999';
                        if (yc === '-' || yc === 'N/A') yc = dir === 'asc' ? '999999' : '-999999';

                        const xv = parseFloat(xc.replace(/[^0-9.\-]+/g, ''));
                        const yv = parseFloat(yc.replace(/[^0-9.\-]+/g, ''));
                        const isNum = !isNaN(xv) && !isNaN(yv);

                        if (dir === 'asc') {
                            if (isNum ? xv > yv : xc.toLowerCase() > yc.toLowerCase()) { shouldSwitch = true; break; }
                        } else {
                            if (isNum ? xv < yv : xc.toLowerCase() < yc.toLowerCase()) { shouldSwitch = true; break; }
                        }
                    }
                    if (shouldSwitch) {
                        rows[rows.length - 1].parentNode.insertBefore(rows[switchcount + 1 > 0 ? rows.length - 1 : 1], rows[1]);
                        // Standard bubble sort swap
                        const swapRow = table.rows;
                        for (let i = 1; i < swapRow.length - 1; i++) {
                            const x2 = swapRow[i].getElementsByTagName('TD')[n];
                            const y2 = swapRow[i + 1].getElementsByTagName('TD')[n];
                            let xc2 = (x2.textContent || '').trim();
                            let yc2 = (y2.textContent || '').trim();
                            if (xc2 === '-' || xc2 === 'N/A') xc2 = dir === 'asc' ? '999999' : '-999999';
                            if (yc2 === '-' || yc2 === 'N/A') yc2 = dir === 'asc' ? '999999' : '-999999';
                            const xv2 = parseFloat(xc2.replace(/[^0-9.\-]+/g, ''));
                            const yv2 = parseFloat(yc2.replace(/[^0-9.\-]+/g, ''));
                            const isNum2 = !isNaN(xv2) && !isNaN(yv2);
                            let doSwap = false;
                            if (dir === 'asc') { doSwap = isNum2 ? xv2 > yv2 : xc2.toLowerCase() > yc2.toLowerCase(); }
                            else { doSwap = isNum2 ? xv2 < yv2 : xc2.toLowerCase() < yc2.toLowerCase(); }
                            if (doSwap) {
                                swapRow[i].parentNode.insertBefore(swapRow[i + 1], swapRow[i]);
                            }
                        }
                        switching = false; // We did a full pass
                        switchcount++;
                    } else {
                        if (switchcount === 0 && dir === 'asc') { dir = 'desc'; switching = true; }
                    }
                }
            }

            // Better sort using Array.sort
            function sortTable(tableId, colIdx) {
                const table = document.getElementById(tableId);
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));

                // Determine current sort direction
                const th = table.querySelectorAll('th')[colIdx];
                const currentDir = th.getAttribute('data-sort') || 'none';
                const newDir = currentDir === 'asc' ? 'desc' : 'asc';

                // Reset all headers
                table.querySelectorAll('th').forEach(h => h.removeAttribute('data-sort'));
                th.setAttribute('data-sort', newDir);

                rows.sort((a, b) => {
                    let av = (a.cells[colIdx]?.textContent || '').trim();
                    let bv = (b.cells[colIdx]?.textContent || '').trim();

                    if (av === '-' || av === 'N/A' || av === '') av = newDir === 'asc' ? '\uffff' : '\u0000';
                    if (bv === '-' || bv === 'N/A' || bv === '') bv = newDir === 'asc' ? '\uffff' : '\u0000';

                    const an = parseFloat(av.replace(/[^0-9.\-]+/g, ''));
                    const bn = parseFloat(bv.replace(/[^0-9.\-]+/g, ''));

                    if (!isNaN(an) && !isNaN(bn)) {
                        return newDir === 'asc' ? an - bn : bn - an;
                    }
                    return newDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
                });

                rows.forEach(r => tbody.appendChild(r));
            }

            // ═══════════ Stock Counts ═══════════
            function updateCounts() {
                document.querySelectorAll('table').forEach(table => {
                    const id = table.id;
                    const countEl = document.getElementById('count-' + id);
                    if (countEl) {
                        const visible = table.querySelectorAll('tbody tr:not(.hidden)').length;
                        countEl.textContent = visible + ' stocks';
                    }
                });
            }

            // ═══════════ Refresh Data ═══════════
            let refreshPolling = null;

            function refreshData() {
                const btn = document.getElementById('refreshBtn');
                const overlay = document.getElementById('refreshOverlay');
                const statusEl = document.getElementById('refreshStatus');

                // Try server API first
                fetch('/api/refresh').then(r => r.json()).then(data => {
                    if (data.status === 'already_running') {
                        statusEl.textContent = data.message;
                    }
                    btn.classList.add('loading');
                    btn.querySelector('.refresh-label').textContent = 'Refreshing...';
                    overlay.classList.add('active');
                    statusEl.textContent = data.message || 'Starting...';

                    // Poll for status
                    if (refreshPolling) clearInterval(refreshPolling);
                    refreshPolling = setInterval(() => {
                        fetch('/api/status').then(r => r.json()).then(s => {
                            statusEl.textContent = s.message;
                            if (!s.running) {
                                clearInterval(refreshPolling);
                                refreshPolling = null;
                                statusEl.textContent = 'Done! Reloading page...';
                                setTimeout(() => window.location.reload(), 1500);
                            }
                        }).catch(() => {});
                    }, 3000);
                }).catch(() => {
                    // Not running via server.py — show instructions
                    overlay.classList.add('active');
                    statusEl.innerHTML = '<div style="color:var(--warning); font-size:0.85rem; line-height:1.6;">' +
                        '<strong>Server not running!</strong><br><br>' +
                        'To use auto-refresh, run this in your terminal:<br>' +
                        '<code style="background:rgba(255,255,255,0.08); padding:0.3rem 0.6rem; border-radius:4px; font-size:0.8rem;">python server.py</code><br><br>' +
                        'Then open <code style="background:rgba(255,255,255,0.08); padding:0.3rem 0.6rem; border-radius:4px; font-size:0.8rem;">http://localhost:8080</code><br><br>' +
                        '<button onclick="document.getElementById(\'refreshOverlay\').classList.remove(\'active\')" ' +
                        'style="padding:0.5rem 1.5rem; border-radius:6px; border:1px solid var(--border); ' +
                        'background:var(--surface-hover); color:var(--text-main); cursor:pointer; font-family:Inter,sans-serif; font-weight:600;">Close</button></div>';
                });
            }

            // ═══════════ Init ═══════════
            document.addEventListener('DOMContentLoaded', () => {
                renderFocusPanel();
                updateStarButtons();
                filterHistoricalDate();
                updateCounts();
            });
        </script>
    </body>
    </html>
    """

    # Inject the last-updated timestamp into the HTML
    html_content = html_content.replace(
        '<span class="last-updated" id="lastUpdated"></span>',
        f'<span class="last-updated" id="lastUpdated"><span class="dot dot-fresh"></span> Updated: {last_updated}</span>'
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("index.html generated successfully.")

if __name__ == "__main__":
    generate_dashboard()
