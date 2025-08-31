"""
Technical Indicators Tool for calculating various technical analysis indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from framework.mcp.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class TechnicalIndicatorsTool(BaseTool):
    """
    Tool for calculating comprehensive technical analysis indicators.

    Features:
    - Moving averages (SMA, EMA, WMA)
    - Momentum indicators (RSI, MACD, Stochastic)
    - Volatility indicators (Bollinger Bands, ATR)
    - Volume indicators (OBV, Volume SMA)
    - Support and resistance levels
    - Trend analysis and pattern recognition
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="technical_indicators",
            description="Calculate comprehensive technical analysis indicators for stock data",
            version="1.0.0",
            **kwargs
        )
        self.category = "technical_analysis"

    async def execute(
        self,
        stock_data: Dict[str, Any],
        indicators: List[str] = None,
        timeframe: str = "1mo",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Calculate technical indicators for stock data.

        Args:
            stock_data: Stock data from Yahoo Finance tool
            indicators: List of indicators to calculate (default: all)
            timeframe: Timeframe for analysis

        Returns:
            Dictionary containing calculated technical indicators
        """
        try:
            # Extract price data
            if "recent_price_action" not in stock_data:
                raise ValueError("Stock data must include recent_price_action")

            # Convert to DataFrame
            df = self._prepare_dataframe(stock_data)

            if len(df) < 14:  # Minimum data points for most indicators
                raise ValueError("Insufficient data points for technical analysis (minimum 14 required)")

            # Default indicators if none specified
            if indicators is None:
                indicators = ["sma", "ema", "rsi", "macd", "bollinger", "atr", "volume", "support_resistance"]

            # Calculate requested indicators
            results = {
                "symbol": stock_data.get("symbol"),
                "analysis_timestamp": datetime.now().isoformat(),
                "timeframe": timeframe,
                "data_points": len(df),
                "indicators": {}
            }

            for indicator in indicators:
                try:
                    if indicator == "sma":
                        results["indicators"]["sma"] = self._calculate_sma(df)
                    elif indicator == "ema":
                        results["indicators"]["ema"] = self._calculate_ema(df)
                    elif indicator == "rsi":
                        results["indicators"]["rsi"] = self._calculate_rsi(df)
                    elif indicator == "macd":
                        results["indicators"]["macd"] = self._calculate_macd(df)
                    elif indicator == "bollinger":
                        results["indicators"]["bollinger_bands"] = self._calculate_bollinger_bands(df)
                    elif indicator == "atr":
                        results["indicators"]["atr"] = self._calculate_atr(df)
                    elif indicator == "stochastic":
                        results["indicators"]["stochastic"] = self._calculate_stochastic(df)
                    elif indicator == "volume":
                        results["indicators"]["volume_analysis"] = self._calculate_volume_indicators(df)
                    elif indicator == "support_resistance":
                        results["indicators"]["support_resistance"] = self._calculate_support_resistance(df)
                    elif indicator == "fibonacci":
                        results["indicators"]["fibonacci"] = self._calculate_fibonacci_levels(df)

                except Exception as e:
                    logger.warning(f"Failed to calculate {indicator}: {e}")
                    results["indicators"][indicator] = {"error": str(e)}

            # Add overall technical summary
            results["technical_summary"] = self._generate_technical_summary(results["indicators"], df)

            logger.info(f"Calculated {len(results['indicators'])} technical indicators for {stock_data.get('symbol')}")
            return results

        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            raise

    def _prepare_dataframe(self, stock_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert stock data to pandas DataFrame."""
        price_action = stock_data["recent_price_action"]

        # If we have historical summary, try to get more data points
        historical = stock_data.get("historical_summary", {})

        # Create DataFrame from recent price action
        df = pd.DataFrame(price_action)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = df.sort_index()

        # Ensure numeric types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def _calculate_sma(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Simple Moving Averages."""
        sma_data = {}

        periods = [5, 10, 20, 50]
        for period in periods:
            if len(df) >= period:
                sma = df['close'].rolling(window=period).mean()
                current_sma = float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None

                sma_data[f"sma_{period}"] = {
                    "value": current_sma,
                    "signal": self._get_sma_signal(df['close'].iloc[-1], current_sma) if current_sma else "insufficient_data"
                }

        return sma_data

    def _calculate_ema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Exponential Moving Averages."""
        ema_data = {}

        periods = [12, 26, 50]
        for period in periods:
            if len(df) >= period:
                ema = df['close'].ewm(span=period).mean()
                current_ema = float(ema.iloc[-1])

                ema_data[f"ema_{period}"] = {
                    "value": current_ema,
                    "signal": self._get_sma_signal(df['close'].iloc[-1], current_ema)
                }

        return ema_data

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """Calculate Relative Strength Index."""
        if len(df) < period + 1:
            return {"error": "Insufficient data for RSI calculation"}

        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        current_rsi = float(rsi.iloc[-1])

        # Generate RSI signal
        if current_rsi >= 70:
            signal = "overbought"
        elif current_rsi <= 30:
            signal = "oversold"
        elif current_rsi >= 60:
            signal = "bullish"
        elif current_rsi <= 40:
            signal = "bearish"
        else:
            signal = "neutral"

        return {
            "value": current_rsi,
            "signal": signal,
            "interpretation": self._get_rsi_interpretation(current_rsi),
            "period": period
        }

    def _calculate_macd(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(df) < 26:
            return {"error": "Insufficient data for MACD calculation"}

        # Calculate MACD line
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        macd_line = ema_12 - ema_26

        # Calculate signal line
        signal_line = macd_line.ewm(span=9).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        current_macd = float(macd_line.iloc[-1])
        current_signal = float(signal_line.iloc[-1])
        current_histogram = float(histogram.iloc[-1])

        # Generate MACD signal
        if current_macd > current_signal and current_histogram > 0:
            signal = "bullish"
        elif current_macd < current_signal and current_histogram < 0:
            signal = "bearish"
        else:
            signal = "neutral"

        return {
            "macd_line": current_macd,
            "signal_line": current_signal,
            "histogram": current_histogram,
            "signal": signal,
            "interpretation": self._get_macd_interpretation(current_macd, current_signal, current_histogram)
        }

    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict[str, Any]:
        """Calculate Bollinger Bands."""
        if len(df) < period:
            return {"error": "Insufficient data for Bollinger Bands calculation"}

        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        current_price = df['close'].iloc[-1]
        current_upper = float(upper_band.iloc[-1])
        current_lower = float(lower_band.iloc[-1])
        current_middle = float(sma.iloc[-1])

        # Calculate band position
        band_width = current_upper - current_lower
        price_position = (current_price - current_lower) / band_width if band_width > 0 else 0.5

        # Generate signal
        if current_price >= current_upper:
            signal = "overbought"
        elif current_price <= current_lower:
            signal = "oversold"
        elif price_position > 0.8:
            signal = "approaching_upper"
        elif price_position < 0.2:
            signal = "approaching_lower"
        else:
            signal = "neutral"

        return {
            "upper_band": current_upper,
            "middle_band": current_middle,
            "lower_band": current_lower,
            "current_price": float(current_price),
            "band_width": band_width,
            "price_position": price_position,
            "signal": signal,
            "interpretation": self._get_bollinger_interpretation(price_position, signal)
        }

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """Calculate Average True Range."""
        if len(df) < period + 1:
            return {"error": "Insufficient data for ATR calculation"}

        # Calculate True Range
        df_copy = df.copy()
        df_copy['prev_close'] = df_copy['close'].shift(1)

        df_copy['tr1'] = df_copy['high'] - df_copy['low']
        df_copy['tr2'] = abs(df_copy['high'] - df_copy['prev_close'])
        df_copy['tr3'] = abs(df_copy['low'] - df_copy['prev_close'])

        df_copy['true_range'] = df_copy[['tr1', 'tr2', 'tr3']].max(axis=1)

        # Calculate ATR
        atr = df_copy['true_range'].rolling(window=period).mean()
        current_atr = float(atr.iloc[-1])
        current_price = float(df['close'].iloc[-1])

        # Calculate ATR as percentage of price
        atr_percentage = (current_atr / current_price) * 100 if current_price > 0 else 0

        return {
            "value": current_atr,
            "percentage": atr_percentage,
            "interpretation": self._get_atr_interpretation(atr_percentage),
            "period": period
        }

    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, Any]:
        """Calculate Stochastic Oscillator."""
        if len(df) < k_period:
            return {"error": "Insufficient data for Stochastic calculation"}

        # Calculate %K
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()

        k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))

        # Calculate %D (moving average of %K)
        d_percent = k_percent.rolling(window=d_period).mean()

        current_k = float(k_percent.iloc[-1])
        current_d = float(d_percent.iloc[-1])

        # Generate signal
        if current_k >= 80 and current_d >= 80:
            signal = "overbought"
        elif current_k <= 20 and current_d <= 20:
            signal = "oversold"
        elif current_k > current_d:
            signal = "bullish"
        elif current_k < current_d:
            signal = "bearish"
        else:
            signal = "neutral"

        return {
            "k_percent": current_k,
            "d_percent": current_d,
            "signal": signal,
            "interpretation": self._get_stochastic_interpretation(current_k, current_d)
        }

    def _calculate_volume_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volume-based indicators."""
        volume_data = {}

        # Volume moving averages
        if len(df) >= 10:
            volume_sma_10 = df['volume'].rolling(window=10).mean()
            current_volume = df['volume'].iloc[-1]
            avg_volume = float(volume_sma_10.iloc[-1])

            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

            volume_data["volume_analysis"] = {
                "current_volume": int(current_volume),
                "average_volume_10d": int(avg_volume),
                "volume_ratio": volume_ratio,
                "signal": self._get_volume_signal(volume_ratio)
            }

        # On-Balance Volume (OBV)
        if len(df) >= 2:
            obv = self._calculate_obv(df)
            volume_data["obv"] = {
                "value": float(obv.iloc[-1]),
                "trend": self._get_obv_trend(obv)
            }

        return volume_data

    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume."""
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df['volume'].iloc[0]

        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]

        return obv

    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate support and resistance levels."""
        if len(df) < 5:
            return {"error": "Insufficient data for support/resistance calculation"}

        # Find local highs and lows
        highs = df['high'].rolling(window=3, center=True).max()
        lows = df['low'].rolling(window=3, center=True).min()

        # Identify pivot points
        pivot_highs = df['high'][df['high'] == highs]
        pivot_lows = df['low'][df['low'] == lows]

        # Calculate current support and resistance
        current_price = df['close'].iloc[-1]

        # Find nearest support (highest low below current price)
        support_levels = pivot_lows[pivot_lows < current_price]
        nearest_support = float(support_levels.max()) if len(support_levels) > 0 else None

        # Find nearest resistance (lowest high above current price)
        resistance_levels = pivot_highs[pivot_highs > current_price]
        nearest_resistance = float(resistance_levels.min()) if len(resistance_levels) > 0 else None

        return {
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            "support_strength": len(support_levels) if support_levels is not None else 0,
            "resistance_strength": len(resistance_levels) if resistance_levels is not None else 0,
            "current_price": float(current_price)
        }

    def _calculate_fibonacci_levels(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Fibonacci retracement levels."""
        if len(df) < 10:
            return {"error": "Insufficient data for Fibonacci calculation"}

        # Find recent high and low
        recent_high = df['high'].max()
        recent_low = df['low'].min()

        # Calculate Fibonacci levels
        diff = recent_high - recent_low

        fib_levels = {
            "0.0": recent_high,
            "23.6": recent_high - (0.236 * diff),
            "38.2": recent_high - (0.382 * diff),
            "50.0": recent_high - (0.5 * diff),
            "61.8": recent_high - (0.618 * diff),
            "78.6": recent_high - (0.786 * diff),
            "100.0": recent_low
        }

        current_price = float(df['close'].iloc[-1])

        return {
            "levels": fib_levels,
            "recent_high": float(recent_high),
            "recent_low": float(recent_low),
            "current_price": current_price,
            "nearest_level": self._find_nearest_fib_level(current_price, fib_levels)
        }

    def _generate_technical_summary(self, indicators: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Generate overall technical analysis summary."""
        signals = []

        # Collect signals from all indicators
        for indicator_name, indicator_data in indicators.items():
            if isinstance(indicator_data, dict) and "signal" in indicator_data:
                signals.append(indicator_data["signal"])
            elif isinstance(indicator_data, dict):
                # Check for nested signals
                for key, value in indicator_data.items():
                    if isinstance(value, dict) and "signal" in value:
                        signals.append(value["signal"])

        # Count signal types
        bullish_signals = signals.count("bullish") + signals.count("buy")
        bearish_signals = signals.count("bearish") + signals.count("sell")
        neutral_signals = signals.count("neutral") + signals.count("hold")

        total_signals = len(signals)

        # Determine overall sentiment
        if bullish_signals > bearish_signals:
            overall_sentiment = "bullish"
        elif bearish_signals > bullish_signals:
            overall_sentiment = "bearish"
        else:
            overall_sentiment = "neutral"

        # Calculate confidence
        max_signals = max(bullish_signals, bearish_signals, neutral_signals)
        confidence = (max_signals / total_signals) if total_signals > 0 else 0.0

        return {
            "overall_sentiment": overall_sentiment,
            "confidence": confidence,
            "signal_distribution": {
                "bullish": bullish_signals,
                "bearish": bearish_signals,
                "neutral": neutral_signals,
                "total": total_signals
            },
            "trend_strength": self._calculate_trend_strength(df),
            "volatility_assessment": self._assess_volatility(df)
        }

    # Signal interpretation methods
    def _get_sma_signal(self, current_price: float, sma_value: float) -> str:
        """Get SMA signal based on price position."""
        if current_price > sma_value * 1.02:
            return "bullish"
        elif current_price < sma_value * 0.98:
            return "bearish"
        else:
            return "neutral"

    def _get_rsi_interpretation(self, rsi_value: float) -> str:
        """Get RSI interpretation."""
        if rsi_value >= 70:
            return "Stock may be overbought, potential sell signal"
        elif rsi_value <= 30:
            return "Stock may be oversold, potential buy signal"
        elif rsi_value >= 50:
            return "Bullish momentum"
        else:
            return "Bearish momentum"

    def _get_macd_interpretation(self, macd: float, signal: float, histogram: float) -> str:
        """Get MACD interpretation."""
        if macd > signal and histogram > 0:
            return "Bullish momentum strengthening"
        elif macd < signal and histogram < 0:
            return "Bearish momentum strengthening"
        elif macd > signal and histogram < 0:
            return "Bullish momentum weakening"
        else:
            return "Bearish momentum weakening"

    def _get_bollinger_interpretation(self, position: float, signal: str) -> str:
        """Get Bollinger Bands interpretation."""
        if signal == "overbought":
            return "Price at upper band, potential reversal"
        elif signal == "oversold":
            return "Price at lower band, potential bounce"
        elif position > 0.7:
            return "Price in upper region, strong momentum"
        elif position < 0.3:
            return "Price in lower region, weak momentum"
        else:
            return "Price in middle region, neutral"

    def _get_atr_interpretation(self, atr_pct: float) -> str:
        """Get ATR interpretation."""
        if atr_pct > 3.0:
            return "High volatility"
        elif atr_pct > 1.5:
            return "Moderate volatility"
        else:
            return "Low volatility"

    def _get_stochastic_interpretation(self, k: float, d: float) -> str:
        """Get Stochastic interpretation."""
        if k >= 80 and d >= 80:
            return "Overbought conditions"
        elif k <= 20 and d <= 20:
            return "Oversold conditions"
        elif k > d:
            return "Bullish crossover"
        else:
            return "Bearish crossover"

    def _get_volume_signal(self, volume_ratio: float) -> str:
        """Get volume signal."""
        if volume_ratio >= 2.0:
            return "very_high_volume"
        elif volume_ratio >= 1.5:
            return "high_volume"
        elif volume_ratio >= 0.8:
            return "normal_volume"
        else:
            return "low_volume"

    def _get_obv_trend(self, obv: pd.Series) -> str:
        """Get OBV trend."""
        if len(obv) < 3:
            return "insufficient_data"

        recent_obv = obv.tail(3)
        if recent_obv.iloc[-1] > recent_obv.iloc[-2] > recent_obv.iloc[-3]:
            return "rising"
        elif recent_obv.iloc[-1] < recent_obv.iloc[-2] < recent_obv.iloc[-3]:
            return "falling"
        else:
            return "sideways"

    def _find_nearest_fib_level(self, current_price: float, fib_levels: Dict[str, float]) -> Dict[str, Any]:
        """Find nearest Fibonacci level."""
        distances = {level: abs(current_price - price) for level, price in fib_levels.items()}
        nearest_level = min(distances, key=distances.get)

        return {
            "level": nearest_level,
            "price": fib_levels[nearest_level],
            "distance": distances[nearest_level]
        }

    def _calculate_trend_strength(self, df: pd.DataFrame) -> str:
        """Calculate trend strength."""
        if len(df) < 5:
            return "insufficient_data"

        # Simple trend calculation based on price movement
        price_change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]

        if abs(price_change) > 0.1:
            return "strong"
        elif abs(price_change) > 0.05:
            return "moderate"
        else:
            return "weak"

    def _assess_volatility(self, df: pd.DataFrame) -> str:
        """Assess volatility level."""
        if len(df) < 5:
            return "insufficient_data"

        # Calculate daily returns volatility
        returns = df['close'].pct_change().dropna()
        volatility = returns.std()

        if volatility > 0.05:
            return "high"
        elif volatility > 0.02:
            return "moderate"
        else:
            return "low"

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "stock_data": {
                    "type": "object",
                    "description": "Stock data from Yahoo Finance tool containing recent_price_action"
                },
                "indicators": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["sma", "ema", "rsi", "macd", "bollinger", "atr", "stochastic", "volume", "support_resistance", "fibonacci"]
                    },
                    "description": "List of technical indicators to calculate",
                    "default": ["sma", "ema", "rsi", "macd", "bollinger", "atr", "volume", "support_resistance"]
                },
                "timeframe": {
                    "type": "string",
                    "description": "Timeframe for analysis",
                    "default": "1mo"
                }
            },
            "required": ["stock_data"]
        }

    async def health_check(self) -> bool:
        """Perform health check with sample data."""
        try:
            # Create sample stock data
            sample_data = {
                "symbol": "TEST",
                "recent_price_action": [
                    {"date": "2024-01-01", "open": 100, "high": 105, "low": 98, "close": 103, "volume": 1000000},
                    {"date": "2024-01-02", "open": 103, "high": 107, "low": 101, "close": 106, "volume": 1200000},
                    {"date": "2024-01-03", "open": 106, "high": 108, "low": 104, "close": 105, "volume": 900000},
                    {"date": "2024-01-04", "open": 105, "high": 109, "low": 103, "close": 108, "volume": 1100000},
                    {"date": "2024-01-05", "open": 108, "high": 112, "low": 106, "close": 110, "volume": 1300000},
                    {"date": "2024-01-06", "open": 110, "high": 113, "low": 108, "close": 111, "volume": 1000000},
                    {"date": "2024-01-07", "open": 111, "high": 114, "low": 109, "close": 112, "volume": 1150000},
                    {"date": "2024-01-08", "open": 112, "high": 115, "low": 110, "close": 113, "volume": 1050000},
                    {"date": "2024-01-09", "open": 113, "high": 116, "low": 111, "close": 114, "volume": 1250000},
                    {"date": "2024-01-10", "open": 114, "high": 117, "low": 112, "close": 115, "volume": 1100000},
                    {"date": "2024-01-11", "open": 115, "high": 118, "low": 113, "close": 116, "volume": 1200000},
                    {"date": "2024-01-12", "open": 116, "high": 119, "low": 114, "close": 117, "volume": 1000000},
                    {"date": "2024-01-13", "open": 117, "high": 120, "low": 115, "close": 118, "volume": 1300000},
                    {"date": "2024-01-14", "open": 118, "high": 121, "low": 116, "close": 119, "volume": 1150000},
                    {"date": "2024-01-15", "open": 119, "high": 122, "low": 117, "close": 120, "volume": 1250000}
                ]
            }

            result = await self.execute(sample_data, indicators=["sma", "rsi"])
            return "indicators" in result and len(result["indicators"]) > 0

        except Exception as e:
            logger.error(f"Technical indicators health check failed: {e}")
            return False
