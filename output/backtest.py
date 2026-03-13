# output/backtest.py
# PURPOSE: Backtesting — simulate trading with historical data to measure performance
# USAGE:   Imported by main.py

import pandas as pd
import matplotlib.pyplot as plt
import os

os.makedirs('output', exist_ok=True)


def backtest(df, symbol, initial_capital=100000, trade_pct=0.10):
    """
    Simulates buying and selling based on the Signal column.
    Signal = 1  → BUY  (use 10% of available cash)
    Signal = -1 → SELL (sell all held shares)
    Signal = 0  → HOLD (do nothing)

    Returns: (trades_df, final_portfolio_value, total_return_pct)
    """
    capital  = float(initial_capital)   # cash available
    position = 0                         # shares held
    trades   = []                        # list of trade records
    portfolio_values = []                # track portfolio value over time

    for _, row in df.iterrows():
        price  = float(row['Close'])
        signal = int(row.get('Signal', 0))
        date   = str(row['Date'])

        current_value = capital + position * price
        portfolio_values.append({'Date': date, 'Portfolio_Value': current_value})

        if signal == 1 and capital > price:   # BUY signal
            # Buy with 10% of available capital
            invest = capital * trade_pct
            shares_to_buy = int(invest / price)

            if shares_to_buy > 0:
                cost = shares_to_buy * price
                capital  -= cost
                position += shares_to_buy
                trades.append({
                    'Date':   date,
                    'Action': 'BUY',
                    'Price':  round(price, 2),
                    'Shares': shares_to_buy,
                    'Cost':   round(cost, 2),
                    'Cash_After': round(capital, 2),
                })

        elif signal == -1 and position > 0:  # SELL signal
            # Sell all shares
            proceeds = position * price
            capital  += proceeds
            trades.append({
                'Date':   date,
                'Action': 'SELL',
                'Price':  round(price, 2),
                'Shares': position,
                'Cost':   round(proceeds, 2),
                'Cash_After': round(capital, 2),
            })
            position = 0

    # Final portfolio value (cash + remaining shares at last price)
    last_price    = float(df['Close'].iloc[-1])
    final_value   = capital + position * last_price
    total_return  = ((final_value - initial_capital) / initial_capital) * 100
    num_buys      = sum(1 for t in trades if t['Action'] == 'BUY')
    num_sells     = sum(1 for t in trades if t['Action'] == 'SELL')

    # ── Print results ─────────────────────────────────────────────────
    print(f'  Backtest Results for {symbol}:')
    print(f'    Initial Capital : ${initial_capital:>12,.2f}')
    print(f'    Final Value     : ${final_value:>12,.2f}')
    print(f'    Total Return    : {total_return:>+11.2f}%')
    print(f'    Total Trades    : {len(trades)} ({num_buys} buys, {num_sells} sells)')

    # ── Save trade log ────────────────────────────────────────────────
    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    if not trades_df.empty:
        path = f'output/{symbol}_trades.csv'
        trades_df.to_csv(path, index=False)
        print(f'    Trades saved to {path}')

    # ── Plot portfolio value over time ────────────────────────────────
    _plot_portfolio(portfolio_values, symbol, initial_capital)

    return trades_df, round(final_value, 2), round(total_return, 2)


def _plot_portfolio(portfolio_values, symbol, initial_capital):
    """Creates a chart showing portfolio value over time vs buy-and-hold."""
    if not portfolio_values:
        return

    pf = pd.DataFrame(portfolio_values)
    pf['Date'] = pd.to_datetime(pf['Date'], utc=True, errors='coerce')
    pf.dropna(subset=['Date'], inplace=True)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(pf['Date'], pf['Portfolio_Value'], color='#1F4E79', linewidth=1.5, label='Strategy Portfolio')
    ax.axhline(initial_capital, color='gray', linestyle='--', alpha=0.7, label=f'Initial: ${initial_capital:,.0f}')
    ax.fill_between(pf['Date'], pf['Portfolio_Value'], initial_capital,
                    where=(pf['Portfolio_Value'] >= initial_capital),
                    alpha=0.15, color='green', label='Profit zone')
    ax.fill_between(pf['Date'], pf['Portfolio_Value'], initial_capital,
                    where=(pf['Portfolio_Value'] < initial_capital),
                    alpha=0.15, color='red', label='Loss zone')
    ax.set_title(f'{symbol} — Backtest Portfolio Value', fontsize=13, fontweight='bold')
    ax.set_ylabel('Portfolio Value (USD)')
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = f'output/{symbol}_backtest.png'
    plt.savefig(path, dpi=120)
    plt.close()
    print(f'    Backtest chart saved: {path}')
