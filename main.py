# main.py
# PURPOSE: Master entry point — runs the full trading pipeline
# USAGE:   python main.py

import os
from dotenv import load_dotenv

# Load .env file before anything else
load_dotenv()

from ingestion.fetch_data       import fetch_stock_data, upload_to_s3, save_to_rds, save_locally
from eda.analysis               import load_data, add_indicators, plot_analysis
from agents.orchestrator        import TradingOrchestrator
from output.backtest            import backtest

# ── Configuration ────────────────────────────────────────────────────────
# Change these symbols to track different stocks/crypto
SYMBOLS = ['AAPL', 'MSFT', 'BTC-USD']

# Starting portfolio value in USD (paper money — not real)
INITIAL_CAPITAL = 100_000


def run_pipeline():
    """
    Runs the complete 4-step pipeline:
    1. Collect data from Yahoo Finance → S3 → RDS
    2. EDA — clean, add indicators, create charts
    3. Agentic AI — 4 agents make trading decisions
    4. Backtest — simulate historical trading performance
    """
    print('\n' + '='*60)
    print('  AGENTIC AI TRADING SYSTEM — STARTING')
    print('='*60)

    # Create output folder if it doesn't exist
    os.makedirs('output', exist_ok=True)

    # Create orchestrator (manages all 4 agents)
    orchestrator = TradingOrchestrator(portfolio_value=INITIAL_CAPITAL)

    backtest_summary = []

    for symbol in SYMBOLS:
        print(f'\n{"─"*60}')
        print(f'  Processing: {symbol}')
        print(f'{"─"*60}')

        # ── PHASE 1: Data Collection ──────────────────────────────────
        print(f'\n  [Phase 1] Data Collection...')
        df_raw = fetch_stock_data(symbol, period='1y')
        if df_raw is None:
            print(f'  SKIP: Could not get data for {symbol}')
            continue

        upload_to_s3(df_raw, symbol)      # → AWS S3
        save_to_rds(df_raw)               # → AWS RDS
        save_locally(df_raw, symbol)      # → local data/ folder

        # ── PHASE 2: EDA & Feature Engineering ───────────────────────
        print(f'\n  [Phase 2] EDA & Feature Engineering...')
        df = load_data(symbol)
        if df is None:
            continue
        df = add_indicators(df)
        plot_analysis(df, symbol)         # saves PNG to output/

        # ── PHASE 3: Agentic AI Decision ──────────────────────────────
        print(f'\n  [Phase 3] Agentic AI Agents...')
        result = orchestrator.run_for_symbol(symbol, df)

        # ── PHASE 4: Backtesting ──────────────────────────────────────
        print(f'\n  [Phase 4] Backtesting...')
        trades_df, final_val, ret_pct = backtest(
            df, symbol, initial_capital=INITIAL_CAPITAL
        )
        backtest_summary.append({
            'Symbol':        symbol,
            'Final_Action':  result['final_action'],
            'Sentiment':     result['sentiment'],
            'Confidence':    f"{result['final_conf']:.0%}",
            'Final_Value':   f'${final_val:,.2f}',
            'Return':        f'{ret_pct:+.2f}%',
        })

    # ── Final Summary ─────────────────────────────────────────────────
    orchestrator.print_summary()
    orchestrator.save_trade_log()

    print('\n' + '='*60)
    print('  BACKTEST SUMMARY')
    print('='*60)
    for row in backtest_summary:
        print(f'  {row["Symbol"]:<10} | Action: {row["Final_Action"]:<5} | '
              f'Sentiment: {row["Sentiment"]:<10} | '
              f'Return: {row["Return"]:<10} | Final: {row["Final_Value"]}')

    print('\n  All charts and logs saved in the output/ folder')
    print('  Pipeline complete!')


if __name__ == '__main__':
    run_pipeline()
