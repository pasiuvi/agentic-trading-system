# eda/analysis.py
# PURPOSE: Load stock data, clean it, add technical indicators, create charts
# USAGE:   python eda/analysis.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from ta.trend   import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

os.makedirs('output', exist_ok=True)


# ── Function 1: Load CSV from local data folder ───────────────────────────
def load_data(symbol):
    """
    Loads the CSV file saved by fetch_data.py.
    Returns a cleaned DataFrame.
    """
    path = f'data/{symbol}_data.csv'
    if not os.path.exists(path):
        print(f'  File not found: {path} — run fetch_data.py first')
        return None

    df = pd.read_csv(path)

    # Convert Date column to proper datetime type
    df['Date'] = pd.to_datetime(df['Date'], utc=True, errors='coerce')
    df.dropna(subset=['Date'], inplace=True)   # remove rows with bad dates
    df.sort_values('Date', inplace=True)        # sort oldest first
    df.reset_index(drop=True, inplace=True)

    # Fill small gaps in price data (forward-fill method)
    price_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    df[price_cols] = df[price_cols].ffill()

    # Remove any remaining rows with missing prices
    df.dropna(subset=['Close'], inplace=True)

    print(f'  Loaded {len(df)} rows for {symbol}')
    return df


# ── Function 2: Add all technical indicators ──────────────────────────────
def add_indicators(df):
    """
    Adds these columns to the DataFrame:
    MA_20, MA_50  = Moving Averages (trend direction)
    EMA_12        = Exponential Moving Average
    RSI           = Relative Strength Index (0-100, overbought/oversold)
    MACD          = Moving Average Convergence Divergence
    MACD_Signal   = MACD signal line
    BB_Upper/Lower= Bollinger Bands (volatility channel)
    Daily_Return  = percentage change each day
    Volatility    = rolling standard deviation of returns
    Signal        = 1=BUY, -1=SELL, 0=HOLD
    """
    close = df['Close']

    # Moving Averages
    df['MA_20'] = SMAIndicator(close, window=20).sma_indicator()
    df['MA_50'] = SMAIndicator(close, window=50).sma_indicator()
    df['EMA_12'] = EMAIndicator(close, window=12).ema_indicator()

    # RSI
    df['RSI'] = RSIIndicator(close, window=14).rsi()

    # MACD
    macd_obj = MACD(close)
    df['MACD']        = macd_obj.macd()
    df['MACD_Signal'] = macd_obj.macd_signal()
    df['MACD_Hist']   = macd_obj.macd_diff()   # histogram

    # Bollinger Bands
    bb = BollingerBands(close, window=20, window_dev=2)
    df['BB_Upper'] = bb.bollinger_hband()
    df['BB_Middle'] = bb.bollinger_mavg()
    df['BB_Lower'] = bb.bollinger_lband()

    # Daily return and rolling volatility
    df['Daily_Return'] = close.pct_change()
    df['Volatility']   = df['Daily_Return'].rolling(window=20).std()

    # ── Simple Buy/Sell signals ────────────────────────────────────────
    # Rule: RSI below 30 AND price above MA50 = oversold in uptrend → BUY
    # Rule: RSI above 70 AND price below MA50 = overbought in downtrend → SELL
    df['Signal'] = 0  # default: HOLD
    df.loc[
        (df['RSI'] < 30) & (df['Close'] > df['MA_50']),
        'Signal'] = 1   # BUY
    df.loc[
        (df['RSI'] > 70) & (df['Close'] < df['MA_50']),
        'Signal'] = -1  # SELL

    # Remove rows where indicators couldn't be calculated yet
    df.dropna(subset=['MA_50', 'RSI', 'MACD'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    print(f'  Added indicators. Signals: BUY={sum(df.Signal==1)}, SELL={sum(df.Signal==-1)}')
    return df


# ── Function 3: Create and save charts ───────────────────────────────────
def plot_analysis(df, symbol):
    """Creates a 3-panel chart: Price+MAs, RSI, MACD. Saves as PNG."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(f'{symbol} — Technical Analysis', fontsize=14, fontweight='bold')

    # Panel 1: Price and Moving Averages
    ax1 = axes[0]
    ax1.plot(df['Date'], df['Close'], label='Close Price', color='#1F4E79', linewidth=1.5)
    ax1.plot(df['Date'], df['MA_20'], label='MA 20', color='orange', alpha=0.8, linewidth=1)
    ax1.plot(df['Date'], df['MA_50'], label='MA 50', color='red', alpha=0.8, linewidth=1)
    ax1.fill_between(df['Date'], df['BB_Upper'], df['BB_Lower'], alpha=0.1, color='blue', label='Bollinger Bands')
    # Mark BUY signals with green arrows
    buys  = df[df['Signal'] ==  1]
    sells = df[df['Signal'] == -1]
    ax1.scatter(buys['Date'],  buys['Close'],  marker='^', color='green', s=80, label='BUY',  zorder=5)
    ax1.scatter(sells['Date'], sells['Close'], marker='v', color='red',   s=80, label='SELL', zorder=5)
    ax1.legend(fontsize=8); ax1.set_ylabel('Price (USD)'); ax1.grid(alpha=0.3)

    # Panel 2: RSI
    ax2 = axes[1]
    ax2.plot(df['Date'], df['RSI'], color='purple', linewidth=1.2)
    ax2.axhline(70, color='red',   linestyle='--', alpha=0.6, label='Overbought (70)')
    ax2.axhline(30, color='green', linestyle='--', alpha=0.6, label='Oversold (30)')
    ax2.fill_between(df['Date'], df['RSI'], 70, where=(df['RSI']>=70), alpha=0.2, color='red')
    ax2.fill_between(df['Date'], df['RSI'], 30, where=(df['RSI']<=30), alpha=0.2, color='green')
    ax2.set_ylabel('RSI'); ax2.set_ylim(0, 100); ax2.legend(fontsize=8); ax2.grid(alpha=0.3)

    # Panel 3: MACD
    ax3 = axes[2]
    ax3.plot(df['Date'], df['MACD'],        label='MACD',   color='blue', linewidth=1.2)
    ax3.plot(df['Date'], df['MACD_Signal'],  label='Signal', color='red',  linewidth=1.2)
    ax3.bar(df['Date'],  df['MACD_Hist'], color=df['MACD_Hist'].apply(
            lambda x: 'green' if x>=0 else 'red'), alpha=0.4, label='Histogram')
    ax3.axhline(0, color='black', linewidth=0.5)
    ax3.set_ylabel('MACD'); ax3.legend(fontsize=8); ax3.grid(alpha=0.3)

    plt.tight_layout()
    save_path = f'output/{symbol}_analysis.png'
    plt.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f'  Chart saved: {save_path}')


# ── Function 4: Cluster assets by behaviour ───────────────────────────────
def cluster_assets(symbols, n_clusters=3):
    """
    Groups stocks into clusters based on average return, volatility and RSI.
    This helps find which assets behave similarly.
    """
    print('\n  Clustering assets...')
    feature_rows = []
    valid_symbols = []

    for symbol in symbols:
        df = load_data(symbol)
        if df is None: continue
        df = add_indicators(df)
        avg_return = df['Daily_Return'].mean()
        avg_vol    = df['Volatility'].mean()
        avg_rsi    = df['RSI'].mean()
        feature_rows.append([avg_return, avg_vol, avg_rsi])
        valid_symbols.append(symbol)

    if len(valid_symbols) < 2:
        print('  Not enough data for clustering')
        return

    scaler = StandardScaler()
    X = scaler.fit_transform(feature_rows)

    n = min(n_clusters, len(valid_symbols))
    kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    print('  Asset Clusters:')
    for sym, lbl in zip(valid_symbols, labels):
        print(f'    {sym:10s} → Cluster {lbl}')
    return labels


# ── Function 5: Print descriptive statistics ──────────────────────────────
def descriptive_stats(df, symbol):
    """Prints basic statistical summary of the stock."""
    print(f'\n  === Descriptive Stats: {symbol} ===')
    stats = df[['Close','Volume','RSI','MACD','Volatility']].describe()
    print(stats.to_string())


# ── Main: Run for all symbols ─────────────────────────────────────────────
if __name__ == '__main__':
    SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'BTC-USD', 'ETH-USD']
    print('=== EDA STARTED ===')
    for symbol in SYMBOLS:
        print(f'\nAnalyzing: {symbol}')
        df = load_data(symbol)
        if df is not None:
            df = add_indicators(df)
            descriptive_stats(df, symbol)
            plot_analysis(df, symbol)
    cluster_assets(SYMBOLS)
    print('\n=== EDA COMPLETE — check output/ folder for charts ===')
