# agents/market_analysis.py
# PURPOSE: Market Analysis Agent - reads technical indicators and scores them

class MarketAnalysisAgent:
    """
    Reads the latest indicator values for a stock and decides whether
    conditions suggest BUY, SELL, or HOLD. Gives a confidence score (0-1).
    """
    def analyze(self, df):
        latest     = df.iloc[-1]
        signal     = 'HOLD'
        confidence = 0.50
        reasons    = []
        rsi        = latest.get('RSI', 50)
        macd       = latest.get('MACD', 0)
        macd_sig   = latest.get('MACD_Signal', 0)
        close      = latest.get('Close', 0)
        ma20       = latest.get('MA_20', close)
        ma50       = latest.get('MA_50', close)
        volatility = latest.get('Volatility', 0)

        # Rule 1: RSI-based signal
        if rsi < 30:
            signal = 'BUY'; confidence = 0.65
            reasons.append(f'RSI={rsi:.1f} (oversold below 30)')
        elif rsi > 70:
            signal = 'SELL'; confidence = 0.65
            reasons.append(f'RSI={rsi:.1f} (overbought above 70)')
        elif 45 <= rsi <= 55:
            reasons.append(f'RSI={rsi:.1f} (neutral)')

        # Rule 2: MACD crossover
        if macd > macd_sig and signal != 'SELL':
            if signal == 'BUY': confidence = min(confidence + 0.10, 0.95)
            else: signal = 'BUY'; confidence = 0.60
            reasons.append('MACD above signal (bullish)')
        elif macd < macd_sig and signal != 'BUY':
            if signal == 'SELL': confidence = min(confidence + 0.10, 0.95)
            else: signal = 'SELL'; confidence = 0.60
            reasons.append('MACD below signal (bearish)')

        # Rule 3: Moving Average crossover
        if ma20 > ma50:
            reasons.append('MA20 > MA50 (uptrend)')
            if signal == 'BUY': confidence = min(confidence + 0.08, 0.95)
        elif ma20 < ma50:
            reasons.append('MA20 < MA50 (downtrend)')
            if signal == 'SELL': confidence = min(confidence + 0.08, 0.95)

        # Rule 4: High volatility warning
        if volatility > 0.03:
            confidence = max(confidence - 0.05, 0.10)
            reasons.append(f'High volatility ({volatility:.3f}) - caution')

        return {
            'signal': signal,
            'confidence': round(confidence, 2),
            'rsi': round(rsi, 2),
            'macd': round(macd, 4),
            'close': round(close, 2),
            'reasons': reasons,
        }
