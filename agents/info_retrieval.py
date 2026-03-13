# agents/info_retrieval.py
# PURPOSE: Information Retrieval Agent - fetches news and scores sentiment
#          ENHANCED: uses VADER NLP for proper sentiment scoring
# USAGE:   Imported by orchestrator.py

import feedparser
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class InfoRetrievalAgent:
    """
    Fetches latest news headlines for a stock/crypto symbol
    and scores them using VADER (Valence Aware Dictionary and sEntiment Reasoner).
    VADER is designed specifically for social media and financial text.
    """

    NEWS_FEEDS = {
        'AAPL':    'https://finance.yahoo.com/rss/headline?s=AAPL',
        'MSFT':    'https://finance.yahoo.com/rss/headline?s=MSFT',
        'GOOGL':   'https://finance.yahoo.com/rss/headline?s=GOOGL',
        'BTC-USD': 'https://finance.yahoo.com/rss/headline?s=BTC-USD',
        'ETH-USD': 'https://finance.yahoo.com/rss/headline?s=ETH-USD',
    }

    def __init__(self):
        # VADER analyser - no API key needed, works offline
        self.analyser = SentimentIntensityAnalyzer()

    def get_news_headlines(self, symbol, max_headlines=15):
        """Fetches recent news headlines. Returns a list of strings."""
        url = self.NEWS_FEEDS.get(symbol, '')
        headlines = []
        if not url:
            print(f'  No RSS feed configured for {symbol}')
            return headlines
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_headlines]:
                headlines.append(entry.title)
        except Exception as e:
            print(f'  Could not fetch news for {symbol}: {e}')
        return headlines

    def score_sentiment(self, headlines):
        """
        Uses VADER to score each headline on a scale from -1 (very negative)
        to +1 (very positive). The compound score is the overall sentiment.
        """
        if not headlines:
            return 'NEUTRAL', {'avg_score': 0.0, 'headlines_count': 0}
        scores = []
        for headline in headlines:
            vs = self.analyser.polarity_scores(headline)
            scores.append(vs['compound'])  # compound = -1 to +1
        avg_score = sum(scores) / len(scores)
        # VADER thresholds: > 0.05 = positive, < -0.05 = negative
        if avg_score > 0.05:
            sentiment = 'POSITIVE'
        elif avg_score < -0.05:
            sentiment = 'NEGATIVE'
        else:
            sentiment = 'NEUTRAL'
        return sentiment, {
            'avg_score': round(avg_score, 3),
            'headlines_count': len(headlines),
            'individual_scores': scores
        }

    def get_sentiment(self, symbol):
        """
        Main method: fetch news + score sentiment for a symbol.
        Returns: sentiment string ('POSITIVE', 'NEGATIVE', 'NEUTRAL')
        """
        headlines = self.get_news_headlines(symbol)
        if not headlines:
            print(f'  No headlines found for {symbol} - defaulting to NEUTRAL')
            return 'NEUTRAL'
        sentiment, scores = self.score_sentiment(headlines)
        print(f'  News sentiment for {symbol}: {sentiment} '
              f'(VADER score: {scores["avg_score"]:+.3f}, '
              f'{scores["headlines_count"]} headlines)')
        return sentiment
