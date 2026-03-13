# output/backtest.py
# PURPOSE: Backtesting - simulate trading with historical data to measure performance
#          ENHANCED: Sharpe Ratio, Max Drawdown, Win Rate, Benchmark comparison
# USAGE:   Imported by main.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

os.makedirs('output', exist_ok=True)

def calculate_metrics(portfolio_values, initial_capital, trades):
    """
    Calculates professional performance metrics used by real hedge funds:
    - Sharpe Ratio: return per unit of risk (>1 = good, >2 = excellent)
    - Max Drawdown: worst peak-to-trough loss
    - Win Rate: % of profitable trades
    """
    if len(portfolio_values) < 2:
        return {}
    values = [p['Portfolio_Value'] for p in portfolio_values]
    # Daily returns of the strategy
    returns = pd.Series(values).pct_change().dropna()
    # Sharpe Ratio (annualised, assumes 252 trading days, risk-free rate ~0)
    if returns.std() > 0:
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
    else:
        sharpe = 0.0
    # Maximum Drawdown
    peak = pd.Series(values).cummax()
    drawdown = (pd.Series(values) - peak) / peak
    max_drawdown = drawdown.min()
    # Win Rate - % of SELL trades that were profitable
    buy_prices = {}
    profits = []
    for t in trades:
        if t['Action'] == 'BUY':
            buy_prices[t['Date']] = t['Price']
        elif t['Action'] == 'SELL' and buy_prices:
            last_buy = list(buy_prices.values())[-1]
            profits.append(t['Price'] - last_buy)
    win_rate = sum(1 for p in profits if p > 0) / len(profits) if profits else 0
    return {
        'Sharpe Ratio':    round(sharpe, 2),
        'Max Drawdown':    f'{max_drawdown:.1%}',
        'Win Rate':        f'{win_rate:.1%}',
        'Profitable Trades': sum(1 for p in profits if p > 0),
        'Total Completed Trades': len(profits)
    }

def backtest(df, symbol, initial_capital=100000, trade_pct=0.10):
    """
    Simulates buying and selling based on the Signal column.
    Signal = 1  -> BUY  (use 10% of available cash)
    Signal = -1 -> SELL (sell all held shares)
    Signal = 0  -> HOLD (do nothing)
    Returns: (trades_df, final_portfolio_value, total_return_pct)
    """
    capital    = float(initial_capital)
    position   = 0
    trades     = []
    portfolio_values = []

    for _, row in df.iterrows():
        price    = float(row['Close'])
        signal   = int(row.get('Signal', 0))
        date     = str(row['Date'])
        cur_val  = capital + position * price
        portfolio_values.append({'Date': date, 'Portfolio_Value': cur_val})

        if signal == 1 and capital > price:        # BUY signal
            invest         = capital * trade_pct
            shares_to_buy  = int(invest / price)
            if shares_to_buy > 0:
                cost     = shares_to_buy * price
                capital -= cost
                position += shares_to_buy
                trades.append({'Date':date,'Action':'BUY','Price':round(price,2),
                               'Shares':shares_to_buy,'Cost':round(cost,2),'Cash_After':round(capital,2)})
        elif signal == -1 and position > 0:        # SELL signal
            proceeds = position * price
            capital += proceeds
            trades.append({'Date':date,'Action':'SELL','Price':round(price,2),
                           'Shares':position,'Cost':round(proceeds,2),'Cash_After':round(capital,2)})
            position = 0

    # Final portfolio value
    last_price  = float(df['Close'].iloc[-1])
    final_value = capital + position * last_price
    total_return = ((final_value - initial_capital) / initial_capital) * 100

    # Buy-and-hold benchmark: buy on day 1, sell on last day
    first_price = float(df['Close'].iloc[0])
    shares_bh   = int(initial_capital / first_price)
    bh_value    = shares_bh * last_price + (initial_capital - shares_bh * first_price)
    bh_return   = ((bh_value - initial_capital) / initial_capital) * 100

    # Calculate advanced metrics
    metrics = calculate_metrics(portfolio_values, initial_capital, trades)

    num_buys  = sum(1 for t in trades if t['Action'] == 'BUY')
    num_sells = sum(1 for t in trades if t['Action'] == 'SELL')

    print(f'\n  Backtest Results for {symbol}:')
    print(f'  {"":─<50}')
    print(f'  Initial Capital      : ${initial_capital:>12,.2f}')
    print(f'  Final Value          : ${final_value:>12,.2f}')
    print(f'  Strategy Return      : {total_return:>+11.2f}%')
    print(f'  Buy-and-Hold Return  : {bh_return:>+11.2f}%')
    print(f'  Outperformance       : {total_return - bh_return:>+11.2f}%')
    print(f'  Total Trades         : {len(trades)} ({num_buys} buys, {num_sells} sells)')
    for k, v in metrics.items():
        print(f'  {k:<22}: {v}')
    print(f'  {"":─<50}')

    # Save trade log
    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    if not trades_df.empty:
        path = f'output/{symbol}_trades.csv'
        trades_df.to_csv(path, index=False)
        print(f'  Trades saved to {path}')

    # Plot portfolio vs benchmark
    _plot_portfolio(portfolio_values, symbol, initial_capital,
                    df, shares_bh, first_price)

    return trades_df, round(final_value, 2), round(total_return, 2), metrics

def _plot_portfolio(portfolio_values, symbol, initial_capital, df, shares_bh, first_price):
    """Creates portfolio vs buy-and-hold comparison chart."""
    if not portfolio_values:
        return
    pf = pd.DataFrame(portfolio_values)
    pf['Date'] = pd.to_datetime(pf['Date'], utc=True, errors='coerce')
    pf.dropna(subset=['Date'], inplace=True)

    # Build buy-and-hold line
    bh_values = shares_bh * df['Close'].values + (initial_capital - shares_bh * first_price)

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(pf['Date'], pf['Portfolio_Value'], color='#1F4E79',
            linewidth=2, label='Strategy Portfolio', zorder=3)
    ax.plot(pf['Date'][:len(bh_values)], bh_values[:len(pf)], color='orange',
            linewidth=1.5, linestyle='--', label='Buy-and-Hold Benchmark')
    ax.axhline(initial_capital, color='gray', linestyle=':', alpha=0.7,
               label=f'Initial: ${initial_capital:,.0f}')
    ax.fill_between(pf['Date'], pf['Portfolio_Value'], initial_capital,
                    where=(pf['Portfolio_Value'] >= initial_capital),
                    alpha=0.15, color='green', label='Profit zone')
    ax.fill_between(pf['Date'], pf['Portfolio_Value'], initial_capital,
                    where=(pf['Portfolio_Value'] < initial_capital),
                    alpha=0.15, color='red', label='Loss zone')
    ax.set_title(f'{symbol} - Strategy vs Buy-and-Hold Backtest', fontsize=13, fontweight='bold')
    ax.set_ylabel('Portfolio Value (USD)')
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = f'output/{symbol}_backtest.png'
    plt.savefig(path, dpi=120)
    plt.close()
    print(f'  Backtest chart saved: {path}')
