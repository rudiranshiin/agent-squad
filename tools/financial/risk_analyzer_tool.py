"""
Risk Analysis Tool for comprehensive risk assessment of stocks and portfolios.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from framework.mcp.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class RiskAnalyzerTool(BaseTool):
    """
    Tool for comprehensive risk analysis of stocks and trading positions.

    Features:
    - Volatility analysis (historical and implied)
    - Value at Risk (VaR) calculations
    - Maximum drawdown analysis
    - Beta and correlation analysis
    - Position sizing recommendations
    - Risk-adjusted return metrics
    - Stress testing scenarios
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="risk_analyzer",
            description="Comprehensive risk analysis for stocks and trading positions",
            version="1.0.0",
            **kwargs
        )
        self.category = "risk_management"

    async def execute(
        self,
        symbol: str,
        stock_data: Dict[str, Any],
        technical_data: Dict[str, Any] = None,
        risk_tolerance: str = "moderate",
        position_size: float = None,
        portfolio_value: float = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform comprehensive risk analysis.

        Args:
            symbol: Stock symbol
            stock_data: Stock data from Yahoo Finance tool
            technical_data: Technical analysis data
            risk_tolerance: Risk tolerance level (conservative, moderate, aggressive)
            position_size: Proposed position size in dollars
            portfolio_value: Total portfolio value

        Returns:
            Comprehensive risk analysis results
        """
        try:
            # Prepare price data
            price_data = self._prepare_price_data(stock_data)

            if len(price_data) < 10:
                raise ValueError("Insufficient price data for risk analysis (minimum 10 data points required)")

            # Calculate basic risk metrics
            risk_metrics = self._calculate_basic_risk_metrics(price_data)

            # Calculate volatility metrics
            volatility_analysis = self._calculate_volatility_metrics(price_data)

            # Calculate Value at Risk
            var_analysis = self._calculate_var_metrics(price_data)

            # Calculate drawdown analysis
            drawdown_analysis = self._calculate_drawdown_metrics(price_data)

            # Assess risk level
            risk_assessment = self._assess_overall_risk_level(
                risk_metrics, volatility_analysis, var_analysis, drawdown_analysis
            )

            # Position sizing recommendations
            position_recommendations = self._calculate_position_sizing(
                risk_assessment, risk_tolerance, position_size, portfolio_value
            )

            # Risk-adjusted performance metrics
            performance_metrics = self._calculate_risk_adjusted_metrics(price_data, stock_data)

            # Stress testing
            stress_test_results = self._perform_stress_testing(price_data, stock_data)

            # Market risk factors
            market_risk_factors = self._analyze_market_risk_factors(stock_data, technical_data)

            # Compile comprehensive results
            results = {
                "symbol": symbol,
                "analysis_timestamp": datetime.now().isoformat(),
                "risk_level": risk_assessment["overall_risk_level"],
                "risk_score": risk_assessment["risk_score"],
                "confidence": risk_assessment["confidence"],

                "volatility_analysis": volatility_analysis,
                "var_analysis": var_analysis,
                "drawdown_analysis": drawdown_analysis,
                "position_recommendations": position_recommendations,
                "performance_metrics": performance_metrics,
                "stress_test_results": stress_test_results,
                "market_risk_factors": market_risk_factors,

                "risk_summary": self._generate_risk_summary(risk_assessment, risk_tolerance),
                "recommendations": self._generate_risk_recommendations(
                    risk_assessment, risk_tolerance, position_recommendations
                )
            }

            logger.info(f"Risk analysis completed for {symbol}: {risk_assessment['overall_risk_level']} risk level")
            return results

        except Exception as e:
            logger.error(f"Error performing risk analysis for {symbol}: {e}")
            raise

    def _prepare_price_data(self, stock_data: Dict[str, Any]) -> pd.Series:
        """Prepare price data for analysis."""
        recent_prices = stock_data.get("recent_price_action", [])

        if not recent_prices:
            raise ValueError("No recent price action data available")

        # Convert to pandas Series
        prices = pd.Series([float(day["close"]) for day in recent_prices])
        dates = pd.to_datetime([day["date"] for day in recent_prices])

        price_series = pd.Series(prices.values, index=dates)
        return price_series.sort_index()

    def _calculate_basic_risk_metrics(self, price_data: pd.Series) -> Dict[str, Any]:
        """Calculate basic risk metrics."""
        # Calculate returns
        returns = price_data.pct_change().dropna()

        if len(returns) == 0:
            return {"error": "Insufficient data for return calculation"}

        # Basic statistics
        mean_return = float(returns.mean())
        std_return = float(returns.std())
        skewness = float(returns.skew()) if len(returns) > 2 else 0.0
        kurtosis = float(returns.kurtosis()) if len(returns) > 3 else 0.0

        # Annualized metrics (assuming daily data)
        trading_days = 252
        annualized_return = mean_return * trading_days
        annualized_volatility = std_return * np.sqrt(trading_days)

        return {
            "daily_mean_return": mean_return,
            "daily_volatility": std_return,
            "annualized_return": annualized_return,
            "annualized_volatility": annualized_volatility,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "return_distribution": {
                "min": float(returns.min()),
                "max": float(returns.max()),
                "median": float(returns.median()),
                "q25": float(returns.quantile(0.25)),
                "q75": float(returns.quantile(0.75))
            }
        }

    def _calculate_volatility_metrics(self, price_data: pd.Series) -> Dict[str, Any]:
        """Calculate comprehensive volatility metrics."""
        returns = price_data.pct_change().dropna()

        if len(returns) < 5:
            return {"error": "Insufficient data for volatility analysis"}

        # Historical volatility (different periods)
        volatility_metrics = {}

        # Short-term volatility (last 5 days if available)
        if len(returns) >= 5:
            short_term_vol = float(returns.tail(5).std() * np.sqrt(252))
            volatility_metrics["short_term_volatility"] = short_term_vol

        # Medium-term volatility (last 10 days if available)
        if len(returns) >= 10:
            medium_term_vol = float(returns.tail(10).std() * np.sqrt(252))
            volatility_metrics["medium_term_volatility"] = medium_term_vol

        # Full period volatility
        full_period_vol = float(returns.std() * np.sqrt(252))
        volatility_metrics["full_period_volatility"] = full_period_vol

        # Volatility trend
        if len(returns) >= 10:
            recent_vol = returns.tail(5).std() if len(returns) >= 5 else returns.std()
            older_vol = returns.head(5).std() if len(returns) >= 10 else returns.std()

            vol_change = (recent_vol - older_vol) / older_vol if older_vol != 0 else 0

            if vol_change > 0.2:
                vol_trend = "increasing"
            elif vol_change < -0.2:
                vol_trend = "decreasing"
            else:
                vol_trend = "stable"

            volatility_metrics["volatility_trend"] = vol_trend
            volatility_metrics["volatility_change"] = float(vol_change)

        # Volatility classification
        if full_period_vol > 0.4:  # 40%+ annualized volatility
            vol_classification = "very_high"
        elif full_period_vol > 0.25:  # 25%+ annualized volatility
            vol_classification = "high"
        elif full_period_vol > 0.15:  # 15%+ annualized volatility
            vol_classification = "moderate"
        else:
            vol_classification = "low"

        volatility_metrics["volatility_classification"] = vol_classification

        return volatility_metrics

    def _calculate_var_metrics(self, price_data: pd.Series, confidence_levels: List[float] = None) -> Dict[str, Any]:
        """Calculate Value at Risk metrics."""
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]  # 95% and 99% confidence levels

        returns = price_data.pct_change().dropna()

        if len(returns) < 10:
            return {"error": "Insufficient data for VaR calculation"}

        var_results = {}

        for confidence in confidence_levels:
            # Historical VaR (percentile method)
            var_percentile = float(returns.quantile(1 - confidence))

            # Parametric VaR (assuming normal distribution)
            mean_return = returns.mean()
            std_return = returns.std()
            z_score = -1.645 if confidence == 0.95 else -2.326  # For 95% and 99%
            var_parametric = float(mean_return + z_score * std_return)

            var_results[f"var_{int(confidence*100)}"] = {
                "historical_var": var_percentile,
                "parametric_var": var_parametric,
                "confidence_level": confidence
            }

        # Expected Shortfall (Conditional VaR)
        var_95 = var_results.get("var_95", {}).get("historical_var", 0)
        if var_95 != 0:
            tail_returns = returns[returns <= var_95]
            expected_shortfall = float(tail_returns.mean()) if len(tail_returns) > 0 else var_95
            var_results["expected_shortfall_95"] = expected_shortfall

        return var_results

    def _calculate_drawdown_metrics(self, price_data: pd.Series) -> Dict[str, Any]:
        """Calculate drawdown analysis."""
        if len(price_data) < 2:
            return {"error": "Insufficient data for drawdown analysis"}

        # Calculate running maximum (peak)
        running_max = price_data.expanding().max()

        # Calculate drawdown
        drawdown = (price_data - running_max) / running_max

        # Maximum drawdown
        max_drawdown = float(drawdown.min())

        # Current drawdown
        current_drawdown = float(drawdown.iloc[-1])

        # Drawdown duration analysis
        drawdown_periods = []
        in_drawdown = False
        start_idx = None

        for i, dd in enumerate(drawdown):
            if dd < -0.01 and not in_drawdown:  # Start of drawdown (>1%)
                in_drawdown = True
                start_idx = i
            elif dd >= -0.001 and in_drawdown:  # End of drawdown
                in_drawdown = False
                if start_idx is not None:
                    duration = i - start_idx
                    drawdown_periods.append(duration)

        # Average drawdown duration
        avg_drawdown_duration = np.mean(drawdown_periods) if drawdown_periods else 0

        # Recovery analysis
        recovery_time = None
        if current_drawdown < -0.01:  # Currently in drawdown
            # Estimate recovery time based on historical patterns
            if drawdown_periods:
                recovery_time = int(np.median(drawdown_periods))

        return {
            "max_drawdown": max_drawdown,
            "current_drawdown": current_drawdown,
            "avg_drawdown_duration": float(avg_drawdown_duration),
            "drawdown_periods_count": len(drawdown_periods),
            "estimated_recovery_time": recovery_time,
            "drawdown_classification": self._classify_drawdown(max_drawdown)
        }

    def _assess_overall_risk_level(
        self,
        risk_metrics: Dict[str, Any],
        volatility_analysis: Dict[str, Any],
        var_analysis: Dict[str, Any],
        drawdown_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall risk level based on all metrics."""

        risk_factors = []
        risk_score = 0.0

        # Volatility risk factor
        vol_class = volatility_analysis.get("volatility_classification", "moderate")
        vol_scores = {"low": 1, "moderate": 2, "high": 3, "very_high": 4}
        vol_score = vol_scores.get(vol_class, 2)
        risk_score += vol_score * 0.3

        if vol_class in ["high", "very_high"]:
            risk_factors.append(f"High volatility ({vol_class})")

        # Drawdown risk factor
        max_dd = abs(drawdown_analysis.get("max_drawdown", 0))
        if max_dd > 0.3:  # 30%+ drawdown
            dd_score = 4
            risk_factors.append(f"Severe historical drawdown ({max_dd:.1%})")
        elif max_dd > 0.2:  # 20%+ drawdown
            dd_score = 3
            risk_factors.append(f"Significant historical drawdown ({max_dd:.1%})")
        elif max_dd > 0.1:  # 10%+ drawdown
            dd_score = 2
        else:
            dd_score = 1

        risk_score += dd_score * 0.25

        # VaR risk factor
        var_95 = abs(var_analysis.get("var_95", {}).get("historical_var", 0))
        if var_95 > 0.05:  # 5%+ daily VaR
            var_score = 4
            risk_factors.append(f"High daily VaR ({var_95:.1%})")
        elif var_95 > 0.03:  # 3%+ daily VaR
            var_score = 3
        elif var_95 > 0.02:  # 2%+ daily VaR
            var_score = 2
        else:
            var_score = 1

        risk_score += var_score * 0.2

        # Return distribution risk factors
        skewness = risk_metrics.get("skewness", 0)
        kurtosis = risk_metrics.get("kurtosis", 0)

        if skewness < -0.5:  # Negative skew (tail risk)
            risk_factors.append("Negative return skew (tail risk)")
            risk_score += 0.5

        if kurtosis > 3:  # High kurtosis (fat tails)
            risk_factors.append("High kurtosis (extreme events)")
            risk_score += 0.5

        # Current market conditions
        current_dd = abs(drawdown_analysis.get("current_drawdown", 0))
        if current_dd > 0.1:  # Currently in 10%+ drawdown
            risk_factors.append(f"Currently in drawdown ({current_dd:.1%})")
            risk_score += 0.5

        # Normalize risk score to 1-5 scale
        risk_score = min(max(risk_score, 1.0), 5.0)

        # Determine risk level
        if risk_score >= 4.0:
            risk_level = "very_high"
        elif risk_score >= 3.0:
            risk_level = "high"
        elif risk_score >= 2.0:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Calculate confidence based on data quality
        data_points = len(risk_metrics.get("return_distribution", {}).get("min", []))
        confidence = min(0.5 + (data_points / 40), 1.0)  # Higher confidence with more data

        return {
            "overall_risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "confidence": confidence,
            "assessment_basis": {
                "volatility_weight": 0.3,
                "drawdown_weight": 0.25,
                "var_weight": 0.2,
                "distribution_weight": 0.25
            }
        }

    def _calculate_position_sizing(
        self,
        risk_assessment: Dict[str, Any],
        risk_tolerance: str,
        position_size: float = None,
        portfolio_value: float = None
    ) -> Dict[str, Any]:
        """Calculate position sizing recommendations."""

        risk_level = risk_assessment["overall_risk_level"]

        # Base position size recommendations by risk tolerance and asset risk
        position_matrix = {
            "conservative": {"low": 0.05, "medium": 0.03, "high": 0.02, "very_high": 0.01},
            "moderate": {"low": 0.08, "medium": 0.05, "high": 0.03, "very_high": 0.02},
            "aggressive": {"low": 0.12, "medium": 0.08, "high": 0.05, "very_high": 0.03}
        }

        recommended_pct = position_matrix.get(risk_tolerance, position_matrix["moderate"]).get(risk_level, 0.05)

        recommendations = {
            "recommended_position_percentage": recommended_pct,
            "risk_tolerance": risk_tolerance,
            "asset_risk_level": risk_level
        }

        if portfolio_value:
            recommended_dollar_amount = portfolio_value * recommended_pct
            recommendations["recommended_dollar_amount"] = recommended_dollar_amount

            if position_size:
                position_pct = position_size / portfolio_value
                recommendations["proposed_position_percentage"] = position_pct

                if position_pct > recommended_pct * 1.5:
                    recommendations["position_warning"] = "Proposed position size exceeds recommended allocation"
                elif position_pct < recommended_pct * 0.5:
                    recommendations["position_note"] = "Proposed position size is conservative relative to recommendation"

        # Kelly Criterion estimate (simplified)
        # This would require expected return estimates in a real implementation
        recommendations["kelly_criterion_note"] = "Kelly Criterion requires expected return estimates for precise calculation"

        return recommendations

    def _calculate_risk_adjusted_metrics(self, price_data: pd.Series, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk-adjusted performance metrics."""
        returns = price_data.pct_change().dropna()

        if len(returns) < 5:
            return {"error": "Insufficient data for risk-adjusted metrics"}

        # Assume risk-free rate (would be fetched from market data in production)
        risk_free_rate = 0.02 / 252  # 2% annual rate, daily

        mean_return = returns.mean()
        std_return = returns.std()

        # Sharpe Ratio
        excess_return = mean_return - risk_free_rate
        sharpe_ratio = float(excess_return / std_return) if std_return != 0 else 0

        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < risk_free_rate]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else std_return
        sortino_ratio = float(excess_return / downside_std) if downside_std != 0 else 0

        # Calmar Ratio (return/max drawdown)
        total_return = (price_data.iloc[-1] / price_data.iloc[0]) - 1
        max_dd = abs(self._calculate_drawdown_metrics(price_data).get("max_drawdown", 0.01))
        calmar_ratio = float(total_return / max_dd) if max_dd != 0 else 0

        return {
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": calmar_ratio,
            "total_return": float(total_return),
            "risk_adjusted_interpretation": self._interpret_risk_adjusted_metrics(sharpe_ratio, sortino_ratio, calmar_ratio)
        }

    def _perform_stress_testing(self, price_data: pd.Series, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform stress testing scenarios."""
        current_price = float(price_data.iloc[-1])

        # Define stress scenarios
        scenarios = {
            "market_crash_2008": -0.37,  # 37% decline like 2008
            "covid_crash_2020": -0.34,   # 34% decline like March 2020
            "moderate_correction": -0.20,  # 20% correction
            "severe_correction": -0.30,   # 30% correction
            "flash_crash": -0.10          # 10% single-day decline
        }

        stress_results = {}

        for scenario_name, decline_pct in scenarios.items():
            stressed_price = current_price * (1 + decline_pct)
            dollar_loss_per_share = current_price - stressed_price

            stress_results[scenario_name] = {
                "price_decline_percent": decline_pct,
                "stressed_price": stressed_price,
                "dollar_loss_per_share": dollar_loss_per_share,
                "scenario_probability": self._estimate_scenario_probability(scenario_name)
            }

        return {
            "current_price": current_price,
            "scenarios": stress_results,
            "stress_test_summary": self._summarize_stress_tests(stress_results)
        }

    def _analyze_market_risk_factors(self, stock_data: Dict[str, Any], technical_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze market-specific risk factors."""
        risk_factors = {}

        # Liquidity risk
        volume = stock_data.get("volume", 0)
        avg_volume = stock_data.get("avg_volume", volume)

        if avg_volume > 0:
            volume_ratio = volume / avg_volume
            if volume_ratio < 0.5:
                risk_factors["liquidity_risk"] = "Low trading volume may impact execution"
            elif volume_ratio > 2.0:
                risk_factors["liquidity_note"] = "High volume suggests good liquidity"

        # Market cap risk
        market_cap = stock_data.get("market_cap")
        if market_cap:
            if market_cap < 2e9:  # Less than $2B
                risk_factors["market_cap_risk"] = "Small cap stock with higher volatility risk"
            elif market_cap < 10e9:  # Less than $10B
                risk_factors["market_cap_note"] = "Mid cap stock with moderate liquidity"

        # Price level risk
        current_price = stock_data.get("current_price", 0)
        if current_price < 5:
            risk_factors["price_level_risk"] = "Low-priced stock with higher volatility and bid-ask spread risk"

        # 52-week position risk
        high_52w = stock_data.get("fifty_two_week_high")
        low_52w = stock_data.get("fifty_two_week_low")

        if high_52w and low_52w and current_price:
            position_in_range = (current_price - low_52w) / (high_52w - low_52w)

            if position_in_range > 0.9:
                risk_factors["price_position_risk"] = "Trading near 52-week high, potential for reversal"
            elif position_in_range < 0.1:
                risk_factors["price_position_opportunity"] = "Trading near 52-week low, potential for recovery"

        # Technical risk factors
        if technical_data:
            rsi_data = technical_data.get("indicators", {}).get("rsi", {})
            if isinstance(rsi_data, dict):
                rsi_value = rsi_data.get("value", 50)
                if rsi_value > 80:
                    risk_factors["technical_risk"] = "Overbought conditions (RSI > 80)"
                elif rsi_value < 20:
                    risk_factors["technical_opportunity"] = "Oversold conditions (RSI < 20)"

        return risk_factors

    def _generate_risk_summary(self, risk_assessment: Dict[str, Any], risk_tolerance: str) -> str:
        """Generate human-readable risk summary."""
        risk_level = risk_assessment["overall_risk_level"]
        risk_score = risk_assessment["risk_score"]
        risk_factors = risk_assessment.get("risk_factors", [])

        summary = f"Overall Risk Assessment: {risk_level.upper()} (Score: {risk_score:.1f}/5.0)\n\n"

        if risk_factors:
            summary += "Key Risk Factors:\n"
            for factor in risk_factors:
                summary += f"• {factor}\n"
            summary += "\n"

        # Risk tolerance alignment
        tolerance_alignment = self._assess_risk_tolerance_alignment(risk_level, risk_tolerance)
        summary += f"Risk Tolerance Alignment: {tolerance_alignment}\n"

        return summary.strip()

    def _generate_risk_recommendations(
        self,
        risk_assessment: Dict[str, Any],
        risk_tolerance: str,
        position_recommendations: Dict[str, Any]
    ) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []

        risk_level = risk_assessment["overall_risk_level"]

        # Position sizing recommendations
        recommended_pct = position_recommendations.get("recommended_position_percentage", 0.05)
        recommendations.append(f"Recommended position size: {recommended_pct:.1%} of portfolio")

        # Risk-specific recommendations
        if risk_level in ["high", "very_high"]:
            recommendations.append("Consider using stop-loss orders to limit downside risk")
            recommendations.append("Monitor position closely due to elevated risk levels")

            if risk_tolerance == "conservative":
                recommendations.append("This asset may not align with conservative risk tolerance")

        # General risk management
        recommendations.append("Diversify across multiple positions to reduce concentration risk")
        recommendations.append("Regular portfolio rebalancing recommended")

        if "High volatility" in str(risk_assessment.get("risk_factors", [])):
            recommendations.append("Consider volatility-based position sizing")

        return recommendations

    # Helper methods
    def _classify_drawdown(self, max_drawdown: float) -> str:
        """Classify drawdown severity."""
        abs_dd = abs(max_drawdown)
        if abs_dd > 0.5:
            return "severe"
        elif abs_dd > 0.3:
            return "significant"
        elif abs_dd > 0.15:
            return "moderate"
        else:
            return "mild"

    def _interpret_risk_adjusted_metrics(self, sharpe: float, sortino: float, calmar: float) -> str:
        """Interpret risk-adjusted performance metrics."""
        if sharpe > 1.0:
            sharpe_desc = "excellent"
        elif sharpe > 0.5:
            sharpe_desc = "good"
        elif sharpe > 0:
            sharpe_desc = "acceptable"
        else:
            sharpe_desc = "poor"

        return f"Sharpe ratio indicates {sharpe_desc} risk-adjusted returns"

    def _estimate_scenario_probability(self, scenario_name: str) -> str:
        """Estimate probability of stress scenarios."""
        probabilities = {
            "market_crash_2008": "very_low",
            "covid_crash_2020": "low",
            "moderate_correction": "moderate",
            "severe_correction": "low",
            "flash_crash": "low"
        }
        return probabilities.get(scenario_name, "unknown")

    def _summarize_stress_tests(self, stress_results: Dict[str, Any]) -> str:
        """Summarize stress test results."""
        worst_case = min(stress_results.values(), key=lambda x: x["price_decline_percent"])
        return f"Worst case scenario: {worst_case['price_decline_percent']:.1%} decline"

    def _assess_risk_tolerance_alignment(self, risk_level: str, risk_tolerance: str) -> str:
        """Assess alignment between asset risk and investor risk tolerance."""
        alignment_matrix = {
            ("low", "conservative"): "Well aligned",
            ("low", "moderate"): "Well aligned",
            ("low", "aggressive"): "Conservative for tolerance",
            ("medium", "conservative"): "Slightly aggressive for tolerance",
            ("medium", "moderate"): "Well aligned",
            ("medium", "aggressive"): "Conservative for tolerance",
            ("high", "conservative"): "Too aggressive for tolerance",
            ("high", "moderate"): "Aggressive for tolerance",
            ("high", "aggressive"): "Aligned",
            ("very_high", "conservative"): "Significantly too aggressive",
            ("very_high", "moderate"): "Too aggressive for tolerance",
            ("very_high", "aggressive"): "Aggressive even for high tolerance"
        }

        return alignment_matrix.get((risk_level, risk_tolerance), "Alignment unclear")

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol for risk analysis"
                },
                "stock_data": {
                    "type": "object",
                    "description": "Stock data from Yahoo Finance tool"
                },
                "technical_data": {
                    "type": "object",
                    "description": "Technical analysis data (optional)"
                },
                "risk_tolerance": {
                    "type": "string",
                    "enum": ["conservative", "moderate", "aggressive"],
                    "description": "Investor risk tolerance level",
                    "default": "moderate"
                },
                "position_size": {
                    "type": "number",
                    "description": "Proposed position size in dollars (optional)"
                },
                "portfolio_value": {
                    "type": "number",
                    "description": "Total portfolio value in dollars (optional)"
                }
            },
            "required": ["symbol", "stock_data"]
        }

    async def health_check(self) -> bool:
        """Perform health check with sample data."""
        try:
            # Create sample stock data
            sample_stock_data = {
                "symbol": "TEST",
                "current_price": 100,
                "recent_price_action": [
                    {"date": "2024-01-01", "close": 95},
                    {"date": "2024-01-02", "close": 98},
                    {"date": "2024-01-03", "close": 102},
                    {"date": "2024-01-04", "close": 99},
                    {"date": "2024-01-05", "close": 105},
                    {"date": "2024-01-06", "close": 103},
                    {"date": "2024-01-07", "close": 107},
                    {"date": "2024-01-08", "close": 104},
                    {"date": "2024-01-09", "close": 108},
                    {"date": "2024-01-10", "close": 110}
                ]
            }

            result = await self.execute("TEST", sample_stock_data)
            return "risk_level" in result and "risk_score" in result

        except Exception as e:
            logger.error(f"Risk analyzer health check failed: {e}")
            return False
