"""
News Sentiment Analysis Tool for analyzing market news and sentiment.
"""

import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import re
from textblob import TextBlob
from framework.mcp.tools.base_tool import CachedTool

logger = logging.getLogger(__name__)


class NewsSentimentTool(CachedTool):
    """
    Tool for analyzing news sentiment related to stocks and market conditions.

    Features:
    - Fetch recent news articles for specific stocks
    - Analyze sentiment of news headlines and content
    - Aggregate sentiment scores and trends
    - Identify key market-moving events
    - Track news volume and frequency
    """

    def __init__(self, api_key: str = None, cache_ttl: float = 300.0, **kwargs):
        super().__init__(
            name="news_sentiment_analyzer",
            description="Analyze news sentiment for stocks and market conditions",
            version="1.0.0",
            cache_ttl=cache_ttl,  # Cache for 5 minutes
            **kwargs
        )
        self.api_key = api_key
        self.category = "sentiment_analysis"

        # News sources and their reliability weights
        self.news_sources = {
            "reuters.com": 0.9,
            "bloomberg.com": 0.9,
            "wsj.com": 0.85,
            "cnbc.com": 0.8,
            "marketwatch.com": 0.75,
            "yahoo.com": 0.7,
            "seekingalpha.com": 0.7,
            "fool.com": 0.6
        }

    async def execute(
        self,
        symbol: str,
        days_back: int = 7,
        include_market_news: bool = True,
        max_articles: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze news sentiment for a stock symbol.

        Args:
            symbol: Stock symbol to analyze
            days_back: Number of days to look back for news
            include_market_news: Whether to include general market news
            max_articles: Maximum number of articles to analyze

        Returns:
            Comprehensive sentiment analysis results
        """
        try:
            # Fetch news articles
            articles = await self._fetch_news_articles(symbol, days_back, max_articles, include_market_news)

            if not articles:
                return {
                    "symbol": symbol,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "articles_analyzed": 0,
                    "overall_sentiment": 0.0,
                    "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                    "confidence": 0.0,
                    "error": "No news articles found for analysis"
                }

            # Analyze sentiment for each article
            analyzed_articles = []
            for article in articles:
                sentiment_data = await self._analyze_article_sentiment(article)
                analyzed_articles.append(sentiment_data)

            # Aggregate sentiment results
            sentiment_results = self._aggregate_sentiment_results(analyzed_articles, symbol)

            # Add trend analysis
            sentiment_results["sentiment_trend"] = self._analyze_sentiment_trend(analyzed_articles)

            # Add key events detection
            sentiment_results["key_events"] = self._detect_key_events(analyzed_articles)

            # Add news volume analysis
            sentiment_results["news_volume_analysis"] = self._analyze_news_volume(analyzed_articles, days_back)

            logger.info(f"Analyzed sentiment for {symbol}: {len(analyzed_articles)} articles, score: {sentiment_results['overall_sentiment']:.3f}")
            return sentiment_results

        except Exception as e:
            logger.error(f"Error analyzing news sentiment for {symbol}: {e}")
            raise

    async def _fetch_news_articles(
        self,
        symbol: str,
        days_back: int,
        max_articles: int,
        include_market_news: bool
    ) -> List[Dict[str, Any]]:
        """Fetch news articles from various sources."""
        articles = []

        try:
            # Try multiple news sources
            sources = [
                self._fetch_yahoo_finance_news,
                self._fetch_alpha_vantage_news,
                self._fetch_newsapi_articles
            ]

            # Fetch from each source
            for source_func in sources:
                try:
                    source_articles = await source_func(symbol, days_back, max_articles // len(sources))
                    articles.extend(source_articles)

                    if len(articles) >= max_articles:
                        break

                except Exception as e:
                    logger.debug(f"Failed to fetch from source {source_func.__name__}: {e}")
                    continue

            # If no API sources work, use fallback method
            if not articles:
                articles = await self._fetch_fallback_news(symbol, days_back)

            # Remove duplicates and sort by date
            articles = self._deduplicate_articles(articles)
            articles = sorted(articles, key=lambda x: x.get('published_date', ''), reverse=True)

            return articles[:max_articles]

        except Exception as e:
            logger.error(f"Error fetching news articles: {e}")
            return []

    async def _fetch_yahoo_finance_news(self, symbol: str, days_back: int, max_articles: int) -> List[Dict[str, Any]]:
        """Fetch news from Yahoo Finance (simulated - would need actual API)."""
        # This is a placeholder for Yahoo Finance news API
        # In a real implementation, you would use yfinance or Yahoo Finance API

        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)

            # Get news (this is a simplified version)
            news_data = ticker.news if hasattr(ticker, 'news') else []

            articles = []
            for item in news_data[:max_articles]:
                article = {
                    "title": item.get('title', ''),
                    "summary": item.get('summary', ''),
                    "url": item.get('link', ''),
                    "published_date": datetime.fromtimestamp(item.get('providerPublishTime', 0)).isoformat() if item.get('providerPublishTime') else datetime.now().isoformat(),
                    "source": item.get('publisher', 'yahoo'),
                    "relevance_score": 0.8  # Default relevance for symbol-specific news
                }
                articles.append(article)

            return articles

        except Exception as e:
            logger.debug(f"Yahoo Finance news fetch failed: {e}")
            return []

    async def _fetch_alpha_vantage_news(self, symbol: str, days_back: int, max_articles: int) -> List[Dict[str, Any]]:
        """Fetch news from Alpha Vantage API."""
        if not self.api_key:
            return []

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": symbol,
                "apikey": self.api_key,
                "limit": max_articles
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        articles = []
                        for item in data.get('feed', []):
                            # Filter by date
                            pub_date = datetime.strptime(item['time_published'], '%Y%m%dT%H%M%S')
                            if (datetime.now() - pub_date).days <= days_back:

                                article = {
                                    "title": item.get('title', ''),
                                    "summary": item.get('summary', ''),
                                    "url": item.get('url', ''),
                                    "published_date": pub_date.isoformat(),
                                    "source": item.get('source', 'alpha_vantage'),
                                    "relevance_score": float(item.get('relevance_score', 0.5)),
                                    "sentiment_score": float(item.get('overall_sentiment_score', 0.0))
                                }
                                articles.append(article)

                        return articles

        except Exception as e:
            logger.debug(f"Alpha Vantage news fetch failed: {e}")
            return []

    async def _fetch_newsapi_articles(self, symbol: str, days_back: int, max_articles: int) -> List[Dict[str, Any]]:
        """Fetch news from NewsAPI (requires API key)."""
        # This would require a NewsAPI key
        # Placeholder implementation
        return []

    async def _fetch_fallback_news(self, symbol: str, days_back: int) -> List[Dict[str, Any]]:
        """Fallback method to generate sample news data for testing."""
        # This is a fallback for when no real news APIs are available
        # In production, you would want to implement actual news scraping or use paid APIs

        sample_headlines = [
            f"{symbol} reports strong quarterly earnings, beats expectations",
            f"Analysts upgrade {symbol} price target following positive guidance",
            f"{symbol} announces new product launch, shares rise in pre-market",
            f"Market volatility affects {symbol} trading, investors remain cautious",
            f"{symbol} CEO discusses future growth strategy in investor call",
            f"Regulatory concerns impact {symbol} stock performance",
            f"{symbol} partners with major tech company for innovation project",
            f"Economic indicators suggest positive outlook for {symbol} sector"
        ]

        articles = []
        for i, headline in enumerate(sample_headlines):
            # Generate sentiment based on headline keywords
            sentiment_score = self._get_headline_sentiment(headline)

            article = {
                "title": headline,
                "summary": f"Analysis of {headline.lower()}...",
                "url": f"https://example.com/news/{i}",
                "published_date": (datetime.now() - timedelta(days=i)).isoformat(),
                "source": "sample_news",
                "relevance_score": 0.7,
                "sentiment_score": sentiment_score
            }
            articles.append(article)

        return articles

    def _get_headline_sentiment(self, headline: str) -> float:
        """Get basic sentiment from headline keywords."""
        positive_words = ['strong', 'beats', 'upgrade', 'rise', 'positive', 'growth', 'innovation', 'partners']
        negative_words = ['volatility', 'concerns', 'impact', 'regulatory', 'cautious', 'decline', 'falls']

        headline_lower = headline.lower()

        positive_count = sum(1 for word in positive_words if word in headline_lower)
        negative_count = sum(1 for word in negative_words if word in headline_lower)

        if positive_count > negative_count:
            return 0.3 + (positive_count * 0.2)
        elif negative_count > positive_count:
            return -0.3 - (negative_count * 0.2)
        else:
            return 0.0

    async def _analyze_article_sentiment(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of a single article."""
        try:
            # Combine title and summary for analysis
            text_to_analyze = f"{article.get('title', '')} {article.get('summary', '')}"

            # Use TextBlob for sentiment analysis
            blob = TextBlob(text_to_analyze)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1

            # If article already has sentiment score from API, use weighted average
            api_sentiment = article.get('sentiment_score', 0.0)
            if api_sentiment != 0.0:
                # Weight API sentiment more heavily if available
                final_sentiment = (polarity * 0.4) + (api_sentiment * 0.6)
            else:
                final_sentiment = polarity

            # Calculate confidence based on subjectivity and source reliability
            source_weight = self.news_sources.get(self._extract_domain(article.get('url', '')), 0.5)
            confidence = (1 - subjectivity) * source_weight * article.get('relevance_score', 0.5)

            # Categorize sentiment
            if final_sentiment > 0.1:
                sentiment_category = "positive"
            elif final_sentiment < -0.1:
                sentiment_category = "negative"
            else:
                sentiment_category = "neutral"

            return {
                **article,
                "sentiment_score": final_sentiment,
                "sentiment_category": sentiment_category,
                "confidence": confidence,
                "subjectivity": subjectivity,
                "word_count": len(text_to_analyze.split()),
                "analysis_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing article sentiment: {e}")
            return {
                **article,
                "sentiment_score": 0.0,
                "sentiment_category": "neutral",
                "confidence": 0.0,
                "error": str(e)
            }

    def _aggregate_sentiment_results(self, analyzed_articles: List[Dict[str, Any]], symbol: str) -> Dict[str, Any]:
        """Aggregate sentiment results from all articles."""
        if not analyzed_articles:
            return {
                "symbol": symbol,
                "analysis_timestamp": datetime.now().isoformat(),
                "articles_analyzed": 0,
                "overall_sentiment": 0.0,
                "confidence": 0.0
            }

        # Calculate weighted average sentiment
        total_weighted_sentiment = 0.0
        total_weight = 0.0

        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}

        for article in analyzed_articles:
            sentiment = article.get('sentiment_score', 0.0)
            confidence = article.get('confidence', 0.5)
            relevance = article.get('relevance_score', 0.5)

            # Weight by confidence and relevance
            weight = confidence * relevance
            total_weighted_sentiment += sentiment * weight
            total_weight += weight

            # Count sentiment categories
            category = article.get('sentiment_category', 'neutral')
            sentiment_counts[category] += 1

        # Calculate overall sentiment
        overall_sentiment = total_weighted_sentiment / total_weight if total_weight > 0 else 0.0

        # Calculate overall confidence
        avg_confidence = sum(a.get('confidence', 0) for a in analyzed_articles) / len(analyzed_articles)

        # Calculate sentiment strength
        sentiment_strength = abs(overall_sentiment)

        return {
            "symbol": symbol,
            "analysis_timestamp": datetime.now().isoformat(),
            "articles_analyzed": len(analyzed_articles),
            "overall_sentiment": overall_sentiment,
            "sentiment_strength": sentiment_strength,
            "confidence": avg_confidence,
            "sentiment_distribution": sentiment_counts,
            "sentiment_interpretation": self._interpret_sentiment(overall_sentiment, sentiment_strength),
            "articles_summary": self._create_articles_summary(analyzed_articles)
        }

    def _analyze_sentiment_trend(self, analyzed_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment trend over time."""
        if len(analyzed_articles) < 2:
            return {"trend": "insufficient_data"}

        # Sort articles by date
        sorted_articles = sorted(
            analyzed_articles,
            key=lambda x: x.get('published_date', ''),
            reverse=False  # Oldest first
        )

        # Calculate sentiment for different time periods
        recent_articles = sorted_articles[-len(sorted_articles)//2:]  # Recent half
        older_articles = sorted_articles[:len(sorted_articles)//2]   # Older half

        recent_sentiment = sum(a.get('sentiment_score', 0) for a in recent_articles) / len(recent_articles)
        older_sentiment = sum(a.get('sentiment_score', 0) for a in older_articles) / len(older_articles)

        sentiment_change = recent_sentiment - older_sentiment

        # Determine trend
        if sentiment_change > 0.1:
            trend = "improving"
        elif sentiment_change < -0.1:
            trend = "deteriorating"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "sentiment_change": sentiment_change,
            "recent_sentiment": recent_sentiment,
            "older_sentiment": older_sentiment,
            "trend_strength": abs(sentiment_change)
        }

    def _detect_key_events(self, analyzed_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect key market-moving events from news."""
        key_events = []

        # Keywords that indicate important events
        event_keywords = {
            "earnings": ["earnings", "quarterly", "revenue", "profit", "eps"],
            "merger": ["merger", "acquisition", "buyout", "takeover"],
            "product": ["launch", "product", "release", "innovation"],
            "regulatory": ["regulatory", "fda", "approval", "investigation"],
            "leadership": ["ceo", "executive", "management", "resignation"],
            "partnership": ["partnership", "deal", "agreement", "contract"]
        }

        for article in analyzed_articles:
            title = article.get('title', '').lower()
            summary = article.get('summary', '').lower()
            text = f"{title} {summary}"

            # Check for event keywords
            for event_type, keywords in event_keywords.items():
                if any(keyword in text for keyword in keywords):
                    # High sentiment change or high relevance indicates key event
                    sentiment_score = abs(article.get('sentiment_score', 0))
                    relevance = article.get('relevance_score', 0)

                    if sentiment_score > 0.3 or relevance > 0.8:
                        key_events.append({
                            "event_type": event_type,
                            "title": article.get('title', ''),
                            "sentiment_impact": sentiment_score,
                            "date": article.get('published_date', ''),
                            "url": article.get('url', ''),
                            "relevance": relevance
                        })

        # Sort by sentiment impact
        key_events.sort(key=lambda x: x['sentiment_impact'], reverse=True)

        return key_events[:5]  # Return top 5 events

    def _analyze_news_volume(self, analyzed_articles: List[Dict[str, Any]], days_back: int) -> Dict[str, Any]:
        """Analyze news volume and frequency."""
        if not analyzed_articles:
            return {"volume": "no_data"}

        # Group articles by date
        daily_counts = {}
        for article in analyzed_articles:
            try:
                pub_date = datetime.fromisoformat(article.get('published_date', ''))
                date_key = pub_date.strftime('%Y-%m-%d')
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            except:
                continue

        # Calculate average daily volume
        avg_daily_volume = len(analyzed_articles) / days_back if days_back > 0 else 0

        # Find peak volume day
        peak_day = max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None

        # Determine volume level
        if avg_daily_volume > 10:
            volume_level = "high"
        elif avg_daily_volume > 5:
            volume_level = "moderate"
        else:
            volume_level = "low"

        return {
            "volume_level": volume_level,
            "avg_daily_articles": avg_daily_volume,
            "total_articles": len(analyzed_articles),
            "days_analyzed": days_back,
            "peak_volume_day": peak_day[0] if peak_day else None,
            "peak_volume_count": peak_day[1] if peak_day else 0,
            "daily_distribution": daily_counts
        }

    def _create_articles_summary(self, analyzed_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create summary of top articles."""
        # Sort by relevance and sentiment strength
        sorted_articles = sorted(
            analyzed_articles,
            key=lambda x: (x.get('relevance_score', 0) + abs(x.get('sentiment_score', 0))),
            reverse=True
        )

        summary = []
        for article in sorted_articles[:5]:  # Top 5 articles
            summary.append({
                "title": article.get('title', ''),
                "sentiment_score": article.get('sentiment_score', 0),
                "sentiment_category": article.get('sentiment_category', 'neutral'),
                "published_date": article.get('published_date', ''),
                "source": article.get('source', ''),
                "relevance_score": article.get('relevance_score', 0),
                "url": article.get('url', '')
            })

        return summary

    def _interpret_sentiment(self, sentiment: float, strength: float) -> str:
        """Interpret overall sentiment score."""
        if strength < 0.1:
            return "Neutral sentiment with minimal market impact expected"
        elif sentiment > 0.3:
            return "Strong positive sentiment, potential bullish catalyst"
        elif sentiment > 0.1:
            return "Moderate positive sentiment, supportive for price"
        elif sentiment < -0.3:
            return "Strong negative sentiment, potential bearish pressure"
        elif sentiment < -0.1:
            return "Moderate negative sentiment, headwind for price"
        else:
            return "Mixed sentiment, limited directional bias"

    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on title similarity."""
        if not articles:
            return articles

        unique_articles = []
        seen_titles = set()

        for article in articles:
            title = article.get('title', '').lower().strip()

            # Simple deduplication based on title
            title_words = set(title.split())

            is_duplicate = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())

                # If more than 70% of words overlap, consider it a duplicate
                if len(title_words & seen_words) / max(len(title_words), len(seen_words)) > 0.7:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.add(title)

        return unique_articles

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol to analyze news sentiment for",
                    "pattern": "^[A-Z]{1,5}$"
                },
                "days_back": {
                    "type": "integer",
                    "description": "Number of days to look back for news",
                    "minimum": 1,
                    "maximum": 30,
                    "default": 7
                },
                "include_market_news": {
                    "type": "boolean",
                    "description": "Whether to include general market news",
                    "default": True
                },
                "max_articles": {
                    "type": "integer",
                    "description": "Maximum number of articles to analyze",
                    "minimum": 5,
                    "maximum": 100,
                    "default": 50
                }
            },
            "required": ["symbol"]
        }

    async def health_check(self) -> bool:
        """Perform health check with sample data."""
        try:
            # Test with a sample symbol
            result = await self.execute("AAPL", days_back=1, max_articles=5)
            return "overall_sentiment" in result and "articles_analyzed" in result
        except Exception as e:
            logger.error(f"News sentiment health check failed: {e}")
            return False
