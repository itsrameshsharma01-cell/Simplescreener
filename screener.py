import pandas as pd
import yfinance as yf
import requests
import io
import time
import numpy as np
from datetime import datetime
import warnings
import os

# Suppress pandas warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

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
    # Adding Nifty 50 for RS baseline
    symbols.append("^NSEI")
    
    if not symbols:
        print("No symbols found. Exiting.")
        return

    print(f"Downloading 1-year historical data for {len(symbols)} symbols. This may take a few minutes...")
    # period="1y" ensures we have enough data for 200 EMA and 52-week low
    data = yf.download(symbols, period="1y", group_by="ticker", auto_adjust=False, threads=True)
    
    print(f"Download complete in {time.time() - start_time:.2f} seconds. Processing technicals...")
    
    passed_technicals = []
    
    # Process Nifty 50 baseline
    if "^NSEI" in data:
        nifty_df = data["^NSEI"].dropna()
        if len(nifty_df) >= 66:
            nifty_3m_return = ((nifty_df['Close'].iloc[-1] / nifty_df['Close'].iloc[-66]) - 1) * 100
        else:
            nifty_3m_return = 0
    else:
        nifty_3m_return = 0

    for symbol in symbols:
        if symbol == "^NSEI":
            continue
            
        try:
            if symbol not in data:
                continue
                
            df = data[symbol]
            if isinstance(df, pd.DataFrame) and 'Close' in df.columns:
                df = df.dropna(subset=['Close'])
                
                if len(df) < 200:
                    continue  # Not enough data for 200 EMA
                
                close = df['Close']
                
                # Circuit limit proxy: Max daily move over last 30 days
                daily_ret = (close / close.shift(1) - 1).abs()
                max_daily_move = daily_ret.rolling(30).max().iloc[-1] * 100
                if max_daily_move <= 5.1:
                    continue # Exclude 5% circuit limit stocks
                
                # EMAs
                ema_10 = close.ewm(span=10, adjust=False).mean().iloc[-1]
                ema_20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
                ema_50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
                ema_200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
                
                current_price = close.iloc[-1]
                
                # 52w low
                low_52w = df['Low'].rolling(window=250, min_periods=100).min().iloc[-1]
                
                # Momentum
                ret_3m = ((current_price / close.iloc[-66]) - 1) * 100 if len(close) >= 66 else 0
                ret_1w = ((current_price / close.iloc[-5]) - 1) * 100 if len(close) >= 5 else 0
                
                # Technical Filters
                cond_emas = (current_price > ema_20) and (current_price > ema_50) and (current_price > ema_200)
                cond_52w = current_price >= (low_52w * 1.70)
                cond_momentum = (ret_3m >= 30) or (ret_1w >= 19)
                
                if cond_emas and cond_52w and cond_momentum:
                    # Setup detection
                    dist_to_10ema = abs((current_price / ema_10) - 1) * 100
                    is_watchlist = dist_to_10ema <= 4.0
                    
                    # Refined Breakout: Was in watchlist yesterday, broke out today
                    dist_to_10ema_yest = abs((close.iloc[-2] / close.ewm(span=10, adjust=False).mean().iloc[-2]) - 1) * 100
                    is_breakout = (dist_to_10ema_yest <= 4.0) and (current_price > (ema_10 * 1.04))
                    
                    passed_technicals.append({
                        'Symbol': symbol,
                        'Price': round(current_price, 2),
                        '3M_Ret': round(ret_3m, 2),
                        '1W_Ret': round(ret_1w, 2),
                        'Dist_10EMA': round((current_price / ema_10 - 1)*100, 2),
                        'Is_Watchlist': is_watchlist,
                        'Is_Breakout': is_breakout
                    })
        except Exception as e:
            pass 

    print(f"{len(passed_technicals)} stocks passed the strict technical and circuit limit filters.")
    
    if not passed_technicals:
        print("No stocks passed the filters today.")
        return

    print("Fetching fundamental data (Market Cap, Sector, QoQ EPS/Sales, Free Float) to apply final filters...")
    final_stocks = []
    
    for i, stock in enumerate(passed_technicals):
        symbol = stock['Symbol']
        print(f"[{i+1}/{len(passed_technicals)}] Fetching fundamentals for {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Market Cap filter (2000 Cr to 80000 Cr)
            mcap = info.get('marketCap', 0)
            mcap_cr = mcap / 10000000 if mcap else 0
            
            if 2000 <= mcap_cr <= 80000:
                sector = info.get('sector', 'Unknown')
                rs_rating = stock['3M_Ret'] - nifty_3m_return
                
                # Debt/Equity Ratio
                debt_eq = info.get('debtToEquity')
                debt_ratio = round(debt_eq / 100, 2) if isinstance(debt_eq, (int, float)) else "N/A"
                
                # Free Float %
                f_shares = info.get('floatShares')
                o_shares = info.get('sharesOutstanding')
                free_float = round((f_shares / o_shares) * 100, 1) if (f_shares and o_shares) else "N/A"
                
                qoq_sales = "N/A"
                qoq_eps = "N/A"
                
                # QoQ Sales
                q_fin = ticker.quarterly_financials
                if not q_fin.empty and 'Total Revenue' in q_fin.index:
                    revs = q_fin.loc['Total Revenue']
                    if len(revs) >= 2 and pd.notna(revs.iloc[0]) and pd.notna(revs.iloc[1]) and revs.iloc[1] > 0:
                        qoq_sales = round(((revs.iloc[0] / revs.iloc[1]) - 1) * 100, 1)
                        
                # QoQ EPS
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
                
                stock.update({
                    'MarketCap_Cr': round(mcap_cr, 2),
                    'Sector': sector,
                    'RS_Score': round(rs_rating, 2),
                    'Debt_Equity': debt_ratio,
                    'Free_Float': free_float,
                    'QoQ_Sales': qoq_sales,
                    'QoQ_EPS': qoq_eps
                })
                final_stocks.append(stock)
        except Exception as e:
            pass

    print(f"\nFinal processing complete. {len(final_stocks)} stocks made the final cut.")
    
    df_final = pd.DataFrame(final_stocks)
    if not df_final.empty:
        df_final = df_final.sort_values(by='RS_Score', ascending=False)
        
        sector_rs = df_final.groupby('Sector')['RS_Score'].mean().sort_values(ascending=False)
        df_final['Sector_Rank'] = df_final['Sector'].map(lambda x: sector_rs.index.get_loc(x) + 1 if x in sector_rs else 99)
        
        df_final = df_final.sort_values(by=['Sector_Rank', 'RS_Score'], ascending=[True, False])
        
        df_final.to_csv("daily_screener_results.csv", index=False)
        print("\nFull results saved to daily_screener_results.csv")
        
        os.system("python generate_dashboard.py")

if __name__ == "__main__":
    main()
