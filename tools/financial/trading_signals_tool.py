"""
Trading Signals Generator Tool for creating actionable trading recommendations.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import numpy as np
from framework.mcp.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class TradingSignalsTool(BaseTool):
    """
    Tool for generating comprehensive trading signals and recommendations.

    Features:
    - Multi-factor signal generation
    - Technical analysis integration
    - Sentiment-based signals
    - Risk-adjusted recommendations
    - Entry/exit point suggestions
    - Signal strength scoring
    - Confidence levels
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="trading_signal_generator",
            description="Generate comprehensive trading signals and recommendations",
            version="1.0.0",
            **kwargs
        )
        self.category = "trading_signals"

    async def execute(
        self,
        symbol: str,
        stock_data: Dict[str, Any],
        technical_analysis: Dict[str, Any] = None,
        news_sentiment: Dict[str, Any] = None,
        risk_assessment: Dict[str, Any] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on multiple data sources.

        Args:
            symbol: Stock symbol
            stock_data: Stock market data
            technical_analysis: Technical indicators data
            news_sentiment: News sentiment analysis
            risk_assessment: Risk analysis results

        Returns:
            List of trading signals with recommendations
        """
        try:
            signals = []

            # Generate technical signals
            if technical_analysis:
                tech_signals = self._generate_technical_signals(symbol, stock_data, technical_analysis)
                signals.extend(tech_signals)

            # Generate sentiment signals
            if news_sentiment:
                sentiment_signals = self._generate_sentiment_signals(symbol, news_sentiment)
                signals.extend(sentiment_signals)

            # Generate momentum signals
            momentum_signals = self._generate_momentum_signals(symbol, stock_data)
            signals.extend(momentum_signals)

            # Generate volume signals
            volume_signals = self._generate_volume_signals(symbol, stock_data)
            signals.extend(volume_signals)

            # Generate price action signals
            price_signals = self._generate_price_action_signals(symbol, stock_data)
            signals.extend(price_signals)

            # Adjust signals based on risk assessment
            if risk_assessment:
                signals = self._adjust_signals_for_risk(signals, risk_assessment)

            # Aggregate and rank signals
            final_signals = self._aggregate_and_rank_signals(signals, symbol)

            # Add meta information
            for signal in final_signals:
                signal["generated_at"] = datetime.now().isoformat()
                signal["symbol"] = symbol

            logger.info(f"Generated {len(final_signals)} trading signals for {symbol}")
            return final_signals

        except Exception as e:
            logger.error(f"Error generating trading signals for {symbol}: {e}")
            raise

    def _generate_technical_signals(
        self,
        symbol: str,
        stock_data: Dict[str, Any],
        technical_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate signals based on technical indicators."""
        signals = []
        indicators = technical_analysis.get("indicators", {})
        current_price = stock_data.get("current_price", 0)

        # RSI signals
        rsi_data = indicators.get("rsi", {})
        if isinstance(rsi_data, dict) and "value" in rsi_data:
            rsi_value = rsi_data["value"]

            if rsi_value <= 30:
                signals.append({
                    "type": "technical",
                    "indicator": "RSI",
                    "action": "buy",
                    "strength": min((30 - rsi_value) / 10, 1.0),
                    "reason": f"RSI oversold at {rsi_value:.1f}",
                    "entry_price": current_price,
                    "confidence": 0.7
                })
            elif rsi_value >= 70:
                signals.append({
                    "type": "technical",
                    "indicator": "RSI",
                    "action": "sell",
                    "strength": min((rsi_value - 70) / 10, 1.0),
                    "reason": f"RSI overbought at {rsi_value:.1f}",
                    "entry_price": current_price,
                    "confidence": 0.7
                })

        # MACD signals
        macd_data = indicators.get("macd", {})
        if isinstance(macd_data, dict) and "signal" in macd_data:
            macd_signal = macd_data["signal"]
            histogram = macd_data.get("histogram", 0)

            if macd_signal == "bullish" and histogram > 0:
                signals.append({
                    "type": "technical",
                    "indicator": "MACD",
                    "action": "buy",
                    "strength": min(abs(histogram) * 10, 1.0),
                    "reason": "MACD bullish crossover with positive histogram",
                    "entry_price": current_price,
                    "confidence": 0.75
                })
            elif macd_signal == "bearish" and histogram < 0:
                signals.append({
                    "type": "technical",
                    "indicator": "MACD",
                    "action": "sell",
                    "strength": min(abs(histogram) * 10, 1.0),
                    "reason": "MACD bearish crossover with negative histogram",
                    "entry_price": current_price,
                    "confidence": 0.75
                })

        # Bollinger Bands signals
        bollinger_data = indicators.get("bollinger_bands", {})
        if isinstance(bollinger_data, dict) and "signal" in bollinger_data:
            bb_signal = bollinger_data["signal"]
            price_position = bollinger_data.get("price_position", 0.5)

            if bb_signal == "oversold":
                signals.append({
                    "type": "technical",
                    "indicator": "Bollinger_Bands",
                    "action": "buy",
                    "strength": 0.8,
                    "reason": "Price at lower Bollinger Band",
                    "entry_price": current_price,
                    "confidence": 0.6
                })
            elif bb_signal == "overbought":
                signals.append({
                    "type": "technical",
                    "indicator": "Bollinger_Bands",
                    "action": "sell",
                    "strength": 0.8,
                    "reason": "Price at upper Bollinger Band",
                    "entry_price": current_price,
                    "confidence": 0.6
                })

        # Moving Average signals
        sma_data = indicators.get("sma", {})
        if isinstance(sma_data, dict):
            sma_20 = sma_data.get("sma_20", {})
            if isinstance(sma_20, dict) and "signal" in sma_20:
                if sma_20["signal"] == "bullish":
                    signals.append({
                        "type": "technical",
                        "indicator": "SMA_20",
                        "action": "buy",
                        "strength": 0.6,
                        "reason": "Price above 20-day SMA",
                        "entry_price": current_price,
                        "confidence": 0.5
                    })
                elif sma_20["signal"] == "bearish":
                    signals.append({
                        "type": "technical",
                        "indicator": "SMA_20",
                        "action": "sell",
                        "strength": 0.6,
                        "reason": "Price below 20-day SMA",
                        "entry_price": current_price,
                        "confidence": 0.5
                    })

        return signals

    def _generate_sentiment_signals(self, symbol: str, news_sentiment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate signals based on news sentiment."""
        signals = []

        overall_sentiment = news_sentiment.get("overall_sentiment", 0.0)
        sentiment_strength = news_sentiment.get("sentiment_strength", 0.0)
        confidence = news_sentiment.get("confidence", 0.0)
        articles_count = news_sentiment.get("articles_analyzed", 0)

        # Only generate signals if we have sufficient data
        if articles_count >= 3 and sentiment_strength > 0.2:

            if overall_sentiment > 0.3:
                signals.append({
                    "type": "sentiment",
                    "indicator": "News_Sentiment",
                    "action": "buy",
                    "strength": min(sentiment_strength, 1.0),
                    "reason": f"Strong positive news sentiment ({overall_sentiment:.2f})",
                    "confidence": confidence * 0.8,  # Slightly discount sentiment confidence
                    "supporting_data": {
                        "sentiment_score": overall_sentiment,
                        "articles_analyzed": articles_count
                    }
                })
            elif overall_sentiment < -0.3:
                signals.append({
                    "type": "sentiment",
                    "indicator": "News_Sentiment",
                    "action": "sell",
                    "strength": min(sentiment_strength, 1.0),
                    "reason": f"Strong negative news sentiment ({overall_sentiment:.2f})",
                    "confidence": confidence * 0.8,
                    "supporting_data": {
                        "sentiment_score": overall_sentiment,
                        "articles_analyzed": articles_count
                    }
                })

        # Sentiment trend signals
        sentiment_trend = news_sentiment.get("sentiment_trend", {})
        if isinstance(sentiment_trend, dict):
            trend = sentiment_trend.get("trend", "stable")
            sentiment_change = sentiment_trend.get("sentiment_change", 0)

            if trend == "improving" and sentiment_change > 0.2:
                signals.append({
                    "type": "sentiment",
                    "indicator": "Sentiment_Trend",
                    "action": "buy",
                    "strength": min(sentiment_change, 1.0),
                    "reason": "Improving sentiment trend",
                    "confidence": 0.6
                })
            elif trend == "deteriorating" and sentiment_change < -0.2:
                signals.append({
                    "type": "sentiment",
                    "indicator": "Sentiment_Trend",
                    "action": "sell",
                    "strength": min(abs(sentiment_change), 1.0),
                    "reason": "Deteriorating sentiment trend",
                    "confidence": 0.6
                })

        return signals

    def _generate_momentum_signals(self, symbol: str, stock_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate momentum-based signals."""
        signals = []

        current_price = stock_data.get("current_price", 0)
        price_change_pct = stock_data.get("price_change_percent", 0)

        # Strong momentum signals
        if abs(price_change_pct) > 5:  # 5%+ move
            if price_change_pct > 5:
                signals.append({
                    "type": "momentum",
                    "indicator": "Price_Momentum",
                    "action": "buy",
                    "strength": min(price_change_pct / 10, 1.0),
                    "reason": f"Strong upward momentum ({price_change_pct:+.1f}%)",
                    "confidence": 0.6,
                    "entry_price": current_price
                })
            elif price_change_pct < -5:
                signals.append({
                    "type": "momentum",
                    "indicator": "Price_Momentum",
                    "action": "sell",
                    "strength": min(abs(price_change_pct) / 10, 1.0),
                    "reason": f"Strong downward momentum ({price_change_pct:+.1f}%)",
                    "confidence": 0.6,
                    "entry_price": current_price
                })

        # 52-week position momentum
        high_52w = stock_data.get("fifty_two_week_high")
        low_52w = stock_data.get("fifty_two_week_low")

        if high_52w and low_52w and current_price:
            position_in_range = (current_price - low_52w) / (high_52w - low_52w)

            if position_in_range > 0.95:  # Near 52-week high
                signals.append({
                    "type": "momentum",
                    "indicator": "52W_Position",
                    "action": "buy",
                    "strength": 0.7,
                    "reason": "Breaking out near 52-week high",
                    "confidence": 0.5,
                    "entry_price": current_price,
                    "note": "Momentum breakout signal"
                })
            elif position_in_range < 0.05:  # Near 52-week low
                signals.append({
                    "type": "momentum",
                    "indicator": "52W_Position",
                    "action": "buy",
                    "strength": 0.6,
                    "reason": "Potential reversal near 52-week low",
                    "confidence": 0.4,
                    "entry_price": current_price,
                    "note": "Contrarian reversal signal"
                })

        return signals

    def _generate_volume_signals(self, symbol: str, stock_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate volume-based signals."""
        signals = []

        volume = stock_data.get("volume", 0)
        avg_volume = stock_data.get("avg_volume", volume)
        price_change_pct = stock_data.get("price_change_percent", 0)
        current_price = stock_data.get("current_price", 0)

        if avg_volume > 0:
            volume_ratio = volume / avg_volume

            # High volume with price movement
            if volume_ratio > 2.0 and abs(price_change_pct) > 2:
                if price_change_pct > 0:
                    signals.append({
                        "type": "volume",
                        "indicator": "Volume_Breakout",
                        "action": "buy",
                        "strength": min(volume_ratio / 3, 1.0),
                        "reason": f"High volume ({volume_ratio:.1f}x avg) with price increase",
                        "confidence": 0.7,
                        "entry_price": current_price
                    })
                else:
                    signals.append({
                        "type": "volume",
                        "indicator": "Volume_Breakdown",
                        "action": "sell",
                        "strength": min(volume_ratio / 3, 1.0),
                        "reason": f"High volume ({volume_ratio:.1f}x avg) with price decline",
                        "confidence": 0.7,
                        "entry_price": current_price
                    })

            # Low volume warning
            elif volume_ratio < 0.3:
                signals.append({
                    "type": "volume",
                    "indicator": "Low_Volume",
                    "action": "hold",
                    "strength": 0.3,
                    "reason": f"Low volume ({volume_ratio:.1f}x avg) - wait for confirmation",
                    "confidence": 0.5,
                    "entry_price": current_price,
                    "note": "Lack of conviction in current move"
                })

        return signals

    def _generate_price_action_signals(self, symbol: str, stock_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate price action-based signals."""
        signals = []

        recent_prices = stock_data.get("recent_price_action", [])
        if len(recent_prices) < 3:
            return signals

        current_price = stock_data.get("current_price", 0)

        # Get last few days of price data
        last_3_days = recent_prices[-3:]

        # Gap analysis
        if len(last_3_days) >= 2:
            today_open = last_3_days[-1].get("open", 0)
            yesterday_close = last_3_days[-2].get("close", 0)

            if yesterday_close > 0:
                gap_pct = (today_open - yesterday_close) / yesterday_close * 100

                if abs(gap_pct) > 3:  # 3%+ gap
                    if gap_pct > 3:
                        signals.append({
                            "type": "price_action",
                            "indicator": "Gap_Up",
                            "action": "buy",
                            "strength": min(gap_pct / 5, 1.0),
                            "reason": f"Gap up {gap_pct:.1f}% - potential continuation",
                            "confidence": 0.6,
                            "entry_price": current_price
                        })
                    elif gap_pct < -3:
                        signals.append({
                            "type": "price_action",
                            "indicator": "Gap_Down",
                            "action": "sell",
                            "strength": min(abs(gap_pct) / 5, 1.0),
                            "reason": f"Gap down {gap_pct:.1f}% - potential continuation",
                            "confidence": 0.6,
                            "entry_price": current_price
                        })

        # Consecutive days pattern
        if len(last_3_days) >= 3:
            closes = [day.get("close", 0) for day in last_3_days]

            # Three consecutive up days
            if closes[2] > closes[1] > closes[0]:
                pct_change = (closes[2] - closes[0]) / closes[0] * 100 if closes[0] > 0 else 0
                if pct_change > 5:
                    signals.append({
                        "type": "price_action",
                        "indicator": "Three_Up_Days",
                        "action": "buy",
                        "strength": min(pct_change / 10, 1.0),
                        "reason": f"Three consecutive up days ({pct_change:.1f}% total)",
                        "confidence": 0.5,
                        "entry_price": current_price
                    })

            # Three consecutive down days
            elif closes[2] < closes[1] < closes[0]:
                pct_change = abs(closes[2] - closes[0]) / closes[0] * 100 if closes[0] > 0 else 0
                if pct_change > 5:
                    signals.append({
                        "type": "price_action",
                        "indicator": "Three_Down_Days",
                        "action": "buy",  # Contrarian signal
                        "strength": min(pct_change / 15, 1.0),
                        "reason": f"Three consecutive down days ({pct_change:.1f}% total) - potential reversal",
                        "confidence": 0.4,
                        "entry_price": current_price,
                        "note": "Contrarian reversal signal"
                    })

        return signals

    def _adjust_signals_for_risk(self, signals: List[Dict[str, Any]], risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Adjust signal strength and confidence based on risk assessment."""
        risk_level = risk_assessment.get("risk_level", "medium")
        risk_score = risk_assessment.get("risk_score", 3.0)

        # Risk adjustment factors
        risk_adjustments = {
            "low": 1.1,      # Boost signals for low-risk assets
            "medium": 1.0,   # No adjustment
            "high": 0.8,     # Reduce signals for high-risk assets
            "very_high": 0.6 # Significantly reduce signals for very high-risk assets
        }

        adjustment_factor = risk_adjustments.get(risk_level, 1.0)

        adjusted_signals = []
        for signal in signals:
            adjusted_signal = signal.copy()

            # Adjust strength and confidence
            adjusted_signal["strength"] *= adjustment_factor
            adjusted_signal["confidence"] *= adjustment_factor

            # Add risk context
            adjusted_signal["risk_adjustment"] = {
                "risk_level": risk_level,
                "adjustment_factor": adjustment_factor,
                "original_strength": signal["strength"],
                "original_confidence": signal["confidence"]
            }

            # Add risk warnings for high-risk assets
            if risk_level in ["high", "very_high"]:
                adjusted_signal["risk_warning"] = f"High risk asset ({risk_level}) - use appropriate position sizing"

            adjusted_signals.append(adjusted_signal)

        return adjusted_signals

    def _aggregate_and_rank_signals(self, signals: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
        """Aggregate and rank signals by strength and confidence."""
        if not signals:
            return []

        # Group signals by action
        buy_signals = [s for s in signals if s.get("action") == "buy"]
        sell_signals = [s for s in signals if s.get("action") == "sell"]
        hold_signals = [s for s in signals if s.get("action") == "hold"]

        aggregated_signals = []

        # Aggregate buy signals
        if buy_signals:
            buy_aggregate = self._create_aggregate_signal("buy", buy_signals, symbol)
            aggregated_signals.append(buy_aggregate)

        # Aggregate sell signals
        if sell_signals:
            sell_aggregate = self._create_aggregate_signal("sell", sell_signals, symbol)
            aggregated_signals.append(sell_aggregate)

        # Aggregate hold signals
        if hold_signals:
            hold_aggregate = self._create_aggregate_signal("hold", hold_signals, symbol)
            aggregated_signals.append(hold_aggregate)

        # Sort by composite score (strength * confidence)
        for signal in aggregated_signals:
            signal["composite_score"] = signal["strength"] * signal["confidence"]

        aggregated_signals.sort(key=lambda x: x["composite_score"], reverse=True)

        return aggregated_signals

    def _create_aggregate_signal(self, action: str, signals: List[Dict[str, Any]], symbol: str) -> Dict[str, Any]:
        """Create an aggregate signal from multiple individual signals."""

        # Calculate weighted averages
        total_weight = sum(s["confidence"] for s in signals)

        if total_weight == 0:
            avg_strength = sum(s["strength"] for s in signals) / len(signals)
            avg_confidence = sum(s["confidence"] for s in signals) / len(signals)
        else:
            avg_strength = sum(s["strength"] * s["confidence"] for s in signals) / total_weight
            avg_confidence = sum(s["confidence"] for s in signals) / len(signals)

        # Collect supporting indicators
        indicators = list(set(s.get("indicator", "Unknown") for s in signals))
        reasons = [s.get("reason", "") for s in signals]

        # Determine overall recommendation
        if action == "buy":
            if avg_strength > 0.7 and avg_confidence > 0.6:
                recommendation = "Strong Buy"
            elif avg_strength > 0.5 and avg_confidence > 0.5:
                recommendation = "Buy"
            else:
                recommendation = "Weak Buy"
        elif action == "sell":
            if avg_strength > 0.7 and avg_confidence > 0.6:
                recommendation = "Strong Sell"
            elif avg_strength > 0.5 and avg_confidence > 0.5:
                recommendation = "Sell"
            else:
                recommendation = "Weak Sell"
        else:  # hold
            recommendation = "Hold"

        return {
            "action": action,
            "recommendation": recommendation,
            "strength": min(avg_strength, 1.0),
            "confidence": min(avg_confidence, 1.0),
            "supporting_indicators": indicators,
            "signal_count": len(signals),
            "reasons": reasons,
            "summary": self._create_signal_summary(action, indicators, avg_strength, avg_confidence),
            "individual_signals": signals
        }

    def _create_signal_summary(self, action: str, indicators: List[str], strength: float, confidence: float) -> str:
        """Create a human-readable signal summary."""
        indicator_str = ", ".join(indicators[:3])  # Show top 3 indicators
        if len(indicators) > 3:
            indicator_str += f" and {len(indicators) - 3} others"

        strength_desc = "strong" if strength > 0.7 else "moderate" if strength > 0.4 else "weak"
        confidence_desc = "high" if confidence > 0.7 else "moderate" if confidence > 0.5 else "low"

        return f"{strength_desc.title()} {action} signal with {confidence_desc} confidence based on {indicator_str}"

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol for signal generation"
                },
                "stock_data": {
                    "type": "object",
                    "description": "Stock market data from Yahoo Finance tool"
                },
                "technical_analysis": {
                    "type": "object",
                    "description": "Technical analysis data (optional)"
                },
                "news_sentiment": {
                    "type": "object",
                    "description": "News sentiment analysis data (optional)"
                },
                "risk_assessment": {
                    "type": "object",
                    "description": "Risk assessment data (optional)"
                }
            },
            "required": ["symbol", "stock_data"]
        }

    async def health_check(self) -> bool:
        """Perform health check with sample data."""
        try:
            sample_stock_data = {
                "symbol": "TEST",
                "current_price": 100,
                "price_change_percent": 2.5,
                "volume": 1000000,
                "avg_volume": 800000,
                "recent_price_action": [
                    {"date": "2024-01-01", "open": 95, "close": 97},
                    {"date": "2024-01-02", "open": 97, "close": 99},
                    {"date": "2024-01-03", "open": 99, "close": 100}
                ]
            }

            result = await self.execute("TEST", sample_stock_data)
            return isinstance(result, list) and len(result) >= 0

        except Exception as e:
            logger.error(f"Trading signals health check failed: {e}")
            return False
