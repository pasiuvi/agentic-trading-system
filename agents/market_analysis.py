# agents/market_analysis.py
# PURPOSE: Market Analysis Agent — reads technical indicators and scores them
# USAGE:   Imported by orchestrator.py (not run directly)

class MarketAnalysisAgent:
    """
    This agent looks at the latest indicator values for a stock
    and decides whether conditions suggest BUY, SELL, or HOLD.
    It also gives a confidence score (0.0 to 1.0).
    """

    def analyze(self, df):
        """
        Input:  df = DataFrame with at least the last row having:
                RSI, MACD, MACD_Signal, MA_20, MA_50, Close, Volatility
        Output: dict with signal, confidence, and indicator values
        """
        # Get the most recent data point
        latest = df.iloc[-1]

        signal     = 'HOLD'
        confidence = 0.50   # default: 50% confident → HOLD
        reasons    = []

        rsi         = latest.get('RSI', 50)
        macd        = latest.get('MACD', 0)
        macd_signal = latest.get('MACD_Signal', 0)
        close       = latest.get('Close', 0)
        ma20        = latest.get('MA_20', close)
        ma50        = latest.get('MA_50', close)
        volatility  = latest.get('Volatility', 0)

        # ── Rule 1: RSI-based signal ──────────────────────────────────
        # RSI < 30: stock is oversold → likely to bounce up → BUY
        # RSI > 70: stock is overbought → likely to fall → SELL
        if rsi < 30:
            signal = 'BUY'
            confidence = 0.65
            reasons.append(f'RSI={rsi:.1f} (oversold below 30)')
        elif rsi > 70:
            signal = 'SELL'
            confidence = 0.65
            reasons.append(f'RSI={rsi:.1f} (overbought above 70)')
        elif 45 <= rsi <= 55:
            reasons.append(f'RSI={rsi:.1f} (neutral)')

        # ── Rule 2: MACD crossover ───────────────────────────────────
        # MACD crosses above signal line → bullish momentum → BUY
        # MACD crosses below signal line → bearish momentum → SELL
        if macd > macd_signal and signal != 'SELL':
            if signal == 'BUY':
                confidence = min(confidence + 0.10, 0.95)  # extra confidence
            else:
                signal = 'BUY'
                confidence = 0.60
            reasons.append('MACD above signal (bullish)')
        elif macd < macd_signal and signal != 'BUY':
            if signal == 'SELL':
                confidence = min(confidence + 0.10, 0.95)
            else:
                signal = 'SELL'
                confidence = 0.60
            reasons.append('MACD below signal (bearish)')

        # ── Rule 3: Moving Average crossover ─────────────────────────
        # Short MA above long MA = uptrend → boosts BUY confidence
        # Short MA below long MA = downtrend → boosts SELL confidence
        if ma20 > ma50:
            reasons.append('MA20 > MA50 (uptrend)')
            if signal == 'BUY':
                confidence = min(confidence + 0.08, 0.95)
        elif ma20 < ma50:
            reasons.append('MA20 < MA50 (downtrend)')
            if signal == 'SELL':
                confidence = min(confidence + 0.08, 0.95)

        # ── Rule 4: High volatility warning ──────────────────────────
        # High volatility = risky market → reduce confidence slightly
        if volatility > 0.03:   # 3% daily swing is high
            confidence = max(confidence - 0.05, 0.10)
            reasons.append(f'High volatility ({volatility:.3f}) — caution')

        return {
            'signal':     signal,
            'confidence': round(confidence, 2),
            'rsi':        round(rsi, 2),
            'macd':       round(macd, 4),
            'close':      round(close, 2),
            'reasons':    reasons,
        }
