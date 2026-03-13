# agents/decision_engine.py
# PURPOSE: Decision Engine — combines market analysis and news sentiment
#          to make the final BUY / SELL / HOLD decision
# USAGE:   Imported by orchestrator.py

class DecisionEngine:
    """
    This is the brain of the trading system.
    It takes the market signal (from MarketAnalysisAgent)
    and the news sentiment (from InfoRetrievalAgent)
    and combines them to produce a final decision.
    """

    def decide(self, market_result, sentiment):
        """
        Inputs:
          market_result = dict from MarketAnalysisAgent.analyze()
          sentiment     = string: 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'

        Output: dict with decision, confidence, and explanation
        """
        signal     = market_result['signal']       # 'BUY', 'SELL', or 'HOLD'
        confidence = market_result['confidence']   # 0.0 to 1.0
        reasons    = list(market_result.get('reasons', []))

        # ── Sentiment adjustment rules ────────────────────────────────

        if sentiment == 'POSITIVE':
            if signal == 'BUY':
                # Good news + technical BUY = strong buy
                confidence = min(confidence + 0.12, 0.95)
                reasons.append('Positive news boosts BUY confidence')
            elif signal == 'SELL':
                # Good news contradicts SELL — reduce confidence
                confidence = max(confidence - 0.10, 0.10)
                reasons.append('Positive news weakens SELL signal')
            elif signal == 'HOLD':
                # Good news might push a HOLD toward BUY
                signal = 'BUY'
                confidence = 0.55
                reasons.append('Positive news turns HOLD into weak BUY')

        elif sentiment == 'NEGATIVE':
            if signal == 'SELL':
                # Bad news + technical SELL = strong sell
                confidence = min(confidence + 0.12, 0.95)
                reasons.append('Negative news boosts SELL confidence')
            elif signal == 'BUY':
                # Bad news contradicts BUY — reduce confidence a lot
                confidence = max(confidence - 0.15, 0.10)
                reasons.append('Negative news weakens BUY signal')
                # If confidence drops too low, switch to HOLD (safer)
                if confidence < 0.40:
                    signal = 'HOLD'
                    reasons.append('Low confidence — switching to HOLD for safety')
            elif signal == 'HOLD':
                # Bad news might push a HOLD toward SELL
                signal = 'SELL'
                confidence = 0.55
                reasons.append('Negative news turns HOLD into weak SELL')

        # NEUTRAL news: no change to signal or confidence
        elif sentiment == 'NEUTRAL':
            reasons.append('Neutral news — no sentiment adjustment')

        return {
            'decision':    signal,
            'confidence':  round(confidence, 2),
            'sentiment':   sentiment,
            'reasoning':   reasons,
        }
