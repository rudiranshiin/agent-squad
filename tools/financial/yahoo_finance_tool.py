"""
Yahoo Finance API Tool for retrieving real-time stock data and market information.
"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
from framework.mcp.tools.base_tool import CachedTool

logger = logging.getLogger(__name__)


class YahooFinanceTool(CachedTool):
    """
    Tool for retrieving comprehensive stock market data using Yahoo Finance API.

    Features:
    - Real-time stock prices and market data
    - Historical price data with multiple timeframes
    - Fundamental data (P/E, market cap, etc.)
    - Volume and trading statistics
    - 52-week ranges and moving averages
    - Dividend and split information
    """

    def __init__(self, cache_ttl: float = 60.0, **kwargs):
        super().__init__(
            name="yahoo_finance_api",
            description="Retrieve comprehensive stock market data from Yahoo Finance",
            version="1.0.0",
            cache_ttl=cache_ttl,  # Cache for 1 minute for real-time data
            **kwargs
        )
        self.category = "financial_data"

    async def execute(self, symbol: str, period: str = "1mo", include_fundamentals: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Retrieve stock data from Yahoo Finance.

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            include_fundamentals: Whether to include fundamental data

        Returns:
            Comprehensive stock data dictionary
        """
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol.upper())

            # Get basic info
            info = ticker.info
            if not info or 'symbol' not in info:
                raise ValueError(f"Invalid symbol or no data available for {symbol}")

            # Get historical data
            hist_data = ticker.history(period=period)
            if hist_data.empty:
                raise ValueError(f"No historical data available for {symbol}")

            # Get current price data
            current_data = hist_data.iloc[-1]
            previous_data = hist_data.iloc[-2] if len(hist_data) > 1 else current_data

            # Calculate basic metrics
            current_price = float(current_data['Close'])
            previous_close = float(previous_data['Close'])
            price_change = current_price - previous_close
            price_change_pct = (price_change / previous_close) * 100 if previous_close != 0 else 0.0

            # Build comprehensive response
            stock_data = {
                "symbol": symbol.upper(),
                "company_name": info.get('longName', symbol.upper()),
                "current_price": current_price,
                "previous_close": previous_close,
                "price_change": price_change,
                "price_change_percent": price_change_pct,
                "volume": int(current_data.get('Volume', 0)),
                "market_cap": info.get('marketCap'),
                "currency": info.get('currency', 'USD'),
                "exchange": info.get('exchange', 'Unknown'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "timestamp": datetime.now().isoformat(),
                "data_period": period
            }

            # Add price statistics
            high_52w = info.get('fiftyTwoWeekHigh')
            low_52w = info.get('fiftyTwoWeekLow')

            stock_data.update({
                "day_high": float(current_data.get('High', current_price)),
                "day_low": float(current_data.get('Low', current_price)),
                "fifty_two_week_high": high_52w,
                "fifty_two_week_low": low_52w,
                "avg_volume": info.get('averageVolume'),
                "avg_volume_10day": info.get('averageDailyVolume10Day')
            })

            # Calculate position within 52-week range
            if high_52w and low_52w and high_52w != low_52w:
                range_position = ((current_price - low_52w) / (high_52w - low_52w)) * 100
                stock_data["fifty_two_week_position_pct"] = range_position

            # Add moving averages if enough data
            if len(hist_data) >= 50:
                stock_data["sma_50"] = float(hist_data['Close'].rolling(50).mean().iloc[-1])
            if len(hist_data) >= 200:
                stock_data["sma_200"] = float(hist_data['Close'].rolling(200).mean().iloc[-1])

            # Add fundamental data if requested
            if include_fundamentals:
                fundamentals = self._extract_fundamental_data(info)
                stock_data["fundamentals"] = fundamentals

            # Add historical data summary
            stock_data["historical_summary"] = {
                "period": period,
                "data_points": len(hist_data),
                "start_date": hist_data.index[0].strftime('%Y-%m-%d'),
                "end_date": hist_data.index[-1].strftime('%Y-%m-%d'),
                "period_high": float(hist_data['High'].max()),
                "period_low": float(hist_data['Low'].min()),
                "period_volume_avg": float(hist_data['Volume'].mean()),
                "volatility": float(hist_data['Close'].pct_change().std() * 100)  # Daily volatility %
            }

            # Add recent price action (last 5 days)
            recent_data = hist_data.tail(5)
            stock_data["recent_price_action"] = [
                {
                    "date": date.strftime('%Y-%m-%d'),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                }
                for date, row in recent_data.iterrows()
            ]

            # Add dividend information if available
            try:
                dividends = ticker.dividends
                if not dividends.empty:
                    recent_dividend = dividends.tail(1)
                    stock_data["dividend_info"] = {
                        "last_dividend": float(recent_dividend.iloc[0]),
                        "last_dividend_date": recent_dividend.index[0].strftime('%Y-%m-%d'),
                        "dividend_yield": info.get('dividendYield'),
                        "payout_ratio": info.get('payoutRatio')
                    }
            except Exception as e:
                logger.debug(f"Could not retrieve dividend data for {symbol}: {e}")

            # Add analyst data if available
            analyst_data = self._get_analyst_data(info)
            if analyst_data:
                stock_data["analyst_data"] = analyst_data

            logger.info(f"Successfully retrieved data for {symbol}: ${current_price:.2f} ({price_change_pct:+.2f}%)")
            return stock_data

        except Exception as e:
            logger.error(f"Error retrieving data for {symbol}: {e}")
            raise

    def _extract_fundamental_data(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fundamental analysis data from ticker info."""
        fundamentals = {}

        # Valuation metrics
        fundamentals.update({
            "pe_ratio": info.get('trailingPE'),
            "forward_pe": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio'),
            "price_to_book": info.get('priceToBook'),
            "price_to_sales": info.get('priceToSalesTrailing12Months'),
            "enterprise_value": info.get('enterpriseValue'),
            "ev_to_revenue": info.get('enterpriseToRevenue'),
            "ev_to_ebitda": info.get('enterpriseToEbitda')
        })

        # Profitability metrics
        fundamentals.update({
            "profit_margin": info.get('profitMargins'),
            "operating_margin": info.get('operatingMargins'),
            "return_on_assets": info.get('returnOnAssets'),
            "return_on_equity": info.get('returnOnEquity'),
            "revenue_growth": info.get('revenueGrowth'),
            "earnings_growth": info.get('earningsGrowth')
        })

        # Financial health
        fundamentals.update({
            "total_cash": info.get('totalCash'),
            "total_debt": info.get('totalDebt'),
            "debt_to_equity": info.get('debtToEquity'),
            "current_ratio": info.get('currentRatio'),
            "quick_ratio": info.get('quickRatio'),
            "book_value": info.get('bookValue')
        })

        # Revenue and earnings
        fundamentals.update({
            "total_revenue": info.get('totalRevenue'),
            "revenue_per_share": info.get('revenuePerShare'),
            "earnings_per_share": info.get('trailingEps'),
            "forward_eps": info.get('forwardEps')
        })

        # Remove None values
        fundamentals = {k: v for k, v in fundamentals.items() if v is not None}

        return fundamentals

    def _get_analyst_data(self, info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract analyst recommendations and targets."""
        analyst_data = {}

        # Price targets
        target_high = info.get('targetHighPrice')
        target_low = info.get('targetLowPrice')
        target_mean = info.get('targetMeanPrice')

        if any([target_high, target_low, target_mean]):
            analyst_data["price_targets"] = {
                "high": target_high,
                "low": target_low,
                "mean": target_mean
            }

        # Recommendations
        recommendation = info.get('recommendationKey')
        if recommendation:
            analyst_data["recommendation"] = recommendation
            analyst_data["recommendation_mean"] = info.get('recommendationMean')

        # Number of analysts
        analyst_data["number_of_analysts"] = info.get('numberOfAnalystOpinions')

        return analyst_data if analyst_data else None

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., AAPL, TSLA, MSFT)",
                    "pattern": "^[A-Z]{1,5}$"
                },
                "period": {
                    "type": "string",
                    "description": "Time period for historical data",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                    "default": "1mo"
                },
                "include_fundamentals": {
                    "type": "boolean",
                    "description": "Whether to include fundamental analysis data",
                    "default": True
                }
            },
            "required": ["symbol"]
        }

    async def health_check(self) -> bool:
        """Perform health check by testing with a known symbol."""
        try:
            # Test with Apple stock
            test_data = await self.execute("AAPL", period="1d", include_fundamentals=False)
            return test_data is not None and "current_price" in test_data
        except Exception as e:
            logger.error(f"Yahoo Finance health check failed: {e}")
            return False


class MultiSymbolYahooFinanceTool(YahooFinanceTool):
    """
    Extended Yahoo Finance tool that can handle multiple symbols at once.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "multi_symbol_yahoo_finance"
        self.description = "Retrieve stock data for multiple symbols simultaneously"

    async def execute(self, symbols: List[str], period: str = "1mo", include_fundamentals: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Retrieve stock data for multiple symbols.

        Args:
            symbols: List of stock symbols
            period: Time period for historical data
            include_fundamentals: Whether to include fundamental data

        Returns:
            Dictionary with data for each symbol
        """
        if not symbols:
            raise ValueError("At least one symbol must be provided")

        if len(symbols) > 10:
            raise ValueError("Maximum 10 symbols allowed per request")

        results = {}
        errors = {}

        for symbol in symbols:
            try:
                symbol_data = await super().execute(
                    symbol=symbol,
                    period=period,
                    include_fundamentals=include_fundamentals,
                    **kwargs
                )
                results[symbol.upper()] = symbol_data
            except Exception as e:
                logger.error(f"Error retrieving data for {symbol}: {e}")
                errors[symbol.upper()] = str(e)

        response = {
            "symbols_data": results,
            "request_summary": {
                "symbols_requested": len(symbols),
                "symbols_successful": len(results),
                "symbols_failed": len(errors),
                "period": period,
                "timestamp": datetime.now().isoformat()
            }
        }

        if errors:
            response["errors"] = errors

        return response

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for multi-symbol tool parameters."""
        return {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^[A-Z]{1,5}$"
                    },
                    "description": "List of stock symbols (e.g., ['AAPL', 'TSLA', 'MSFT'])",
                    "minItems": 1,
                    "maxItems": 10
                },
                "period": {
                    "type": "string",
                    "description": "Time period for historical data",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                    "default": "1mo"
                },
                "include_fundamentals": {
                    "type": "boolean",
                    "description": "Whether to include fundamental analysis data",
                    "default": True
                }
            },
            "required": ["symbols"]
        }
