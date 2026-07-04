import pandas as pd
import yfinance as yf
import requests
import io
import time
import numpy as np
from datetime import datetime
import warnings
import os

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

def get_nse_symbols():
    print("Fetching NSE active equities list...")
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    try:
        response = requests.get(url, headers=headers)
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = df.columns.str.strip()
        df = df[df['SERIES'] == 'EQ']
        return [f"{s}.NS" for s in df['SYMBOL'].tolist()]
    except Exception as e:
        print(f"Error fetching NSE symbols: {e}")
        return []

def main():
    start_time = time.time()
    
    symbols = get_nse_symbols()
    if "^NSEI" not in symbols:
        symbols.append("^NSEI")
        
    if not symbols:
        print("No symbols found. Exiting.")
        return

    print(f"Downloading 1-year historical data for {len(symbols)} symbols...")
    data = yf.download(symbols, period="1y", group_by="ticker", auto_adjust=False, threads=True)
    print(f"Download complete in {time.time() - start_time:.2f} seconds. Vectorizing technicals...")

    close_dict = {}
    valid_universe_dict = {}
    dist_10ema_dict = {}
    is_watchlist_dict = {}
    is_breakout_dict = {}
    ret_3m_dict = {}
    
    for sym in symbols:
        if sym in data and isinstance(data[sym], pd.DataFrame) and 'Close' in data[sym].columns:
            df = data[sym].dropna(subset=['Close'])
            if len(df) < 200:
                continue
                
            close = df['Close']
            low = df['Low']
            
            # Circuit limit proxy: Max daily move over last 30 days
            daily_ret = (close / close.shift(1) - 1).abs()
            max_daily_move_30d = daily_ret.rolling(window=30).max()
            
            ema_10 = close.ewm(span=10, adjust=False).mean()
            ema_20 = close.ewm(span=20, adjust=False).mean()
            ema_50 = close.ewm(span=50, adjust=False).mean()
            ema_200 = close.ewm(span=200, adjust=False).mean()
            
            low_52w = low.rolling(window=250, min_periods=100).min()
            
            ret_3m_sym = (close / close.shift(66) - 1) * 100
            ret_1w = (close / close.shift(5) - 1) * 100
            
            cond_emas = (close > ema_20) & (close > ema_50) & (close > ema_200)
            cond_52w = close >= (low_52w * 1.70)
            cond_mom = (ret_3m_sym >= 30) | (ret_1w >= 19)
            cond_circuit = max_daily_move_30d > 0.051
            
            valid = cond_emas & cond_52w & cond_mom & cond_circuit
            
            dist = (close / ema_10 - 1) * 100
            is_wl = dist.abs() <= 4.0
            is_bo = (is_wl.shift(1) == True) & (dist > 4.0)
            
            close_dict[sym] = close
            valid_universe_dict[sym] = valid
            dist_10ema_dict[sym] = dist
            is_watchlist_dict[sym] = is_wl
            is_breakout_dict[sym] = is_bo
            ret_3m_dict[sym] = ret_3m_sym

    close_df = pd.DataFrame(close_dict)
    valid_universe_df = pd.DataFrame(valid_universe_dict).fillna(False)
    dist_10ema = pd.DataFrame(dist_10ema_dict)
    is_watchlist = pd.DataFrame(is_watchlist_dict).fillna(False)
    is_breakout = pd.DataFrame(is_breakout_dict).fillna(False)
    ret_3m = pd.DataFrame(ret_3m_dict)

    lookback_days = min(60, len(valid_universe_df))
    valid_universe_60d = valid_universe_df.iloc[-lookback_days:]

    symbols_to_fetch = valid_universe_60d.columns[valid_universe_60d.any()].tolist()
    if "^NSEI" in symbols_to_fetch:
        symbols_to_fetch.remove("^NSEI")

    print(f"{len(symbols_to_fetch)} unique stocks met the technical criteria at some point in the last 3 months.")
    print("Fetching fundamental data (QoQ metrics, Float, Sectors) for this reduced universe...")
    
    fundamentals = {}
    valid_final_symbols = []
    
    for i, sym in enumerate(symbols_to_fetch):
        print(f"[{i+1}/{len(symbols_to_fetch)}] Fundamentals for {sym}...")
        try:
            ticker = yf.Ticker(sym)
            info = ticker.info
            mcap = info.get('marketCap', 0)
            mcap_cr = mcap / 10000000 if mcap else 0
            
            if 2000 <= mcap_cr <= 80000:
                debt_eq = info.get('debtToEquity')
                debt_ratio = round(debt_eq / 100, 2) if isinstance(debt_eq, (int, float)) else "N/A"
                
                f_shares = info.get('floatShares')
                o_shares = info.get('sharesOutstanding')
                free_float = round((f_shares / o_shares) * 100, 1) if (f_shares and o_shares) else "N/A"
                
                qoq_sales = "N/A"
                qoq_eps = "N/A"
                
                q_fin = ticker.quarterly_financials
                if not q_fin.empty and 'Total Revenue' in q_fin.index:
                    revs = q_fin.loc['Total Revenue']
                    if len(revs) >= 2 and pd.notna(revs.iloc[0]) and pd.notna(revs.iloc[1]) and revs.iloc[1] > 0:
                        qoq_sales = round(((revs.iloc[0] / revs.iloc[1]) - 1) * 100, 1)
                        
                q_inc = ticker.quarterly_income_stmt
                if not q_inc.empty:
                    if 'Diluted EPS' in q_inc.index:
                        eps = q_inc.loc['Diluted EPS']
                        if len(eps) >= 2 and pd.notna(eps.iloc[0]) and pd.notna(eps.iloc[1]) and eps.iloc[1] > 0:
                            qoq_eps = round(((eps.iloc[0] / eps.iloc[1]) - 1) * 100, 1)
                    elif 'Net Income' in q_inc.index:
                        ni = q_inc.loc['Net Income']
                        if len(ni) >= 2 and pd.notna(ni.iloc[0]) and pd.notna(ni.iloc[1]) and ni.iloc[1] > 0:
                            qoq_eps = round(((ni.iloc[0] / ni.iloc[1]) - 1) * 100, 1)

                fundamentals[sym] = {
                    'Sector': info.get('sector', 'Unknown'),
                    'MarketCap_Cr': round(mcap_cr, 2),
                    'Debt_Equity': debt_ratio,
                    'Free_Float': free_float,
                    'QoQ_Sales': qoq_sales,
                    'QoQ_EPS': qoq_eps
                }
                valid_final_symbols.append(sym)
        except Exception:
            continue

    print(f"{len(valid_final_symbols)} stocks passed the fundamental Market Cap filter.")

    events = []
    dates = close_df.index[-lookback_days:]
    
    if "^NSEI" in ret_3m.columns:
        nifty_3m_df = ret_3m["^NSEI"]
    else:
        nifty_3m_df = pd.Series(0, index=ret_3m.index)

    print("Generating date-wise historical events...")
    
    sector_daily_rs = {}
    for date in dates:
        sector_rs_sums = {}
        sector_counts = {}
        for sym in valid_final_symbols:
            if valid_universe_df.loc[date, sym]:
                sec = fundamentals[sym]['Sector']
                rs = ret_3m.loc[date, sym] - nifty_3m_df.loc[date]
                if not np.isnan(rs):
                    sector_rs_sums[sec] = sector_rs_sums.get(sec, 0) + rs
                    sector_counts[sec] = sector_counts.get(sec, 0) + 1
        
        avg_rs = {sec: sector_rs_sums[sec]/sector_counts[sec] for sec in sector_rs_sums}
        ranked_sectors = sorted(avg_rs.items(), key=lambda item: item[1], reverse=True)
        sector_daily_rs[date] = {sec: rank+1 for rank, (sec, _) in enumerate(ranked_sectors)}

    for date in dates:
        date_str = date.strftime('%Y-%m-%d')
        sector_ranks_today = sector_daily_rs.get(date, {})
        
        for sym in valid_final_symbols:
            if not valid_universe_df.loc[date, sym]:
                continue
                
            trigger_watchlist = is_watchlist.loc[date, sym]
            trigger_breakout = is_breakout.loc[date, sym]
            
            if trigger_watchlist or trigger_breakout:
                rs_score = ret_3m.loc[date, sym] - nifty_3m_df.loc[date]
                sec = fundamentals[sym]['Sector']
                sec_rank = sector_ranks_today.get(sec, 99)
                
                events.append({
                    'Date': date_str,
                    'Symbol': sym,
                    'Sector': sec,
                    'Sector_Rank_On_Date': sec_rank,
                    'RS_Score_On_Date': round(rs_score, 2),
                    'Setup': 'Breakout' if trigger_breakout else 'Watchlist',
                    'Price': round(close_df.loc[date, sym], 2),
                    'Dist_10EMA': round(dist_10ema.loc[date, sym], 2),
                    'MarketCap_Cr': fundamentals[sym]['MarketCap_Cr'],
                    'Debt_Equity': fundamentals[sym]['Debt_Equity'],
                    'Free_Float': fundamentals[sym]['Free_Float'],
                    'QoQ_Sales': fundamentals[sym]['QoQ_Sales'],
                    'QoQ_EPS': fundamentals[sym]['QoQ_EPS']
                })

    final_df = pd.DataFrame(events)
    if not final_df.empty:
        final_df = final_df.sort_values(by=['Date', 'Sector_Rank_On_Date', 'RS_Score_On_Date'], ascending=[False, True, False])
        final_df.to_csv("historical_screener_results.csv", index=False)
        print(f"\nSuccessfully generated {len(final_df)} historical setups across {lookback_days} days!")
        print("Saved to historical_screener_results.csv")
        
        os.system("python generate_dashboard.py")
    else:
        print("No historical setups found in the last 3 months.")

if __name__ == "__main__":
    main()
