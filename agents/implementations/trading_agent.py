"""
Advanced Trading Agent implementation for comprehensive stock market analysis.

This agent provides:
- Real-time stock data analysis
- Technical indicator calculations
- News sentiment analysis
- Risk assessment and portfolio management
- Trading recommendations with risk management
"""

from typing import Dict, Any, List, Optional
import logging
import json
import asyncio
from datetime import datetime, timedelta
from framework.core.agent_base import BaseAgent

logger = logging.getLogger(__name__)


class TradingAgent(BaseAgent):
    """
    Advanced trading agent specialized in stock market analysis and trading decisions.

    Features:
    - Real-time stock data retrieval and analysis
    - Technical analysis with multiple indicators
    - News sentiment analysis for market context
    - Risk assessment and portfolio optimization
    - Trading signal generation with confidence levels
    - Historical pattern analysis and volatility assessment
    - Multi-timeframe analysis for comprehensive insights
    """

    def __init__(self, config_path: str):
        super().__init__(config_path)

        # Trading-specific configuration
        self.trading_specialties = self.config.get("trading_specialties", [])
        self.risk_tolerance = self.config.get("risk_tolerance", "moderate")
        self.analysis_timeframes = self.config.get("analysis_timeframes", ["1d", "5d", "1mo"])
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)

        # Initialize trading context
        self._current_portfolio = {}
        self._watchlist = []
        self._analysis_cache = {}

        # Tool execution tracking for transparency
        self._tool_executions = []

        logger.info(f"Initialized trading agent: {self.name} with risk tolerance: {self.risk_tolerance}")

    async def use_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Override use_tool to capture detailed execution results for transparency."""
        import time
        start_time = time.time()

        try:
            # Call the parent method
            result = await super().use_tool(tool_name, parameters)
            execution_time = time.time() - start_time

            # Capture detailed execution info
            tool_execution = {
                "tool_name": tool_name,
                "parameters": parameters,
                "success": result.success if hasattr(result, 'success') else True,
                "execution_time": execution_time,
                "result_summary": self._generate_result_summary(tool_name, result),
                "timestamp": time.time()
            }

            # Include result data if available and not too large
            if hasattr(result, 'data') and result.data:
                try:
                    # Try to format as JSON for better readability
                    import json
                    if isinstance(result.data, (dict, list)):
                        result_str = json.dumps(result.data, indent=2, default=str)
                    else:
                        result_str = str(result.data)
                except Exception:
                    result_str = str(result.data)

                if len(result_str) > 2000:
                    # For large results, create a properly formatted preview
                    try:
                        if isinstance(result.data, (dict, list)):
                            preview_data = json.dumps(result.data, indent=2, default=str)[:1000]
                            # Try to end at a complete line
                            last_newline = preview_data.rfind('\n')
                            if last_newline > 500:  # Only if we have a reasonable amount of content
                                preview_data = preview_data[:last_newline]
                            tool_execution["result_preview"] = preview_data + "\n... (truncated)"
                        else:
                            tool_execution["result_preview"] = str(result.data)[:1000] + "... (truncated)"
                    except Exception:
                        tool_execution["result_preview"] = str(result.data)[:1000] + "... (truncated)"

                    tool_execution["result_size"] = len(result_str)
                    # Also include full data for expansion capability
                    tool_execution["result_data_full"] = result.data
                else:
                    tool_execution["result_data"] = result.data

            # Include error info if tool failed
            if hasattr(result, 'success') and not result.success:
                if hasattr(result, 'error'):
                    tool_execution["error"] = str(result.error)
                else:
                    tool_execution["error"] = "Tool execution failed"

            self._tool_executions.append(tool_execution)
            return result

        except Exception as e:
            execution_time = time.time() - start_time

            # Capture error execution info
            tool_execution = {
                "tool_name": tool_name,
                "parameters": parameters,
                "success": False,
                "execution_time": execution_time,
                "result_summary": f"Tool execution failed: {str(e)}",
                "error": str(e),
                "timestamp": time.time()
            }

            self._tool_executions.append(tool_execution)
            raise

    def _generate_result_summary(self, tool_name: str, result: Any) -> str:
        """Generate a human-readable summary of tool execution results."""
        try:
            if not hasattr(result, 'data') or not result.data:
                return "No data returned"

            data = result.data

            if tool_name == "yahoo_finance_api":
                if isinstance(data, dict):
                    symbol = data.get('symbol', 'Unknown')
                    price = data.get('current_price', 'N/A')
                    return f"Retrieved stock data for {symbol} at ${price}"
                return "Stock data retrieved"

            elif tool_name == "technical_indicators":
                if isinstance(data, dict):
                    indicators = list(data.keys())
                    return f"Calculated {len(indicators)} technical indicators: {', '.join(indicators[:3])}"
                return "Technical indicators calculated"

            elif tool_name == "news_sentiment_analyzer":
                if isinstance(data, dict):
                    sentiment = data.get('overall_sentiment', 'N/A')
                    articles = data.get('articles_count', 0)
                    return f"Analyzed {articles} articles, sentiment: {sentiment}"
                return "News sentiment analyzed"

            elif tool_name == "risk_analyzer":
                if isinstance(data, dict):
                    risk_level = data.get('risk_level', 'N/A')
                    volatility = data.get('volatility', 'N/A')
                    return f"Risk level: {risk_level}, volatility: {volatility}"
                return "Risk analysis completed"

            elif tool_name == "symbol_extractor":
                if isinstance(data, list):
                    return f"Extracted {len(data)} symbols: {', '.join(data[:3])}"
                return "Symbols extracted"

            else:
                return f"Tool executed successfully"

        except Exception as e:
            return f"Result summary generation failed: {str(e)}"

    async def generate_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive trading analysis response.

        Args:
            message: User's trading query or stock symbol
            context: Additional context including collaboration info

        Returns:
            Trading analysis with recommendations and risk assessment
        """
        try:
            # Check if this is a collaboration request
            if context.get("collaboration_from"):
                return await self._handle_collaboration(message, context)

            # Check if this is a health check
            if context.get("internal_health_check"):
                return {"response": "Trading agent is ready to analyze markets!", "success": True}

            # Parse and analyze the trading query
            query_analysis = await self._analyze_trading_query(message)

            # Generate comprehensive trading analysis
            trading_analysis = await self._generate_trading_analysis(message, query_analysis)

            # Format comprehensive response
            response = {
                "response": trading_analysis["summary"],
                "stock_data": trading_analysis.get("stock_data"),
                "technical_analysis": trading_analysis.get("technical_analysis"),
                "news_sentiment": trading_analysis.get("news_sentiment"),
                "risk_assessment": trading_analysis.get("risk_assessment"),
                "trading_signals": trading_analysis.get("trading_signals", []),
                "recommendations": trading_analysis.get("recommendations", []),
                "confidence_level": trading_analysis.get("confidence_level", 0.0),
                "analysis_timestamp": datetime.now().isoformat(),
                "symbols_analyzed": query_analysis.get("symbols", []),
                "success": True
            }

            # Track tools used for transparency
            tools_used = []
            tool_executions = []

            if trading_analysis.get("stock_data"):
                tools_used.append("yahoo_finance_api")
            if trading_analysis.get("technical_analysis"):
                tools_used.append("technical_indicators")
            if trading_analysis.get("news_sentiment"):
                tools_used.append("news_sentiment_analyzer")
            if trading_analysis.get("risk_assessment"):
                tools_used.append("risk_analyzer")

            # Include detailed tool executions if available
            if hasattr(self, '_tool_executions'):
                tool_executions = self._tool_executions
                # Clear for next request
                self._tool_executions = []

            response["tools_used"] = tools_used
            response["tool_executions"] = tool_executions
            response["analysis_depth"] = "comprehensive"

            return response

        except Exception as e:
            logger.error(f"Error generating trading response: {e}", exc_info=True)
            return {
                "response": "I apologize, but I'm experiencing technical difficulties accessing market data. Please ensure the stock symbol is valid and try again.",
                "error": str(e),
                "success": False,
                "fallback_advice": "Consider consulting multiple sources and performing your own due diligence before making any trading decisions."
            }

    async def _analyze_trading_query(self, message: str) -> Dict[str, Any]:
        """
        Analyze trading query to understand what analysis is needed.

        Args:
            message: User's trading query

        Returns:
            Analysis of the trading query with extracted symbols and intent
        """
        analysis = {
            "query_type": self._determine_query_type(message),
            "symbols": [],
            "timeframe": self._extract_timeframe(message),
            "analysis_type": self._determine_analysis_type(message),
            "risk_level": self._extract_risk_preference(message),
            "specific_indicators": []
        }

        try:
            # Extract stock symbols using symbol extractor tool
            if "symbol_extractor" in self.tool_registry.list_tools():
                symbol_result = await self.use_tool("symbol_extractor", {"text": message})
                if symbol_result.success:
                    analysis["symbols"] = symbol_result.data
                    logger.debug(f"Extracted symbols: {analysis['symbols']}")

            # If no symbols found, try to extract from common patterns
            if not analysis["symbols"]:
                analysis["symbols"] = self._extract_symbols_fallback(message)

            # Identify specific technical indicators requested
            indicator_keywords = {
                "rsi": ["rsi", "relative strength", "overbought", "oversold"],
                "macd": ["macd", "moving average convergence", "divergence"],
                "bollinger": ["bollinger", "bands", "squeeze"],
                "sma": ["sma", "simple moving average", "moving average"],
                "ema": ["ema", "exponential moving average"],
                "volume": ["volume", "trading volume", "volume analysis"],
                "support_resistance": ["support", "resistance", "levels"],
                "fibonacci": ["fibonacci", "fib", "retracement"]
            }

            message_lower = message.lower()
            for indicator, keywords in indicator_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    analysis["specific_indicators"].append(indicator)

            # Determine if this is a buy/sell/hold query
            if any(word in message_lower for word in ["buy", "purchase", "invest"]):
                analysis["action_intent"] = "buy"
            elif any(word in message_lower for word in ["sell", "exit", "close"]):
                analysis["action_intent"] = "sell"
            elif any(word in message_lower for word in ["hold", "keep", "maintain"]):
                analysis["action_intent"] = "hold"
            else:
                analysis["action_intent"] = "analyze"

        except Exception as e:
            logger.error(f"Error analyzing trading query: {e}")
            analysis["analysis_error"] = str(e)

        return analysis

    async def _generate_trading_analysis(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive trading analysis based on query analysis.

        Args:
            message: Original trading query
            analysis: Query analysis results

        Returns:
            Comprehensive trading analysis with all components
        """
        trading_analysis = {
            "summary": "",
            "stock_data": {},
            "technical_analysis": {},
            "news_sentiment": {},
            "risk_assessment": {},
            "trading_signals": [],
            "recommendations": [],
            "confidence_level": 0.0
        }

        symbols = analysis.get("symbols", [])
        if not symbols:
            trading_analysis["summary"] = "Please provide a valid stock symbol (e.g., AAPL, TSLA, MSFT) for analysis."
            return trading_analysis

        try:
            # Analyze each symbol
            all_analyses = []

            for symbol in symbols[:3]:  # Limit to 3 symbols for performance
                symbol_analysis = await self._analyze_single_stock(symbol, analysis)
                if symbol_analysis:
                    all_analyses.append(symbol_analysis)

            if not all_analyses:
                trading_analysis["summary"] = "Unable to retrieve data for the requested symbols. Please check if they are valid stock tickers."
                return trading_analysis

            # Aggregate results for multiple symbols or use single symbol data
            if len(all_analyses) == 1:
                trading_analysis = all_analyses[0]
            else:
                trading_analysis = await self._aggregate_multi_symbol_analysis(all_analyses, symbols)

            # Generate comprehensive summary
            trading_analysis["summary"] = await self._build_trading_summary(
                message, analysis, trading_analysis
            )

        except Exception as e:
            logger.error(f"Error generating trading analysis: {e}")
            trading_analysis["summary"] = f"Analysis error: {str(e)}"

        return trading_analysis

    async def _analyze_single_stock(self, symbol: str, query_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Perform comprehensive analysis of a single stock.

        Args:
            symbol: Stock symbol to analyze
            query_analysis: Original query analysis

        Returns:
            Complete analysis for the stock or None if failed
        """
        analysis = {
            "symbol": symbol,
            "stock_data": {},
            "technical_analysis": {},
            "news_sentiment": {},
            "risk_assessment": {},
            "trading_signals": [],
            "recommendations": [],
            "confidence_level": 0.0
        }

        try:
            # 1. Get stock data
            if "yahoo_finance_api" in self.tool_registry.list_tools():
                stock_params = {
                    "symbol": symbol,
                    "period": query_analysis.get("timeframe", "1mo"),
                    "include_fundamentals": True
                }

                stock_result = await self.use_tool("yahoo_finance_api", stock_params)
                if stock_result.success:
                    analysis["stock_data"] = stock_result.data
                    logger.debug(f"Retrieved stock data for {symbol}")

            # 2. Perform technical analysis
            if analysis["stock_data"] and "technical_indicators" in self.tool_registry.list_tools():
                tech_params = {
                    "stock_data": analysis["stock_data"],
                    "indicators": query_analysis.get("specific_indicators", ["rsi", "macd", "sma", "volume"]),
                    "timeframe": query_analysis.get("timeframe", "1mo")
                }

                tech_result = await self.use_tool("technical_indicators", tech_params)
                if tech_result.success:
                    analysis["technical_analysis"] = tech_result.data
                    logger.debug(f"Completed technical analysis for {symbol}")

            # 3. Get news sentiment
            if "news_sentiment_analyzer" in self.tool_registry.list_tools():
                news_params = {
                    "symbol": symbol,
                    "days_back": 7,
                    "include_market_news": True
                }

                news_result = await self.use_tool("news_sentiment_analyzer", news_params)
                if news_result.success:
                    analysis["news_sentiment"] = news_result.data
                    logger.debug(f"Analyzed news sentiment for {symbol}")

            # 4. Assess risk
            if "risk_analyzer" in self.tool_registry.list_tools():
                risk_params = {
                    "symbol": symbol,
                    "stock_data": analysis["stock_data"],
                    "technical_data": analysis["technical_analysis"],
                    "risk_tolerance": self.risk_tolerance
                }

                risk_result = await self.use_tool("risk_analyzer", risk_params)
                if risk_result.success:
                    analysis["risk_assessment"] = risk_result.data
                    logger.debug(f"Completed risk assessment for {symbol}")

            # 5. Generate trading signals
            if "trading_signal_generator" in self.tool_registry.list_tools():
                signal_params = {
                    "symbol": symbol,
                    "stock_data": analysis["stock_data"],
                    "technical_analysis": analysis["technical_analysis"],
                    "news_sentiment": analysis["news_sentiment"],
                    "risk_assessment": analysis["risk_assessment"]
                }

                signal_result = await self.use_tool("trading_signal_generator", signal_params)
                if signal_result.success:
                    analysis["trading_signals"] = signal_result.data
                    logger.debug(f"Generated trading signals for {symbol}")

            # 6. Calculate overall confidence level
            analysis["confidence_level"] = self._calculate_confidence_level(analysis)

            # 7. Generate recommendations
            analysis["recommendations"] = self._generate_recommendations(analysis, query_analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing stock {symbol}: {e}")
            return None

    async def _aggregate_multi_symbol_analysis(self, analyses: List[Dict[str, Any]], symbols: List[str]) -> Dict[str, Any]:
        """
        Aggregate analysis results for multiple symbols.

        Args:
            analyses: List of individual stock analyses
            symbols: List of symbols analyzed

        Returns:
            Aggregated analysis
        """
        aggregated = {
            "symbols": symbols,
            "stock_data": {},
            "technical_analysis": {},
            "news_sentiment": {},
            "risk_assessment": {},
            "trading_signals": [],
            "recommendations": [],
            "confidence_level": 0.0,
            "portfolio_analysis": {}
        }

        try:
            # Aggregate data by symbol
            for analysis in analyses:
                symbol = analysis["symbol"]
                aggregated["stock_data"][symbol] = analysis["stock_data"]
                aggregated["technical_analysis"][symbol] = analysis["technical_analysis"]
                aggregated["news_sentiment"][symbol] = analysis["news_sentiment"]
                aggregated["risk_assessment"][symbol] = analysis["risk_assessment"]

                # Collect all trading signals
                for signal in analysis["trading_signals"]:
                    signal["symbol"] = symbol
                    aggregated["trading_signals"].append(signal)

            # Calculate portfolio-level metrics if portfolio analyzer is available
            if "portfolio_analyzer" in self.tool_registry.list_tools():
                portfolio_params = {
                    "symbols": symbols,
                    "analyses": analyses,
                    "correlation_analysis": True,
                    "diversification_score": True
                }

                portfolio_result = await self.use_tool("portfolio_analyzer", portfolio_params)
                if portfolio_result.success:
                    aggregated["portfolio_analysis"] = portfolio_result.data

            # Calculate average confidence level
            confidence_levels = [a["confidence_level"] for a in analyses if a["confidence_level"] > 0]
            aggregated["confidence_level"] = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0.0

            # Generate portfolio recommendations
            aggregated["recommendations"] = self._generate_portfolio_recommendations(analyses)

        except Exception as e:
            logger.error(f"Error aggregating multi-symbol analysis: {e}")

        return aggregated

    def _calculate_confidence_level(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate confidence level based on data quality and signal strength.

        Args:
            analysis: Stock analysis data

        Returns:
            Confidence level between 0.0 and 1.0
        """
        confidence_factors = []

        try:
            # Data availability factor
            if analysis.get("stock_data"):
                confidence_factors.append(0.3)

            if analysis.get("technical_analysis"):
                confidence_factors.append(0.25)

            if analysis.get("news_sentiment"):
                confidence_factors.append(0.2)

            if analysis.get("risk_assessment"):
                confidence_factors.append(0.25)

            # Signal strength factor
            signals = analysis.get("trading_signals", [])
            if signals:
                signal_strengths = [s.get("strength", 0.5) for s in signals]
                avg_signal_strength = sum(signal_strengths) / len(signal_strengths)
                confidence_factors.append(avg_signal_strength * 0.3)

            # Volume and liquidity factor
            stock_data = analysis.get("stock_data", {})
            if stock_data.get("volume") and stock_data.get("avg_volume"):
                volume_ratio = stock_data["volume"] / stock_data["avg_volume"]
                volume_confidence = min(volume_ratio / 2.0, 1.0) * 0.2
                confidence_factors.append(volume_confidence)

            return min(sum(confidence_factors), 1.0)

        except Exception as e:
            logger.error(f"Error calculating confidence level: {e}")
            return 0.5

    def _generate_recommendations(self, analysis: Dict[str, Any], query_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate trading recommendations based on analysis.

        Args:
            analysis: Stock analysis data
            query_analysis: Original query analysis

        Returns:
            List of trading recommendations
        """
        recommendations = []

        try:
            symbol = analysis["symbol"]
            confidence = analysis["confidence_level"]

            # Risk-based recommendations
            risk_data = analysis.get("risk_assessment", {})
            risk_level = risk_data.get("risk_level", "medium")

            # Technical analysis recommendations
            tech_data = analysis.get("technical_analysis", {})

            # News sentiment recommendations
            news_data = analysis.get("news_sentiment", {})
            sentiment_score = news_data.get("overall_sentiment", 0.0)

            # Generate primary recommendation
            signals = analysis.get("trading_signals", [])
            if signals:
                primary_signal = max(signals, key=lambda x: x.get("strength", 0))

                recommendation = {
                    "type": primary_signal.get("action", "hold"),
                    "confidence": confidence,
                    "reasoning": self._build_recommendation_reasoning(analysis),
                    "risk_level": risk_level,
                    "timeframe": query_analysis.get("timeframe", "short-term"),
                    "entry_price": analysis.get("stock_data", {}).get("current_price"),
                    "stop_loss": self._calculate_stop_loss(analysis),
                    "target_price": self._calculate_target_price(analysis)
                }

                recommendations.append(recommendation)

            # Add risk management recommendations
            if risk_level in ["high", "very_high"]:
                recommendations.append({
                    "type": "risk_warning",
                    "message": f"High risk detected for {symbol}. Consider position sizing and stop losses.",
                    "suggested_position_size": "small",
                    "risk_factors": risk_data.get("risk_factors", [])
                })

            # Add market context recommendations
            if sentiment_score < -0.3:
                recommendations.append({
                    "type": "market_context",
                    "message": "Negative news sentiment detected. Monitor for potential volatility.",
                    "context": "bearish_sentiment"
                })
            elif sentiment_score > 0.3:
                recommendations.append({
                    "type": "market_context",
                    "message": "Positive news sentiment detected. Potential momentum opportunity.",
                    "context": "bullish_sentiment"
                })

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append({
                "type": "error",
                "message": "Unable to generate specific recommendations. Please perform additional analysis."
            })

        return recommendations

    def _generate_portfolio_recommendations(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate portfolio-level recommendations for multiple stocks.

        Args:
            analyses: List of individual stock analyses

        Returns:
            List of portfolio recommendations
        """
        recommendations = []

        try:
            symbols = [a["symbol"] for a in analyses]

            # Diversification recommendation
            if len(symbols) > 1:
                recommendations.append({
                    "type": "diversification",
                    "message": f"Analyzing {len(symbols)} symbols provides better diversification than single stock analysis.",
                    "symbols": symbols
                })

            # Risk distribution
            risk_levels = [a.get("risk_assessment", {}).get("risk_level", "medium") for a in analyses]
            high_risk_count = risk_levels.count("high") + risk_levels.count("very_high")

            if high_risk_count > len(symbols) / 2:
                recommendations.append({
                    "type": "portfolio_risk",
                    "message": "Portfolio contains high proportion of risky assets. Consider rebalancing.",
                    "high_risk_symbols": [a["symbol"] for a in analyses
                                        if a.get("risk_assessment", {}).get("risk_level") in ["high", "very_high"]]
                })

            # Correlation warning
            recommendations.append({
                "type": "correlation_note",
                "message": "Consider correlation between selected stocks to avoid concentration risk.",
                "suggestion": "Use portfolio analysis tools for detailed correlation metrics."
            })

        except Exception as e:
            logger.error(f"Error generating portfolio recommendations: {e}")

        return recommendations

    async def _build_trading_summary(
        self,
        message: str,
        analysis: Dict[str, Any],
        trading_data: Dict[str, Any]
    ) -> str:
        """
        Build comprehensive trading summary text.

        Args:
            message: Original query
            analysis: Query analysis
            trading_data: Trading analysis data

        Returns:
            Formatted trading summary text
        """
        # Build trading prompt for LLM
        trading_prompt = self._build_trading_prompt(message, analysis, trading_data)

        # Generate response using context engine
        summary_text = await self._generate_contextual_trading_response(trading_prompt)

        return summary_text

    def _build_trading_prompt(
        self,
        message: str,
        analysis: Dict[str, Any],
        trading_data: Dict[str, Any]
    ) -> str:
        """
        Build context-aware trading prompt for LLM.

        Args:
            message: User query
            analysis: Query analysis
            trading_data: Trading data

        Returns:
            Formatted trading prompt
        """
        symbols = analysis.get("symbols", [])
        symbols_str = ", ".join(symbols) if symbols else "N/A"

        template = """
        {system_context}

        User trading query: "{message}"

        Analysis Details:
        - Symbols: {symbols}
        - Query type: {query_type}
        - Timeframe: {timeframe}
        - Analysis type: {analysis_type}
        - Risk tolerance: {risk_tolerance}

        Market Data Summary:
        {stock_data_summary}

        Technical Analysis:
        {technical_summary}

        News Sentiment:
        {news_summary}

        Risk Assessment:
        {risk_summary}

        Trading Signals:
        {signals_summary}

        Confidence Level: {confidence_level}

        {memory_context}

        Please provide a comprehensive trading analysis using this EXACT format structure:

        ## 📊 Market Overview
        [Brief 2-3 sentence summary of the current market position]

        ## 📈 Technical Analysis
        **Key Indicators:**
        • [Indicator 1]: [Value and interpretation]
        • [Indicator 2]: [Value and interpretation]
        • [Indicator 3]: [Value and interpretation]

        **Support & Resistance:**
        • Support: $[price level]
        • Resistance: $[price level]

        ## 📰 News Impact
        **Sentiment Score:** [score]/10
        **Key Factors:**
        • [Factor 1]
        • [Factor 2]

        ## ⚠️ Risk Assessment
        **Risk Level:** [Low/Medium/High]
        **Volatility:** [percentage]
        **Key Risk Factors:**
        • [Risk 1]
        • [Risk 2]

        ## 🎯 Trading Recommendations
        **Primary Signal:** [BUY/SELL/HOLD]
        **Entry Price:** $[price]
        **Target Price:** $[price]
        **Stop Loss:** $[price]
        **Position Size:** [Small/Medium/Large]

        **Reasoning:**
        [2-3 sentences explaining the recommendation]

        ## ⏰ Timeframe Considerations
        • **Short-term (1-7 days):** [outlook]
        • **Medium-term (1-4 weeks):** [outlook]
        • **Long-term (1-3 months):** [outlook]

        ## 🚨 Important Disclaimer
        This analysis is for educational purposes only. Always conduct your own research and consult with financial advisors before making investment decisions. Past performance does not guarantee future results.

        ---
        *Analysis confidence: {confidence_level} | Generated at: [current time]*

        Response:
        """

        return self.context_engine.build_prompt(
            template,
            message=message,
            symbols=symbols_str,
            query_type=analysis.get("query_type", "general"),
            timeframe=analysis.get("timeframe", "1mo"),
            analysis_type=analysis.get("analysis_type", "comprehensive"),
            risk_tolerance=self.risk_tolerance,
            stock_data_summary=self._format_stock_data_summary(trading_data.get("stock_data", {})),
            technical_summary=self._format_technical_summary(trading_data.get("technical_analysis", {})),
            news_summary=self._format_news_summary(trading_data.get("news_sentiment", {})),
            risk_summary=self._format_risk_summary(trading_data.get("risk_assessment", {})),
            signals_summary=self._format_signals_summary(trading_data.get("trading_signals", [])),
            confidence_level=f"{trading_data.get('confidence_level', 0.0):.1%}",
            personality=self._build_personality_context()
        )

    async def _generate_contextual_trading_response(self, prompt: str) -> str:
        """
        Generate response using LLM with trading context.
        """
        try:
            # Build system message for the trading agent
            system_message = self._build_trading_system_message()

            # Generate response using the LLM client
            response = await self.generate_llm_response(
                prompt=prompt,
                system_message=system_message,
                max_tokens=self.config.get("max_response_tokens", 1200),
                temperature=self.config.get("response_temperature", 0.2),  # Lower temp for factual financial info
                provider=self.config.get("llm_config", {}).get("preferred_provider")
            )

            return response

        except Exception as e:
            logger.error(f"Error generating LLM trading response: {e}")
            return self._get_trading_fallback_response()

    def _build_trading_system_message(self) -> str:
        """
        Build comprehensive system message for the trading agent LLM.
        """
        personality_desc = self._build_personality_context()
        specialties_desc = ", ".join(self.trading_specialties) if self.trading_specialties else "general market analysis"

        system_message = f"""You are an expert financial analyst and trading advisor with the following characteristics:

PERSONALITY: {personality_desc}

TRADING EXPERTISE:
- Specialties: {specialties_desc}
- Risk tolerance approach: {self.risk_tolerance}
- Analysis timeframes: {', '.join(self.analysis_timeframes)}
- Focus on data-driven, objective analysis
- Emphasize risk management and proper position sizing

ANALYSIS GUIDELINES:
1. Always prioritize risk management in all recommendations
2. Provide specific, actionable insights based on data
3. Include both technical and fundamental perspectives
4. Consider market context and news sentiment
5. Explain the reasoning behind recommendations
6. Use clear, professional language appropriate for traders
7. Include appropriate risk disclaimers

RESPONSE STRUCTURE:
CRITICAL: You MUST follow the exact markdown format provided in the prompt, including:
- Use the exact section headers with emojis (## 📊 Market Overview, ## 📈 Technical Analysis, etc.)
- Use bullet points (•) for lists as shown
- Include all sections in the specified order
- Use **bold** formatting for labels
- Keep sections concise but informative
- Always include specific price levels, percentages, and concrete data
- End with the disclaimer and confidence footer as shown

RISK MANAGEMENT FOCUS:
- Always mention appropriate position sizing
- Include stop-loss recommendations
- Highlight potential risks and drawdowns
- Consider correlation with broader market
- Emphasize the importance of diversification

DISCLAIMERS:
- Always include that analysis is for educational purposes
- Recommend users conduct their own research
- Suggest consulting with qualified financial advisors
- Mention that past performance doesn't guarantee future results
- Highlight that all investments carry risk of loss

Your goal is to provide comprehensive, data-driven trading analysis while maintaining the highest standards of risk management and professional responsibility."""

        return system_message

    def _get_trading_fallback_response(self) -> str:
        """
        Get fallback response when LLM is not available.
        """
        return """Thank you for your trading inquiry. I'm currently experiencing technical difficulties with my analysis engine.

For reliable trading analysis, I recommend:

📊 **Technical Analysis:**
- Check key support and resistance levels
- Monitor RSI for overbought/oversold conditions
- Analyze volume patterns for confirmation

📰 **Fundamental Research:**
- Review recent earnings reports and guidance
- Monitor industry news and market sentiment
- Check economic indicators affecting the sector

⚠️ **Risk Management:**
- Never risk more than you can afford to lose
- Use appropriate position sizing (typically 1-2% of portfolio per trade)
- Always set stop-loss orders to limit downside risk
- Diversify across different sectors and asset classes

**Important Disclaimer:** This information is for educational purposes only. Please conduct your own research and consult with a qualified financial advisor before making any investment decisions. All investments carry risk of loss.

Please try your analysis request again in a moment for detailed technical and fundamental insights."""

    # Helper methods for formatting summaries
    def _format_stock_data_summary(self, stock_data: Dict[str, Any]) -> str:
        """Format stock data for prompt."""
        if not stock_data:
            return "No stock data available"

        if isinstance(stock_data, dict) and len(stock_data) == 1:
            # Single stock
            symbol, data = next(iter(stock_data.items()))
            return f"Current Price: ${data.get('current_price', 'N/A')}, Volume: {data.get('volume', 'N/A')}, 52W Range: ${data.get('fifty_two_week_low', 'N/A')} - ${data.get('fifty_two_week_high', 'N/A')}"
        else:
            # Multiple stocks or direct data
            return f"Market data retrieved for analysis (detailed data available in tools)"

    def _format_technical_summary(self, technical_data: Dict[str, Any]) -> str:
        """Format technical analysis for prompt."""
        if not technical_data:
            return "No technical analysis available"

        summary_parts = []
        if isinstance(technical_data, dict):
            for indicator, value in technical_data.items():
                if isinstance(value, (int, float)):
                    summary_parts.append(f"{indicator.upper()}: {value:.2f}")
                elif isinstance(value, dict) and 'signal' in value:
                    summary_parts.append(f"{indicator.upper()}: {value['signal']}")

        return "; ".join(summary_parts) if summary_parts else "Technical indicators calculated"

    def _format_news_summary(self, news_data: Dict[str, Any]) -> str:
        """Format news sentiment for prompt."""
        if not news_data:
            return "No news sentiment data available"

        sentiment = news_data.get('overall_sentiment', 0.0)
        if sentiment > 0.1:
            return f"Positive sentiment ({sentiment:.2f}) - Bullish news coverage"
        elif sentiment < -0.1:
            return f"Negative sentiment ({sentiment:.2f}) - Bearish news coverage"
        else:
            return f"Neutral sentiment ({sentiment:.2f}) - Mixed news coverage"

    def _format_risk_summary(self, risk_data: Dict[str, Any]) -> str:
        """Format risk assessment for prompt."""
        if not risk_data:
            return "No risk assessment available"

        risk_level = risk_data.get('risk_level', 'medium')
        volatility = risk_data.get('volatility', 'N/A')
        return f"Risk Level: {risk_level.title()}, Volatility: {volatility}"

    def _format_signals_summary(self, signals: List[Dict[str, Any]]) -> str:
        """Format trading signals for prompt."""
        if not signals:
            return "No trading signals generated"

        signal_summaries = []
        for signal in signals[:3]:  # Limit to top 3 signals
            action = signal.get('action', 'hold')
            strength = signal.get('strength', 0.5)
            signal_summaries.append(f"{action.upper()} (strength: {strength:.2f})")

        return "; ".join(signal_summaries)

    # Additional helper methods
    def _determine_query_type(self, message: str) -> str:
        """Determine the type of trading query."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["analysis", "analyze", "research"]):
            return "analysis"
        elif any(word in message_lower for word in ["buy", "purchase", "invest"]):
            return "buy_signal"
        elif any(word in message_lower for word in ["sell", "exit", "close"]):
            return "sell_signal"
        elif any(word in message_lower for word in ["portfolio", "diversification", "allocation"]):
            return "portfolio"
        else:
            return "general"

    def _extract_timeframe(self, message: str) -> str:
        """Extract timeframe from trading query."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["intraday", "day trading", "scalping"]):
            return "1d"
        elif any(word in message_lower for word in ["week", "weekly", "short term"]):
            return "5d"
        elif any(word in message_lower for word in ["month", "monthly", "medium term"]):
            return "1mo"
        elif any(word in message_lower for word in ["quarter", "quarterly", "3 month"]):
            return "3mo"
        elif any(word in message_lower for word in ["year", "yearly", "long term"]):
            return "1y"
        else:
            return "1mo"  # Default to 1 month

    def _determine_analysis_type(self, message: str) -> str:
        """Determine what type of analysis is requested."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["technical", "chart", "indicator"]):
            return "technical"
        elif any(word in message_lower for word in ["fundamental", "earnings", "valuation"]):
            return "fundamental"
        elif any(word in message_lower for word in ["news", "sentiment", "events"]):
            return "news"
        elif any(word in message_lower for word in ["risk", "volatility", "drawdown"]):
            return "risk"
        else:
            return "comprehensive"

    def _extract_risk_preference(self, message: str) -> str:
        """Extract risk preference from message."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["conservative", "low risk", "safe"]):
            return "conservative"
        elif any(word in message_lower for word in ["aggressive", "high risk", "speculative"]):
            return "aggressive"
        else:
            return self.risk_tolerance

    def _extract_symbols_fallback(self, message: str) -> List[str]:
        """Fallback method to extract stock symbols from message."""
        import re

        # Look for patterns like AAPL, TSLA, etc. (2-5 uppercase letters)
        pattern = r'\b[A-Z]{2,5}\b'
        potential_symbols = re.findall(pattern, message.upper())

        # Filter out common words that might match the pattern
        common_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BY', 'WORD', 'BUT', 'WHAT', 'SOME', 'WE', 'CAN', 'OUT', 'OTHER', 'WERE', 'WHICH', 'THEIR', 'TIME', 'WILL', 'HOW', 'SAID', 'EACH', 'SHE', 'MAY', 'USE', 'HER', 'THAN', 'NOW', 'WAY', 'WHO', 'ITS', 'DID', 'GET', 'HAS', 'HIM', 'OLD', 'SEE', 'TWO', 'HOW', 'ITS', 'OUR', 'OUT', 'DAY', 'HAD', 'HIS', 'HER', 'HOW', 'MAN', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE'}

        symbols = [s for s in potential_symbols if s not in common_words]
        return symbols[:5]  # Limit to 5 symbols

    def _calculate_stop_loss(self, analysis: Dict[str, Any]) -> Optional[float]:
        """Calculate suggested stop loss price."""
        try:
            stock_data = analysis.get("stock_data", {})
            current_price = stock_data.get("current_price")

            if not current_price:
                return None

            # Use ATR-based stop loss if available
            technical_data = analysis.get("technical_analysis", {})
            atr = technical_data.get("atr")

            if atr:
                return current_price - (2 * atr)  # 2 ATR stop loss
            else:
                # Fallback to percentage-based stop loss
                risk_data = analysis.get("risk_assessment", {})
                risk_level = risk_data.get("risk_level", "medium")

                stop_loss_pct = {
                    "low": 0.05,      # 5%
                    "medium": 0.08,   # 8%
                    "high": 0.12,     # 12%
                    "very_high": 0.15 # 15%
                }.get(risk_level, 0.08)

                return current_price * (1 - stop_loss_pct)

        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            return None

    def _calculate_target_price(self, analysis: Dict[str, Any]) -> Optional[float]:
        """Calculate suggested target price."""
        try:
            stock_data = analysis.get("stock_data", {})
            current_price = stock_data.get("current_price")

            if not current_price:
                return None

            # Use technical levels if available
            technical_data = analysis.get("technical_analysis", {})
            resistance = technical_data.get("resistance_level")

            if resistance and resistance > current_price:
                return resistance
            else:
                # Fallback to risk-reward ratio
                stop_loss = self._calculate_stop_loss(analysis)
                if stop_loss:
                    risk_amount = current_price - stop_loss
                    return current_price + (2 * risk_amount)  # 2:1 risk-reward ratio
                else:
                    # Simple percentage target
                    return current_price * 1.15  # 15% target

        except Exception as e:
            logger.error(f"Error calculating target price: {e}")
            return None

    def _build_recommendation_reasoning(self, analysis: Dict[str, Any]) -> str:
        """Build reasoning text for recommendations."""
        reasoning_parts = []

        try:
            # Technical reasoning
            technical_data = analysis.get("technical_analysis", {})
            if technical_data:
                reasoning_parts.append("Technical indicators suggest current market conditions")

            # Sentiment reasoning
            news_data = analysis.get("news_sentiment", {})
            sentiment = news_data.get("overall_sentiment", 0.0)
            if sentiment > 0.2:
                reasoning_parts.append("positive news sentiment supports bullish outlook")
            elif sentiment < -0.2:
                reasoning_parts.append("negative news sentiment indicates caution")

            # Risk reasoning
            risk_data = analysis.get("risk_assessment", {})
            risk_level = risk_data.get("risk_level", "medium")
            if risk_level in ["high", "very_high"]:
                reasoning_parts.append("elevated risk levels require careful position management")

            return "; ".join(reasoning_parts) if reasoning_parts else "Based on comprehensive market analysis"

        except Exception as e:
            logger.error(f"Error building recommendation reasoning: {e}")
            return "Analysis based on available market data"

    async def _handle_collaboration(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle collaboration with other agents.

        Args:
            message: Collaboration message
            context: Collaboration context

        Returns:
            Collaboration response
        """
        collaborator = context.get("collaboration_from")
        collaboration_type = context.get("collaboration_type", "request")

        # Add collaboration context
        self.context_engine.add_collaboration_context(
            f"Collaborating with {collaborator}: {message}",
            collaboration_id=context.get("collaboration_id", "unknown"),
            metadata={"partner": collaborator, "type": collaboration_type, "direction": "incoming"}
        )

        return {
            "response": f"I'm ready to collaborate with {collaborator}! I can provide comprehensive stock market analysis, technical indicators, risk assessments, and trading recommendations to support our discussion. My expertise includes real-time market data analysis, news sentiment evaluation, and risk management strategies.",
            "trading_capabilities": [
                "Real-time stock data analysis",
                "Technical indicator calculations",
                "News sentiment analysis",
                "Risk assessment and management",
                "Trading signal generation",
                "Portfolio optimization insights"
            ],
            "collaboration_accepted": True,
            "success": True
        }
