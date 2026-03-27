# eda/analysis.py
# PURPOSE: Load stock data, clean it, add technical indicators,
#          create charts including correlation and volatility analysis
# USAGE:   python eda/analysis.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

os.makedirs('output', exist_ok=True)

def load_data(symbol):
    """Loads and cleans CSV saved by fetch_data.py."""
    path = f'data/{symbol}_data.csv'
    if not os.path.exists(path):
        print(f'  File not found: {path} - run fetch_data.py first')
        return None
    df = pd.read_csv(path)
    # ── Missing Value Handling ─────────────────────────────────────────────
    # Step 1: Convert Date column to proper datetime type
    df['Date'] = pd.to_datetime(df['Date'], utc=True, errors='coerce')
    # Step 2: Remove rows with invalid dates
    df.dropna(subset=['Date'], inplace=True)
    # Step 3: Sort by date oldest first
    df.sort_values('Date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    # Step 4: Report missing values BEFORE filling
    price_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_before = df[price_cols].isnull().sum()
    if missing_before.sum() > 0:
        print(f'  Missing values found before cleaning:')
        print(missing_before[missing_before > 0])
    # Step 5: Forward-fill price gaps (carry last known price forward)
    #         This handles weekends/holidays where markets are closed
    df[price_cols] = df[price_cols].ffill()
    # Step 6: Remove any rows still missing Close price after fill
    rows_before = len(df)
    df.dropna(subset=['Close'], inplace=True)
    rows_removed = rows_before - len(df)
    if rows_removed > 0:
        print(f'  Removed {rows_removed} rows with unfillable missing prices')
    print(f'  Loaded {len(df)} rows for {symbol} (clean)')
    return df

def add_indicators(df):
    """Adds all technical indicators and generates Buy/Sell signals."""
    close = df['Close']
    # Moving Averages
    df['MA_20'] = SMAIndicator(close, window=20).sma_indicator()
    df['MA_50'] = SMAIndicator(close, window=50).sma_indicator()
    df['EMA_12'] = EMAIndicator(close, window=12).ema_indicator()
    # RSI
    df['RSI'] = RSIIndicator(close, window=14).rsi()
    # MACD
    macd_obj = MACD(close)
    df['MACD'] = macd_obj.macd()
    df['MACD_Signal'] = macd_obj.macd_signal()
    df['MACD_Hist'] = macd_obj.macd_diff()
    # Bollinger Bands
    bb = BollingerBands(close, window=20, window_dev=2)
    df['BB_Upper'] = bb.bollinger_hband()
    df['BB_Middle'] = bb.bollinger_mavg()
    df['BB_Lower'] = bb.bollinger_lband()
    # Returns and Volatility
    df['Daily_Return'] = close.pct_change()
    df['Volatility'] = df['Daily_Return'].rolling(window=20).std()
    # Buy/Sell Signals: Rule-based (also used as ML labels)
    df['Signal'] = 0  # 0 = HOLD
    df.loc[df['RSI'] < 40, 'Signal'] = 1   # BUY
    df.loc[df['RSI'] > 60, 'Signal'] = -1  # SELL
    # Remove rows where indicators couldn't be calculated yet
    df.dropna(subset=['MA_50', 'RSI', 'MACD'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(f'  Added indicators. Signals: BUY={sum(df.Signal==1)}, SELL={sum(df.Signal==-1)}')
    return df

def plot_analysis(df, symbol):
    """Creates 3-panel chart: Price+MAs, RSI, MACD. Saves as PNG."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(f'{symbol} - Technical Analysis', fontsize=14, fontweight='bold')
    ax1 = axes[0]
    ax1.plot(df['Date'], df['Close'], label='Close Price', color='#1F4E79', linewidth=1.5)
    ax1.plot(df['Date'], df['MA_20'], label='MA 20', color='orange', alpha=0.8, linewidth=1)
    ax1.plot(df['Date'], df['MA_50'], label='MA 50', color='red', alpha=0.8, linewidth=1)
    ax1.fill_between(df['Date'], df['BB_Upper'], df['BB_Lower'], alpha=0.1, color='blue', label='Bollinger Bands')
    buys = df[df['Signal'] == 1]
    sells = df[df['Signal'] == -1]
    ax1.scatter(buys['Date'], buys['Close'], marker='^', color='green', s=80, label='BUY', zorder=5)
    ax1.scatter(sells['Date'], sells['Close'], marker='v', color='red', s=80, label='SELL', zorder=5)
    ax1.legend(fontsize=8); ax1.set_ylabel('Price (USD)'); ax1.grid(alpha=0.3)
    ax2 = axes[1]
    ax2.plot(df['Date'], df['RSI'], color='purple', linewidth=1.2)
    ax2.axhline(70, color='red', linestyle='--', alpha=0.6, label='Overbought (70)')
    ax2.axhline(30, color='green', linestyle='--', alpha=0.6, label='Oversold (30)')
    ax2.fill_between(df['Date'], df['RSI'], 70, where=(df['RSI']>=70), alpha=0.2, color='red')
    ax2.fill_between(df['Date'], df['RSI'], 30, where=(df['RSI']<=30), alpha=0.2, color='green')
    ax2.set_ylabel('RSI'); ax2.set_ylim(0, 100); ax2.legend(fontsize=8); ax2.grid(alpha=0.3)
    ax3 = axes[2]
    ax3.plot(df['Date'], df['MACD'], label='MACD', color='blue', linewidth=1.2)
    ax3.plot(df['Date'], df['MACD_Signal'], label='Signal', color='red', linewidth=1.2)
    ax3.bar(df['Date'], df['MACD_Hist'],
            color=df['MACD_Hist'].apply(lambda x: 'green' if x>=0 else 'red'), alpha=0.4, label='Histogram')
    ax3.axhline(0, color='black', linewidth=0.5)
    ax3.set_ylabel('MACD'); ax3.legend(fontsize=8); ax3.grid(alpha=0.3)
    plt.tight_layout()
    save_path = f'output/{symbol}_analysis.png'
    plt.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f'  Chart saved: {save_path}')

# ── Correlation Analysis ───────────────────────────────────────────────────
def correlation_analysis(symbols):
    """
    Creates a heatmap showing how correlated all assets are with each other.
    High correlation (near 1.0) means assets move together.
    Low or negative correlation means they move differently (good for diversification).

    FIX: Stocks (Mon-Fri) and crypto (7 days) have different trading calendars.
    We align on date-only index, then forward-fill + backward-fill gaps so the
    combined DataFrame has no NaN rows before computing pct_change().
    """
    print('\n  Running correlation analysis...')
    closes = {}
    for symbol in symbols:
        df = load_data(symbol)
        if df is not None:
            # ── FIX: strip timezone and keep date only so all assets align ──
            df['DateOnly'] = df['Date'].dt.normalize().dt.tz_localize(None)
            series = df.set_index('DateOnly')['Close']
            # Remove duplicate dates (keep last)
            series = series[~series.index.duplicated(keep='last')]
            closes[symbol] = series

    # ── FIX: build combined on a full date range covering all assets ────────
    # Use the union of all dates (stocks Mon-Fri + crypto every day)
    all_dates = sorted(set().union(*[s.index for s in closes.values()]))
    combined = pd.DataFrame(index=all_dates)
    for symbol, series in closes.items():
        combined[symbol] = series

    # ── FIX: fill gaps caused by calendar mismatch ──────────────────────────
    # ffill: carry last known price into weekends/holidays
    # bfill: fill any leading NaNs at the start of shorter series
    combined = combined.ffill().bfill()

    # Drop any remaining all-NaN rows (should be none after bfill)
    combined.dropna(how='all', inplace=True)

    # ── Compute daily returns on the aligned, gap-filled data ───────────────
    returns = combined.pct_change(fill_method=None).dropna()

    # Compute correlation matrix; fillna(0) handles edge cases
    corr_matrix = returns.corr().fillna(0)

    print('  Correlation matrix:')
    print(corr_matrix.to_string())

    # ── Plot ─────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Left: correlation heatmap with values annotated
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt='.2f',
        cmap='RdYlBu_r',
        center=0,
        vmin=-1,
        vmax=1,
        ax=axes[0],
        annot_kws={'size': 11},
        linewidths=0.5,
        linecolor='white'
    )
    axes[0].set_title('Daily Returns Correlation Matrix', fontsize=13, fontweight='bold')
    axes[0].tick_params(axis='x', rotation=30)
    axes[0].tick_params(axis='y', rotation=0)

    # Right: 30-day rolling correlation AAPL vs BTC-USD
    if 'AAPL' in returns.columns and 'BTC-USD' in returns.columns:
        rolling_corr = returns['AAPL'].rolling(30).corr(returns['BTC-USD'])
        rc_vals = rolling_corr.values.astype(float)
        rc_idx  = range(len(rc_vals))

        axes[1].plot(rc_idx, rc_vals, color='#2E75B6', linewidth=1.5)
        axes[1].axhline(0, color='black', linestyle='--', alpha=0.5)
        axes[1].fill_between(rc_idx, rc_vals, 0,
                             where=(rc_vals > 0), alpha=0.2, color='green')
        axes[1].fill_between(rc_idx, rc_vals, 0,
                             where=(rc_vals < 0), alpha=0.2, color='red')
        axes[1].set_title('30-Day Rolling Correlation: AAPL vs BTC', fontsize=13, fontweight='bold')
        axes[1].set_ylabel('Correlation')
        axes[1].set_xlabel('Trading Days')
        axes[1].grid(alpha=0.3)
    else:
        axes[1].text(0.5, 0.5, 'AAPL or BTC-USD data not available',
                     ha='center', va='center', transform=axes[1].transAxes)

    plt.tight_layout()
    plt.savefig('output/correlation_analysis.png', dpi=120, bbox_inches='tight')
    plt.close()
    print('  Correlation heatmap saved: output/correlation_analysis.png')
    return corr_matrix

# ── Volatility Analysis ────────────────────────────────────────────────────
def volatility_analysis(symbols):
    """
    Compares volatility across all assets.
    Also calculates Value at Risk (VaR) - the maximum expected daily loss
    at a 95% confidence level.
    """
    print('\n  Running volatility analysis...')
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    all_returns = {}
    var_results = {}
    for symbol in symbols:
        df = load_data(symbol)
        if df is None:
            continue
        df = add_indicators(df)
        returns = df['Daily_Return'].dropna()
        all_returns[symbol] = returns
        # Plot rolling volatility
        df_plot = df.dropna(subset=['Volatility'])
        axes[0].plot(df_plot['Date'], df_plot['Volatility'] * 100,
                     label=symbol, linewidth=1.2)
        # Value at Risk (VaR) at 95% confidence
        var_95 = np.percentile(returns, 5)  # 5th percentile = worst 5% of days
        var_results[symbol] = round(var_95 * 100, 2)
    axes[0].set_title('20-Day Rolling Volatility (%) by Asset', fontsize=13, fontweight='bold')
    axes[0].set_ylabel('Volatility (%)')
    axes[0].legend(fontsize=9)
    axes[0].grid(alpha=0.3)
    # VaR bar chart
    syms = list(var_results.keys())
    vars_ = [var_results[s] for s in syms]
    colors = ['red' if v < -2 else 'orange' if v < -1 else 'green' for v in vars_]
    axes[1].bar(syms, [abs(v) for v in vars_], color=colors, alpha=0.8)
    for i, (s, v) in enumerate(zip(syms, vars_)):
        axes[1].text(i, abs(v) + 0.05, f'{v}%', ha='center', fontsize=10)
    axes[1].set_title('Value at Risk (VaR 95%) - Max Expected Daily Loss', fontsize=13, fontweight='bold')
    axes[1].set_ylabel('VaR % (higher = riskier)')
    axes[1].grid(alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('output/volatility_analysis.png', dpi=120, bbox_inches='tight')
    plt.close()
    print('  Volatility chart saved: output/volatility_analysis.png')
    print('  Value at Risk (95%) per asset:')
    for s, v in var_results.items():
        print(f'    {s:<12} VaR = {v}% per day')
    return var_results

# ── ML Model ──────────────────────────────────────────────────────────────
def train_ml_model(df, symbol):
    """
    Trains a Random Forest classifier to predict BUY/SELL/HOLD signals.
    This is the machine learning component required by the assignment.
    Uses technical indicators as features.
    """
    print(f'\n  Training ML model for {symbol}...')
    features = ['RSI', 'MACD', 'MACD_Signal', 'MACD_Hist',
                'MA_20', 'MA_50', 'EMA_12', 'Volatility', 'Daily_Return']
    signal_map = {1: 'BUY', -1: 'SELL', 0: 'HOLD'}
    df_clean = df.dropna(subset=features + ['Signal']).copy()
    if len(df_clean) < 50:
        print(f'  Not enough data to train ML model for {symbol}')
        return None
    X = df_clean[features]
    y = df_clean['Signal'].map(signal_map)
    # 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f'  ML Model Accuracy for {symbol}: {acc:.1%}')
    print(classification_report(y_test, y_pred, zero_division=0))
    # Feature importance
    importances = pd.Series(model.feature_importances_, index=features)
    importances = importances.sort_values(ascending=False)
    print('  Feature Importance:')
    for feat, imp in importances.items():
        print(f'    {feat:<20} {imp:.3f}')
    # Save feature importance chart
    fig, ax = plt.subplots(figsize=(8, 5))
    importances.plot(kind='barh', ax=ax, color='#2E75B6')
    ax.set_title(f'{symbol} - Random Forest Feature Importance', fontsize=12, fontweight='bold')
    ax.set_xlabel('Importance Score')
    ax.grid(alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(f'output/{symbol}_feature_importance.png', dpi=120)
    plt.close()
    return model, acc

def cluster_assets(symbols, n_clusters=3):
    """Groups stocks into clusters based on return, volatility and RSI."""
    print('\n  Clustering assets...')
    feature_rows = []
    valid_symbols = []
    for symbol in symbols:
        df = load_data(symbol)
        if df is None: continue
        df = add_indicators(df)
        avg_return  = df['Daily_Return'].mean()
        avg_vol     = df['Volatility'].mean()
        avg_rsi     = df['RSI'].mean()
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
        print(f'    {sym:<12} -> Cluster {lbl}')
    return labels

def descriptive_stats(df, symbol):
    """Prints basic statistical summary of the stock."""
    print(f'\n  === Descriptive Stats: {symbol} ===')
    stats = df[['Close','Volume','RSI','MACD','Volatility']].describe()
    print(stats.to_string())

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
            train_ml_model(df, symbol)
    # Cross-asset analysis
    correlation_analysis(SYMBOLS)
    volatility_analysis(SYMBOLS)
    cluster_assets(SYMBOLS)
    print('\n=== EDA COMPLETE - check output/ folder for charts ===')
