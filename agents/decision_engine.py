# agents/decision_engine.py
# PURPOSE: Combines market analysis and news sentiment to make final decision

class DecisionEngine:
    """
    Combines the market signal (from MarketAnalysisAgent)
    and news sentiment (from InfoRetrievalAgent)
    to produce the final trading decision.
    """
    def decide(self, market_result, sentiment):
        signal     = market_result['signal']
        confidence = market_result['confidence']
        reasons    = list(market_result.get('reasons', []))

        if sentiment == 'POSITIVE':
            if signal == 'BUY':
                confidence = min(confidence + 0.12, 0.95)
                reasons.append('Positive news boosts BUY confidence')
            elif signal == 'SELL':
                confidence = max(confidence - 0.10, 0.10)
                reasons.append('Positive news weakens SELL signal')
            elif signal == 'HOLD':
                signal = 'BUY'; confidence = 0.55
                reasons.append('Positive news turns HOLD into weak BUY')

        elif sentiment == 'NEGATIVE':
            if signal == 'SELL':
                confidence = min(confidence + 0.12, 0.95)
                reasons.append('Negative news boosts SELL confidence')
            elif signal == 'BUY':
                confidence = max(confidence - 0.15, 0.10)
                reasons.append('Negative news weakens BUY signal')
                if confidence < 0.40:
                    signal = 'HOLD'
                    reasons.append('Low confidence - switching to HOLD for safety')
            elif signal == 'HOLD':
                signal = 'SELL'; confidence = 0.55
                reasons.append('Negative news turns HOLD into weak SELL')

        elif sentiment == 'NEUTRAL':
            reasons.append('Neutral news - no sentiment adjustment')

        return {
            'decision':   signal,
            'confidence': round(confidence, 2),
            'sentiment':  sentiment,
            'reasoning':  reasons,
        }
