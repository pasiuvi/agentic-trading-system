# agents/orchestrator.py
# PURPOSE: Orchestrator - calls all 4 agents in order for each symbol

import json, datetime, pandas as pd, os
from agents.market_analysis import MarketAnalysisAgent
from agents.info_retrieval   import InfoRetrievalAgent
from agents.decision_engine  import DecisionEngine
from agents.risk_manager     import RiskManager

class TradingOrchestrator:
    """
    Coordinates the full Agentic AI workflow:
    1. MarketAnalysisAgent  -> reads indicators -> market signal
    2. InfoRetrievalAgent   -> reads news       -> VADER sentiment
    3. DecisionEngine       -> combines both    -> raw decision
    4. RiskManager          -> validates rules  -> final action
    """
    def __init__(self, portfolio_value=100000):
        self.market_agent  = MarketAnalysisAgent()
        self.news_agent    = InfoRetrievalAgent()
        self.decision_eng  = DecisionEngine()
        self.risk_mgr      = RiskManager()
        self.portfolio     = portfolio_value
        self.positions     = {}
        self.trade_log     = []

    def run_for_symbol(self, symbol, df):
        print(f'  [{symbol}] Running agentic workflow...')
        ts = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Step 1: Market Analysis
        print(f'  [{symbol}] Step 1: Market Analysis Agent...')
        market_result = self.market_agent.analyze(df)
        print(f'  [{symbol}] Signal: {market_result["signal"]} ({market_result["confidence"]:.0%} confidence)')

        # Step 2: News Sentiment (VADER)
        print(f'  [{symbol}] Step 2: Info Retrieval Agent (VADER NLP)...')
        sentiment = self.news_agent.get_sentiment(symbol)

        # Step 3: Decision Engine
        print(f'  [{symbol}] Step 3: Decision Engine...')
        decision_result = self.decision_eng.decide(market_result, sentiment)
        print(f'  [{symbol}] Decision: {decision_result["decision"]} ({decision_result["confidence"]:.0%} confidence)')

        # Step 4: Risk Management
        print(f'  [{symbol}] Step 4: Risk Manager...')
        current_price  = float(df['Close'].iloc[-1])
        position_value = self.positions.get(symbol, 0)
        risk_result    = self.risk_mgr.approve(
            decision       = decision_result['decision'],
            confidence     = decision_result['confidence'],
            current_price  = current_price,
            portfolio_value= self.portfolio,
            position_value = position_value,
        )
        final_action = risk_result['action']
        print(f'  [{symbol}] Final Action: {final_action} - {risk_result["reason"]}')

        result = {
            'timestamp':    ts,
            'symbol':       symbol,
            'close_price':  current_price,
            'market_signal':market_result['signal'],
            'market_conf':  market_result['confidence'],
            'rsi':          market_result['rsi'],
            'sentiment':    sentiment,
            'decision':     decision_result['decision'],
            'final_action': final_action,
            'final_conf':   decision_result['confidence'],
            'risk_approved':risk_result['approved'],
            'risk_reason':  risk_result['reason'],
            'trade_size_usd':risk_result.get('suggested_size_usd', 0),
            'reasoning':    ' | '.join(decision_result.get('reasoning', [])),
        }
        self.trade_log.append(result)
        return result

    def save_trade_log(self, path='output/trade_decisions.csv'):
        if self.trade_log:
            os.makedirs('output', exist_ok=True)
            pd.DataFrame(self.trade_log).to_csv(path, index=False)
            print(f'  Trade log saved: {path}')

    def print_summary(self):
        print('\n' + '='*65)
        print(f'  {"SYMBOL":<10} {"SIGNAL":<6} {"SENTIMENT":<10} {"FINAL":<6} {"CONF"}')
        print('='*65)
        for r in self.trade_log:
            print(f'  {r["symbol"]:<10} {r["market_signal"]:<6} '
                  f'{r["sentiment"]:<10} {r["final_action"]:<6} '
                  f'{r["final_conf"]:.0%}')
        print('='*65)
