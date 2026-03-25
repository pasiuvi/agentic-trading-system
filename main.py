# main.py
# PURPOSE: Master entry point - runs the full trading pipeline
# USAGE:   python main.py

import os
from dotenv import load_dotenv
load_dotenv()

from ingestion.fetch_data import fetch_stock_data, upload_to_s3, save_to_rds, save_locally
from eda.analysis import (load_data, add_indicators, plot_analysis,
                           correlation_analysis, volatility_analysis,
                           cluster_assets, train_ml_model)
from agents.orchestrator import TradingOrchestrator
from output.backtest import backtest

SYMBOLS        = ['AAPL', 'MSFT', 'GOOGL', 'BTC-USD', 'ETH-USD']
INITIAL_CAPITAL = 100_000

def run_pipeline():
    print('\n' + '='*60)
    print('  AGENTIC AI TRADING SYSTEM - STARTING')
    print('='*60)
    os.makedirs('output', exist_ok=True)
    orchestrator     = TradingOrchestrator(portfolio_value=INITIAL_CAPITAL)
    backtest_summary = []

    for symbol in SYMBOLS:
        print(f'\n{"─"*60}')
        print(f'  Processing: {symbol}')
        print(f'{"─"*60}')

        # ── PHASE 1: Data Collection ────────────────────────────────
        print(f'\n  [Phase 1] Data Collection...')
        df_raw = fetch_stock_data(symbol, period='1y')
        if df_raw is None:
            print(f'  SKIP: Could not get data for {symbol}')
            continue
        upload_to_s3(df_raw, symbol)
        save_to_rds(df_raw)
        save_locally(df_raw, symbol)

        # ── PHASE 2: EDA & Feature Engineering ────────────────────
        print(f'\n  [Phase 2] EDA & Feature Engineering...')
        df = load_data(symbol)
        if df is None:
            continue
        df = add_indicators(df)
        plot_analysis(df, symbol)
        train_ml_model(df, symbol)   # NEW: ML model evaluation

        # ── PHASE 3: Agentic AI Decision ───────────────────────────
        print(f'\n  [Phase 3] Agentic AI Agents...')
        result = orchestrator.run_for_symbol(symbol, df)

        # ── PHASE 4: Backtesting ────────────────────────────────────
        print(f'\n  [Phase 4] Backtesting...')
        trades_df, final_val, ret_pct, metrics = backtest(
            df, symbol, initial_capital=INITIAL_CAPITAL
        )
        backtest_summary.append({
            'Symbol':        symbol,
            'Final_Action':  result['final_action'],
            'Sentiment':     result['sentiment'],
            'Confidence':    f"{result['final_conf']:.0%}",
            'Final_Value':   f'${final_val:,.2f}',
            'Return':        f'{ret_pct:+.2f}%',
            'Sharpe':        metrics.get('Sharpe Ratio', 'N/A'),
            'MaxDrawdown':   metrics.get('Max Drawdown', 'N/A'),
        })

    # ── Cross-Asset Analysis (NEW) ─────────────────────────────────
    print('\n  [Phase 5] Cross-Asset Analysis...')
    correlation_analysis(SYMBOLS)
    volatility_analysis(SYMBOLS)
    cluster_assets(SYMBOLS)

    # ── Final Summary ──────────────────────────────────────────────
    orchestrator.print_summary()
    orchestrator.save_trade_log()
    print('\n' + '='*60)
    print('  BACKTEST SUMMARY')
    print('='*60)
    for row in backtest_summary:
        print(f'  {row["Symbol"]:<10} | {row["Final_Action"]:<5} | '
              f'{row["Sentiment"]:<10} | {row["Return"]:<10} | '
              f'Sharpe={row["Sharpe"]}  Drawdown={row["MaxDrawdown"]}')
    print('\n  All charts and logs saved in the output/ folder')
    print('  Pipeline complete!')

if __name__ == '__main__':
    run_pipeline()
    print("\n📄 Generating PDF report...")
    import subprocess
    result = subprocess.run(["python", "generate_report.py"], capture_output=False)
    if result.returncode == 0:
        print("✅ PDF report saved to output/trading_report.pdf")
    else:
        print("⚠️  Run python generate_report.py manually")


