# agents/info_retrieval.py
# PURPOSE: Information Retrieval Agent — fetches news and scores sentiment
# USAGE:   Imported by orchestrator.py

import feedparser
import requests

class InfoRetrievalAgent:
    """
    This agent fetches the latest news headlines for a stock/crypto
    and scores them as POSITIVE, NEGATIVE, or NEUTRAL.
    This represents the 'information retrieval from internet' requirement.
    """

    # Yahoo Finance RSS feeds for each symbol
    NEWS_FEEDS = {
        'AAPL':    'https://finance.yahoo.com/rss/headline?s=AAPL',
        'MSFT':    'https://finance.yahoo.com/rss/headline?s=MSFT',
        'GOOGL':   'https://finance.yahoo.com/rss/headline?s=GOOGL',
        'BTC-USD': 'https://finance.yahoo.com/rss/headline?s=BTC-USD',
        'ETH-USD': 'https://finance.yahoo.com/rss/headline?s=ETH-USD',
    }

    # Words that suggest positive news
    POSITIVE_WORDS = [
        'surge', 'gain', 'rally', 'profit', 'beat', 'rise', 'up',
        'growth', 'record', 'high', 'strong', 'buy', 'upgrade',
        'bullish', 'recovery', 'positive', 'exceed', 'outperform'
    ]

    # Words that suggest negative news
    NEGATIVE_WORDS = [
        'fall', 'drop', 'loss', 'miss', 'crash', 'down', 'risk',
        'decline', 'bearish', 'warn', 'weak', 'sell', 'downgrade',
        'negative', 'below', 'concern', 'fear', 'uncertainty', 'cut'
    ]

    def get_news_headlines(self, symbol, max_headlines=15):
        """Fetches recent news headlines for the symbol. Returns a list of strings."""
        url = self.NEWS_FEEDS.get(symbol, '')
        headlines = []

        if not url:
            print(f'    No RSS feed for {symbol}')
            return headlines

        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_headlines]:
                headlines.append(entry.title)
        except Exception as e:
            print(f'    Could not fetch news for {symbol}: {e}')

        return headlines

    def score_sentiment(self, headlines):
        """
        Counts positive and negative words across all headlines.
        Returns: sentiment string and score dict
        """
        pos_count = 0
        neg_count = 0

        for headline in headlines:
            lower = headline.lower()
            pos_count += sum(1 for w in self.POSITIVE_WORDS if w in lower)
            neg_count += sum(1 for w in self.NEGATIVE_WORDS if w in lower)

        total = pos_count + neg_count
        if total == 0:
            return 'NEUTRAL', {'positive': 0, 'negative': 0, 'total': 0}

        # Sentiment is POSITIVE if more positive words found, else NEGATIVE
        sentiment = 'NEUTRAL'
        if pos_count > neg_count * 1.2:  # 20% more positive
            sentiment = 'POSITIVE'
        elif neg_count > pos_count * 1.2:
            sentiment = 'NEGATIVE'

        return sentiment, {'positive': pos_count, 'negative': neg_count, 'total': total}

    def get_sentiment(self, symbol):
        """
        Main method: fetch news + score sentiment for a symbol.
        Returns: sentiment string ('POSITIVE', 'NEGATIVE', 'NEUTRAL')
        """
        headlines = self.get_news_headlines(symbol)

        if not headlines:
            print(f'    No headlines found for {symbol} — defaulting to NEUTRAL')
            return 'NEUTRAL'

        sentiment, scores = self.score_sentiment(headlines)

        print(f'    News sentiment for {symbol}: {sentiment} '
              f'(+{scores["positive"]} / -{scores["negative"]} words, '
              f'{len(headlines)} headlines)')

        return sentiment
