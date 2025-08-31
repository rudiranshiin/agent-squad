"""
Portfolio Analysis Tool for multi-asset portfolio optimization and analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from framework.mcp.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class PortfolioAnalyzerTool(BaseTool):
    """
    Tool for comprehensive portfolio analysis and optimization.

    Features:
    - Multi-asset correlation analysis
    - Diversification scoring
    - Portfolio risk metrics
    - Optimal allocation suggestions
    - Rebalancing recommendations
    - Performance attribution
    - Sector/geographic exposure analysis
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="portfolio_analyzer",
            description="Comprehensive portfolio analysis and optimization tool",
            version="1.0.0",
            **kwargs
        )
        self.category = "portfolio_management"

    async def execute(
        self,
        symbols: List[str],
        analyses: List[Dict[str, Any]],
        correlation_analysis: bool = True,
        diversification_score: bool = True,
        current_weights: List[float] = None,
        target_risk: str = "moderate",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform comprehensive portfolio analysis.

        Args:
            symbols: List of stock symbols in the portfolio
            analyses: List of individual stock analyses
            correlation_analysis: Whether to perform correlation analysis
            diversification_score: Whether to calculate diversification metrics
            current_weights: Current portfolio weights (optional)
            target_risk: Target risk level for optimization

        Returns:
            Comprehensive portfolio analysis results
        """
        try:
            if len(symbols) != len(analyses):
                raise ValueError("Number of symbols must match number of analyses")

            if len(symbols) < 2:
                raise ValueError("Portfolio analysis requires at least 2 assets")

            # Prepare portfolio data
            portfolio_data = self._prepare_portfolio_data(symbols, analyses)

            # Calculate correlation matrix if requested
            correlation_results = {}
            if correlation_analysis:
                correlation_results = self._calculate_correlation_analysis(portfolio_data)

            # Calculate diversification metrics
            diversification_results = {}
            if diversification_score:
                diversification_results = self._calculate_diversification_metrics(
                    portfolio_data, correlation_results
                )

            # Portfolio risk analysis
            portfolio_risk = self._calculate_portfolio_risk_metrics(portfolio_data, current_weights)

            # Sector and geographic analysis
            sector_analysis = self._analyze_sector_exposure(portfolio_data)

            # Optimization recommendations
            optimization_results = self._generate_optimization_recommendations(
                portfolio_data, correlation_results, target_risk, current_weights
            )

            # Rebalancing analysis
            rebalancing_analysis = self._analyze_rebalancing_opportunities(
                portfolio_data, current_weights, optimization_results
            )

            # Performance attribution
            performance_attribution = self._calculate_performance_attribution(portfolio_data, current_weights)

            # Risk-return efficiency
            efficiency_analysis = self._analyze_risk_return_efficiency(portfolio_data)

            # Compile comprehensive results
            results = {
                "portfolio_summary": {
                    "symbols": symbols,
                    "asset_count": len(symbols),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "target_risk_level": target_risk
                },

                "correlation_analysis": correlation_results,
                "diversification_analysis": diversification_results,
                "portfolio_risk_metrics": portfolio_risk,
                "sector_analysis": sector_analysis,
                "optimization_recommendations": optimization_results,
                "rebalancing_analysis": rebalancing_analysis,
                "performance_attribution": performance_attribution,
                "efficiency_analysis": efficiency_analysis,

                "portfolio_score": self._calculate_overall_portfolio_score(
                    diversification_results, portfolio_risk, efficiency_analysis
                ),
                "recommendations": self._generate_portfolio_recommendations(
                    diversification_results, portfolio_risk, optimization_results, rebalancing_analysis
                )
            }

            logger.info(f"Portfolio analysis completed for {len(symbols)} assets")
            return results

        except Exception as e:
            logger.error(f"Error performing portfolio analysis: {e}")
            raise

    def _prepare_portfolio_data(self, symbols: List[str], analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare portfolio data for analysis."""
        portfolio_data = {
            "symbols": symbols,
            "assets": {}
        }

        for i, symbol in enumerate(symbols):
            analysis = analyses[i]

            # Extract key metrics from each analysis
            stock_data = analysis.get("stock_data", {})
            risk_data = analysis.get("risk_assessment", {})
            technical_data = analysis.get("technical_analysis", {})

            asset_info = {
                "symbol": symbol,
                "current_price": stock_data.get("current_price", 0),
                "market_cap": stock_data.get("market_cap"),
                "sector": stock_data.get("sector", "Unknown"),
                "industry": stock_data.get("industry", "Unknown"),
                "currency": stock_data.get("currency", "USD"),
                "exchange": stock_data.get("exchange", "Unknown"),

                # Risk metrics
                "risk_level": risk_data.get("risk_level", "medium"),
                "risk_score": risk_data.get("risk_score", 3.0),
                "volatility": risk_data.get("volatility_analysis", {}).get("full_period_volatility", 0.2),
                "max_drawdown": abs(risk_data.get("drawdown_analysis", {}).get("max_drawdown", 0.1)),

                # Performance metrics
                "price_change_percent": stock_data.get("price_change_percent", 0),
                "ytd_return": self._calculate_ytd_return(stock_data),

                # Technical metrics
                "rsi": technical_data.get("indicators", {}).get("rsi", {}).get("value", 50),
                "technical_sentiment": self._extract_technical_sentiment(technical_data),

                # Fundamental metrics
                "pe_ratio": stock_data.get("fundamentals", {}).get("pe_ratio"),
                "market_cap_category": self._categorize_market_cap(stock_data.get("market_cap"))
            }

            portfolio_data["assets"][symbol] = asset_info

        return portfolio_data

    def _calculate_correlation_analysis(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate correlation analysis between portfolio assets."""
        symbols = portfolio_data["symbols"]

        if len(symbols) < 2:
            return {"error": "Need at least 2 assets for correlation analysis"}

        # Create correlation matrix based on available data
        # In a real implementation, you would use historical price data
        # For now, we'll estimate based on sector and risk characteristics

        correlation_matrix = {}
        avg_correlation = 0.0
        correlation_pairs = []

        for i, symbol1 in enumerate(symbols):
            correlation_matrix[symbol1] = {}
            asset1 = portfolio_data["assets"][symbol1]

            for j, symbol2 in enumerate(symbols):
                if i == j:
                    correlation_matrix[symbol1][symbol2] = 1.0
                else:
                    asset2 = portfolio_data["assets"][symbol2]

                    # Estimate correlation based on sector, market cap, and risk
                    correlation = self._estimate_correlation(asset1, asset2)
                    correlation_matrix[symbol1][symbol2] = correlation

                    if i < j:  # Avoid double counting
                        correlation_pairs.append({
                            "asset1": symbol1,
                            "asset2": symbol2,
                            "correlation": correlation,
                            "interpretation": self._interpret_correlation(correlation)
                        })
                        avg_correlation += correlation

        avg_correlation = avg_correlation / len(correlation_pairs) if correlation_pairs else 0.0

        # Find highest and lowest correlations
        if correlation_pairs:
            highest_corr = max(correlation_pairs, key=lambda x: x["correlation"])
            lowest_corr = min(correlation_pairs, key=lambda x: x["correlation"])
        else:
            highest_corr = lowest_corr = None

        return {
            "correlation_matrix": correlation_matrix,
            "average_correlation": avg_correlation,
            "correlation_pairs": correlation_pairs,
            "highest_correlation": highest_corr,
            "lowest_correlation": lowest_corr,
            "correlation_interpretation": self._interpret_portfolio_correlation(avg_correlation)
        }

    def _calculate_diversification_metrics(
        self,
        portfolio_data: Dict[str, Any],
        correlation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate portfolio diversification metrics."""

        assets = portfolio_data["assets"]
        symbols = portfolio_data["symbols"]

        # Sector diversification
        sectors = {}
        for symbol, asset in assets.items():
            sector = asset.get("sector", "Unknown")
            sectors[sector] = sectors.get(sector, 0) + 1

        sector_count = len(sectors)
        sector_concentration = max(sectors.values()) / len(symbols) if sectors else 1.0

        # Market cap diversification
        market_caps = {}
        for symbol, asset in assets.items():
            cap_category = asset.get("market_cap_category", "Unknown")
            market_caps[cap_category] = market_caps.get(cap_category, 0) + 1

        cap_diversity = len(market_caps)

        # Risk level diversification
        risk_levels = {}
        for symbol, asset in assets.items():
            risk_level = asset.get("risk_level", "medium")
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1

        risk_diversity = len(risk_levels)

        # Geographic diversification (based on exchange)
        exchanges = {}
        for symbol, asset in assets.items():
            exchange = asset.get("exchange", "Unknown")
            exchanges[exchange] = exchanges.get(exchange, 0) + 1

        geographic_diversity = len(exchanges)

        # Overall diversification score
        avg_correlation = correlation_results.get("average_correlation", 0.5)

        # Calculate diversification score (0-100)
        diversification_score = self._calculate_diversification_score(
            sector_count, sector_concentration, cap_diversity, risk_diversity,
            geographic_diversity, avg_correlation, len(symbols)
        )

        return {
            "diversification_score": diversification_score,
            "sector_analysis": {
                "unique_sectors": sector_count,
                "sector_distribution": sectors,
                "sector_concentration": sector_concentration
            },
            "market_cap_analysis": {
                "cap_categories": cap_diversity,
                "cap_distribution": market_caps
            },
            "risk_analysis": {
                "risk_levels": risk_diversity,
                "risk_distribution": risk_levels
            },
            "geographic_analysis": {
                "exchanges": geographic_diversity,
                "exchange_distribution": exchanges
            },
            "correlation_impact": {
                "average_correlation": avg_correlation,
                "correlation_benefit": self._assess_correlation_benefit(avg_correlation)
            },
            "diversification_interpretation": self._interpret_diversification_score(diversification_score)
        }

    def _calculate_portfolio_risk_metrics(
        self,
        portfolio_data: Dict[str, Any],
        current_weights: List[float] = None
    ) -> Dict[str, Any]:
        """Calculate portfolio-level risk metrics."""

        assets = portfolio_data["assets"]
        symbols = portfolio_data["symbols"]

        # Use equal weights if not provided
        if current_weights is None:
            current_weights = [1.0 / len(symbols)] * len(symbols)
        elif len(current_weights) != len(symbols):
            raise ValueError("Number of weights must match number of symbols")

        # Normalize weights
        total_weight = sum(current_weights)
        weights = [w / total_weight for w in current_weights]

        # Calculate weighted portfolio metrics
        portfolio_volatility = 0.0
        portfolio_risk_score = 0.0
        portfolio_max_drawdown = 0.0

        for i, symbol in enumerate(symbols):
            asset = assets[symbol]
            weight = weights[i]

            portfolio_volatility += weight * asset.get("volatility", 0.2)
            portfolio_risk_score += weight * asset.get("risk_score", 3.0)
            portfolio_max_drawdown += weight * asset.get("max_drawdown", 0.1)

        # Risk level classification
        if portfolio_risk_score >= 4.0:
            portfolio_risk_level = "very_high"
        elif portfolio_risk_score >= 3.0:
            portfolio_risk_level = "high"
        elif portfolio_risk_score >= 2.0:
            portfolio_risk_level = "medium"
        else:
            portfolio_risk_level = "low"

        # Concentration risk
        max_weight = max(weights)
        concentration_risk = "high" if max_weight > 0.4 else "medium" if max_weight > 0.25 else "low"

        return {
            "portfolio_risk_level": portfolio_risk_level,
            "portfolio_risk_score": portfolio_risk_score,
            "portfolio_volatility": portfolio_volatility,
            "portfolio_max_drawdown": portfolio_max_drawdown,
            "concentration_risk": concentration_risk,
            "max_position_weight": max_weight,
            "weights": dict(zip(symbols, weights)),
            "risk_contribution": dict(zip(symbols, [w * assets[s].get("risk_score", 3.0) for w, s in zip(weights, symbols)]))
        }

    def _analyze_sector_exposure(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sector and industry exposure."""

        assets = portfolio_data["assets"]

        # Sector analysis
        sector_exposure = {}
        industry_exposure = {}

        for symbol, asset in assets.items():
            sector = asset.get("sector", "Unknown")
            industry = asset.get("industry", "Unknown")

            sector_exposure[sector] = sector_exposure.get(sector, []) + [symbol]
            industry_exposure[industry] = industry_exposure.get(industry, []) + [symbol]

        # Calculate exposure percentages (assuming equal weights for simplicity)
        total_assets = len(assets)

        sector_percentages = {
            sector: len(symbols) / total_assets * 100
            for sector, symbols in sector_exposure.items()
        }

        # Identify concentration risks
        max_sector_exposure = max(sector_percentages.values()) if sector_percentages else 0
        concentrated_sectors = [
            sector for sector, pct in sector_percentages.items() if pct > 40
        ]

        return {
            "sector_exposure": sector_exposure,
            "sector_percentages": sector_percentages,
            "industry_exposure": industry_exposure,
            "max_sector_exposure": max_sector_exposure,
            "concentrated_sectors": concentrated_sectors,
            "sector_diversification": len(sector_exposure),
            "industry_diversification": len(industry_exposure),
            "exposure_analysis": self._analyze_exposure_risks(sector_percentages)
        }

    def _generate_optimization_recommendations(
        self,
        portfolio_data: Dict[str, Any],
        correlation_results: Dict[str, Any],
        target_risk: str,
        current_weights: List[float] = None
    ) -> Dict[str, Any]:
        """Generate portfolio optimization recommendations."""

        symbols = portfolio_data["symbols"]
        assets = portfolio_data["assets"]

        # Target risk parameters
        risk_targets = {
            "conservative": {"max_risk_score": 2.5, "max_volatility": 0.15, "max_single_weight": 0.3},
            "moderate": {"max_risk_score": 3.5, "max_volatility": 0.25, "max_single_weight": 0.4},
            "aggressive": {"max_risk_score": 4.5, "max_volatility": 0.35, "max_single_weight": 0.5}
        }

        target_params = risk_targets.get(target_risk, risk_targets["moderate"])

        # Simple optimization approach (equal risk contribution)
        # In a real implementation, you would use modern portfolio theory

        # Calculate risk-adjusted scores for each asset
        asset_scores = {}
        for symbol in symbols:
            asset = assets[symbol]

            # Score based on risk-return characteristics
            risk_score = asset.get("risk_score", 3.0)
            volatility = asset.get("volatility", 0.2)

            # Lower risk score is better, adjust for target risk
            risk_penalty = abs(risk_score - target_params["max_risk_score"]) / 2.0
            vol_penalty = max(0, volatility - target_params["max_volatility"]) * 5.0

            score = 1.0 - (risk_penalty + vol_penalty) / 2.0
            asset_scores[symbol] = max(0.1, score)  # Minimum 10% score

        # Calculate suggested weights
        total_score = sum(asset_scores.values())
        suggested_weights = {
            symbol: score / total_score for symbol, score in asset_scores.items()
        }

        # Apply maximum weight constraints
        max_weight = target_params["max_single_weight"]
        for symbol in suggested_weights:
            if suggested_weights[symbol] > max_weight:
                excess = suggested_weights[symbol] - max_weight
                suggested_weights[symbol] = max_weight

                # Redistribute excess to other assets
                other_symbols = [s for s in symbols if s != symbol]
                if other_symbols:
                    redistribution = excess / len(other_symbols)
                    for other_symbol in other_symbols:
                        suggested_weights[other_symbol] += redistribution

        # Renormalize
        total_weight = sum(suggested_weights.values())
        suggested_weights = {s: w / total_weight for s, w in suggested_weights.items()}

        return {
            "target_risk_level": target_risk,
            "target_parameters": target_params,
            "asset_scores": asset_scores,
            "suggested_weights": suggested_weights,
            "current_weights": dict(zip(symbols, current_weights)) if current_weights else None,
            "optimization_method": "risk_adjusted_scoring",
            "weight_constraints": {
                "max_single_position": max_weight,
                "min_single_position": 0.05  # 5% minimum
            }
        }

    def _analyze_rebalancing_opportunities(
        self,
        portfolio_data: Dict[str, Any],
        current_weights: List[float] = None,
        optimization_results: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze rebalancing opportunities."""

        symbols = portfolio_data["symbols"]

        if current_weights is None or optimization_results is None:
            return {"rebalancing_needed": False, "reason": "Insufficient data for rebalancing analysis"}

        current_weights_dict = dict(zip(symbols, current_weights))
        suggested_weights = optimization_results.get("suggested_weights", {})

        # Calculate weight differences
        weight_differences = {}
        total_deviation = 0.0

        for symbol in symbols:
            current = current_weights_dict.get(symbol, 0)
            suggested = suggested_weights.get(symbol, 0)
            difference = suggested - current
            weight_differences[symbol] = {
                "current": current,
                "suggested": suggested,
                "difference": difference,
                "abs_difference": abs(difference)
            }
            total_deviation += abs(difference)

        # Determine if rebalancing is needed
        rebalancing_threshold = 0.05  # 5% threshold
        needs_rebalancing = total_deviation > rebalancing_threshold

        # Identify assets to buy/sell
        to_buy = {s: d for s, d in weight_differences.items() if d["difference"] > 0.02}
        to_sell = {s: d for s, d in weight_differences.items() if d["difference"] < -0.02}

        return {
            "rebalancing_needed": needs_rebalancing,
            "total_deviation": total_deviation,
            "rebalancing_threshold": rebalancing_threshold,
            "weight_differences": weight_differences,
            "assets_to_increase": to_buy,
            "assets_to_decrease": to_sell,
            "rebalancing_priority": "high" if total_deviation > 0.15 else "medium" if total_deviation > 0.1 else "low",
            "estimated_trades": len(to_buy) + len(to_sell)
        }

    def _calculate_performance_attribution(
        self,
        portfolio_data: Dict[str, Any],
        current_weights: List[float] = None
    ) -> Dict[str, Any]:
        """Calculate performance attribution analysis."""

        symbols = portfolio_data["symbols"]
        assets = portfolio_data["assets"]

        if current_weights is None:
            current_weights = [1.0 / len(symbols)] * len(symbols)

        # Normalize weights
        total_weight = sum(current_weights)
        weights = [w / total_weight for w in current_weights]

        # Calculate weighted performance
        total_return = 0.0
        performance_contributions = {}

        for i, symbol in enumerate(symbols):
            asset = assets[symbol]
            weight = weights[i]
            asset_return = asset.get("price_change_percent", 0) / 100  # Convert to decimal

            contribution = weight * asset_return
            total_return += contribution

            performance_contributions[symbol] = {
                "weight": weight,
                "return": asset_return,
                "contribution": contribution,
                "contribution_percent": contribution * 100
            }

        # Identify top and bottom contributors
        sorted_contributors = sorted(
            performance_contributions.items(),
            key=lambda x: x[1]["contribution"],
            reverse=True
        )

        top_contributor = sorted_contributors[0] if sorted_contributors else None
        bottom_contributor = sorted_contributors[-1] if sorted_contributors else None

        return {
            "total_portfolio_return": total_return * 100,  # Convert to percentage
            "performance_contributions": performance_contributions,
            "top_contributor": {
                "symbol": top_contributor[0],
                "contribution": top_contributor[1]["contribution_percent"]
            } if top_contributor else None,
            "bottom_contributor": {
                "symbol": bottom_contributor[0],
                "contribution": bottom_contributor[1]["contribution_percent"]
            } if bottom_contributor else None,
            "attribution_analysis": self._analyze_performance_drivers(performance_contributions)
        }

    def _analyze_risk_return_efficiency(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk-return efficiency of the portfolio."""

        assets = portfolio_data["assets"]

        # Calculate efficiency metrics for each asset
        efficiency_metrics = {}

        for symbol, asset in assets.items():
            returns = asset.get("price_change_percent", 0)
            risk_score = asset.get("risk_score", 3.0)
            volatility = asset.get("volatility", 0.2)

            # Simple risk-adjusted return (return per unit of risk)
            risk_adjusted_return = returns / risk_score if risk_score > 0 else 0
            volatility_adjusted_return = returns / (volatility * 100) if volatility > 0 else 0

            efficiency_metrics[symbol] = {
                "return": returns,
                "risk_score": risk_score,
                "volatility": volatility,
                "risk_adjusted_return": risk_adjusted_return,
                "volatility_adjusted_return": volatility_adjusted_return,
                "efficiency_score": (risk_adjusted_return + volatility_adjusted_return) / 2
            }

        # Portfolio-level efficiency
        avg_efficiency = sum(m["efficiency_score"] for m in efficiency_metrics.values()) / len(efficiency_metrics)

        # Rank assets by efficiency
        efficiency_ranking = sorted(
            efficiency_metrics.items(),
            key=lambda x: x[1]["efficiency_score"],
            reverse=True
        )

        return {
            "asset_efficiency_metrics": efficiency_metrics,
            "portfolio_efficiency_score": avg_efficiency,
            "efficiency_ranking": [
                {"symbol": symbol, "score": data["efficiency_score"]}
                for symbol, data in efficiency_ranking
            ],
            "efficiency_interpretation": self._interpret_efficiency_score(avg_efficiency)
        }

    # Helper methods for calculations and interpretations

    def _estimate_correlation(self, asset1: Dict[str, Any], asset2: Dict[str, Any]) -> float:
        """Estimate correlation between two assets based on characteristics."""

        correlation = 0.3  # Base correlation

        # Sector correlation
        if asset1.get("sector") == asset2.get("sector"):
            correlation += 0.4

        # Market cap correlation
        if asset1.get("market_cap_category") == asset2.get("market_cap_category"):
            correlation += 0.2

        # Risk level correlation
        risk1 = asset1.get("risk_score", 3.0)
        risk2 = asset2.get("risk_score", 3.0)
        risk_similarity = 1.0 - abs(risk1 - risk2) / 4.0  # Normalize to 0-1
        correlation += risk_similarity * 0.2

        # Exchange correlation
        if asset1.get("exchange") == asset2.get("exchange"):
            correlation += 0.1

        return min(max(correlation, -0.5), 0.95)  # Clamp between -0.5 and 0.95

    def _categorize_market_cap(self, market_cap: Optional[float]) -> str:
        """Categorize market cap into size categories."""
        if market_cap is None:
            return "Unknown"

        if market_cap >= 200e9:  # $200B+
            return "Mega Cap"
        elif market_cap >= 10e9:  # $10B+
            return "Large Cap"
        elif market_cap >= 2e9:   # $2B+
            return "Mid Cap"
        elif market_cap >= 300e6: # $300M+
            return "Small Cap"
        else:
            return "Micro Cap"

    def _calculate_ytd_return(self, stock_data: Dict[str, Any]) -> float:
        """Calculate year-to-date return (simplified)."""
        # This is a simplified calculation
        # In a real implementation, you would calculate from Jan 1st
        return stock_data.get("price_change_percent", 0)

    def _extract_technical_sentiment(self, technical_data: Dict[str, Any]) -> str:
        """Extract overall technical sentiment."""
        if not technical_data:
            return "neutral"

        summary = technical_data.get("technical_summary", {})
        return summary.get("overall_sentiment", "neutral")

    def _calculate_diversification_score(
        self,
        sector_count: int,
        sector_concentration: float,
        cap_diversity: int,
        risk_diversity: int,
        geographic_diversity: int,
        avg_correlation: float,
        total_assets: int
    ) -> float:
        """Calculate overall diversification score (0-100)."""

        # Sector diversification (0-25 points)
        sector_score = min(sector_count * 5, 25) * (1 - sector_concentration)

        # Asset class diversification (0-20 points)
        cap_score = min(cap_diversity * 7, 20)

        # Risk diversification (0-15 points)
        risk_score = min(risk_diversity * 5, 15)

        # Geographic diversification (0-15 points)
        geo_score = min(geographic_diversity * 5, 15)

        # Correlation benefit (0-25 points)
        correlation_score = max(0, (0.7 - avg_correlation) * 35.7)  # 0.7 correlation = 0 points

        total_score = sector_score + cap_score + risk_score + geo_score + correlation_score

        return min(max(total_score, 0), 100)

    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation coefficient."""
        if correlation > 0.8:
            return "Very High Positive"
        elif correlation > 0.6:
            return "High Positive"
        elif correlation > 0.3:
            return "Moderate Positive"
        elif correlation > -0.3:
            return "Low/Neutral"
        elif correlation > -0.6:
            return "Moderate Negative"
        else:
            return "High Negative"

    def _interpret_portfolio_correlation(self, avg_correlation: float) -> str:
        """Interpret average portfolio correlation."""
        if avg_correlation > 0.7:
            return "High correlation - limited diversification benefit"
        elif avg_correlation > 0.5:
            return "Moderate correlation - some diversification benefit"
        elif avg_correlation > 0.3:
            return "Low correlation - good diversification benefit"
        else:
            return "Very low correlation - excellent diversification"

    def _assess_correlation_benefit(self, avg_correlation: float) -> str:
        """Assess the benefit from correlation levels."""
        if avg_correlation < 0.3:
            return "Excellent"
        elif avg_correlation < 0.5:
            return "Good"
        elif avg_correlation < 0.7:
            return "Moderate"
        else:
            return "Limited"

    def _interpret_diversification_score(self, score: float) -> str:
        """Interpret diversification score."""
        if score >= 80:
            return "Excellent diversification"
        elif score >= 60:
            return "Good diversification"
        elif score >= 40:
            return "Moderate diversification"
        elif score >= 20:
            return "Limited diversification"
        else:
            return "Poor diversification"

    def _analyze_exposure_risks(self, sector_percentages: Dict[str, float]) -> List[str]:
        """Analyze sector exposure risks."""
        risks = []

        for sector, percentage in sector_percentages.items():
            if percentage > 50:
                risks.append(f"High concentration in {sector} ({percentage:.1f}%)")
            elif percentage > 30:
                risks.append(f"Moderate concentration in {sector} ({percentage:.1f}%)")

        return risks

    def _analyze_performance_drivers(self, contributions: Dict[str, Any]) -> List[str]:
        """Analyze key performance drivers."""
        analysis = []

        # Find assets with significant positive/negative contributions
        for symbol, data in contributions.items():
            contribution = data["contribution_percent"]
            if contribution > 1.0:
                analysis.append(f"{symbol} was a strong positive contributor (+{contribution:.1f}%)")
            elif contribution < -1.0:
                analysis.append(f"{symbol} was a significant drag ({contribution:.1f}%)")

        return analysis

    def _interpret_efficiency_score(self, score: float) -> str:
        """Interpret portfolio efficiency score."""
        if score > 1.0:
            return "Highly efficient risk-return profile"
        elif score > 0.5:
            return "Good risk-return efficiency"
        elif score > 0:
            return "Moderate risk-return efficiency"
        else:
            return "Poor risk-return efficiency"

    def _calculate_overall_portfolio_score(
        self,
        diversification_results: Dict[str, Any],
        portfolio_risk: Dict[str, Any],
        efficiency_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall portfolio score."""

        # Component scores (0-100)
        diversification_score = diversification_results.get("diversification_score", 50)

        # Risk score (invert so lower risk = higher score)
        risk_score_raw = portfolio_risk.get("portfolio_risk_score", 3.0)
        risk_score = max(0, 100 - (risk_score_raw - 1) * 25)  # Scale 1-5 to 100-0

        # Efficiency score
        efficiency_raw = efficiency_analysis.get("portfolio_efficiency_score", 0.5)
        efficiency_score = min(100, max(0, efficiency_raw * 50 + 50))  # Scale to 0-100

        # Weighted overall score
        overall_score = (
            diversification_score * 0.4 +
            risk_score * 0.35 +
            efficiency_score * 0.25
        )

        return {
            "overall_score": overall_score,
            "component_scores": {
                "diversification": diversification_score,
                "risk_management": risk_score,
                "efficiency": efficiency_score
            },
            "score_interpretation": self._interpret_portfolio_score(overall_score)
        }

    def _interpret_portfolio_score(self, score: float) -> str:
        """Interpret overall portfolio score."""
        if score >= 80:
            return "Excellent portfolio construction"
        elif score >= 65:
            return "Good portfolio with minor improvements needed"
        elif score >= 50:
            return "Average portfolio with room for improvement"
        elif score >= 35:
            return "Below average portfolio needing attention"
        else:
            return "Poor portfolio requiring significant restructuring"

    def _generate_portfolio_recommendations(
        self,
        diversification_results: Dict[str, Any],
        portfolio_risk: Dict[str, Any],
        optimization_results: Dict[str, Any],
        rebalancing_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate portfolio recommendations."""
        recommendations = []

        # Diversification recommendations
        div_score = diversification_results.get("diversification_score", 50)
        if div_score < 60:
            recommendations.append("Consider adding assets from different sectors to improve diversification")

        concentrated_sectors = diversification_results.get("sector_analysis", {}).get("concentrated_sectors", [])
        if concentrated_sectors:
            recommendations.append(f"Reduce concentration in {', '.join(concentrated_sectors)} sectors")

        # Risk recommendations
        risk_level = portfolio_risk.get("portfolio_risk_level", "medium")
        concentration_risk = portfolio_risk.get("concentration_risk", "low")

        if concentration_risk == "high":
            recommendations.append("Reduce position concentration - no single position should exceed 25-30%")

        if risk_level == "very_high":
            recommendations.append("Portfolio risk is very high - consider reducing exposure to high-risk assets")

        # Rebalancing recommendations
        if rebalancing_analysis.get("rebalancing_needed", False):
            priority = rebalancing_analysis.get("rebalancing_priority", "medium")
            recommendations.append(f"Rebalancing recommended (Priority: {priority})")

        # Optimization recommendations
        target_risk = optimization_results.get("target_risk_level", "moderate")
        recommendations.append(f"Consider optimization for {target_risk} risk profile")

        return recommendations

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of stock symbols in the portfolio",
                    "minItems": 2
                },
                "analyses": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of individual stock analyses"
                },
                "correlation_analysis": {
                    "type": "boolean",
                    "description": "Whether to perform correlation analysis",
                    "default": True
                },
                "diversification_score": {
                    "type": "boolean",
                    "description": "Whether to calculate diversification metrics",
                    "default": True
                },
                "current_weights": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Current portfolio weights (optional)"
                },
                "target_risk": {
                    "type": "string",
                    "enum": ["conservative", "moderate", "aggressive"],
                    "description": "Target risk level for optimization",
                    "default": "moderate"
                }
            },
            "required": ["symbols", "analyses"]
        }

    async def health_check(self) -> bool:
        """Perform health check with sample data."""
        try:
            # Create sample portfolio data
            sample_symbols = ["AAPL", "MSFT"]
            sample_analyses = [
                {
                    "symbol": "AAPL",
                    "stock_data": {"current_price": 150, "sector": "Technology", "market_cap": 2.5e12},
                    "risk_assessment": {"risk_level": "medium", "risk_score": 2.5}
                },
                {
                    "symbol": "MSFT",
                    "stock_data": {"current_price": 300, "sector": "Technology", "market_cap": 2.2e12},
                    "risk_assessment": {"risk_level": "low", "risk_score": 2.0}
                }
            ]

            result = await self.execute(sample_symbols, sample_analyses)
            return "portfolio_summary" in result and "portfolio_score" in result

        except Exception as e:
            logger.error(f"Portfolio analyzer health check failed: {e}")
            return False
