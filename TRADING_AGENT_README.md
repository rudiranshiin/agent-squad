# 🤖 Advanced Trading Agent

A powerful, AI-driven trading agent built on the Agentic framework that provides comprehensive stock market analysis, risk assessment, and trading recommendations while maintaining the highest standards of risk management.

## 🎯 Key Features

### 📊 **Comprehensive Stock Analysis**
- **Real-time Market Data**: Fetches live stock prices, volume, and market metrics via Yahoo Finance API
- **Multi-timeframe Analysis**: Supports 1d, 5d, 1mo, 3mo analysis periods
- **Fundamental Metrics**: P/E ratios, market cap, revenue, earnings, and financial health indicators
- **52-week Analysis**: Position within trading range and momentum indicators

### 📈 **Advanced Technical Analysis**
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages (SMA/EMA), ATR, Stochastic
- **Volume Analysis**: Volume patterns, On-Balance Volume (OBV), volume confirmation signals
- **Support & Resistance**: Automatic identification of key price levels
- **Fibonacci Retracements**: Key retracement levels for entry/exit planning
- **Trend Analysis**: Strength and direction assessment with confidence scoring

### 📰 **News Sentiment Analysis**
- **Multi-source News Aggregation**: Collects news from various financial sources
- **Sentiment Scoring**: AI-powered sentiment analysis with confidence levels
- **Market Impact Assessment**: Identifies key market-moving events
- **Trend Analysis**: Tracks sentiment changes over time
- **Event Detection**: Automatically identifies earnings, mergers, regulatory events

### ⚠️ **Comprehensive Risk Management**
- **Volatility Analysis**: Historical and implied volatility calculations
- **Value at Risk (VaR)**: 95% and 99% confidence level risk metrics
- **Drawdown Analysis**: Maximum drawdown and recovery time estimation
- **Position Sizing**: Risk-based position sizing recommendations
- **Stress Testing**: Multiple scenario analysis (market crash, corrections, etc.)
- **Risk-adjusted Returns**: Sharpe, Sortino, and Calmar ratios

### 📊 **Portfolio Analysis & Optimization**
- **Correlation Analysis**: Inter-asset correlation matrices and diversification benefits
- **Sector Exposure**: Automatic sector classification and concentration analysis
- **Diversification Scoring**: Quantitative diversification assessment (0-100 scale)
- **Rebalancing Recommendations**: Optimal allocation suggestions with rebalancing triggers
- **Performance Attribution**: Individual asset contribution analysis

### 🎯 **Intelligent Trading Signals**
- **Multi-factor Signal Generation**: Combines technical, fundamental, and sentiment factors
- **Confidence Scoring**: Each signal includes strength and confidence metrics
- **Risk-adjusted Recommendations**: Signals adjusted for asset risk levels
- **Entry/Exit Points**: Specific price targets and stop-loss recommendations
- **Signal Aggregation**: Combines multiple indicators for robust recommendations

## 🏗️ Architecture

### Core Components

```
Trading Agent
├── Stock Data Retrieval (Yahoo Finance)
├── Technical Analysis Engine
├── News Sentiment Analyzer
├── Risk Assessment Engine
├── Trading Signals Generator
├── Portfolio Analyzer
└── Symbol Extractor
```

### Tool Ecosystem

1. **YahooFinanceTool**: Real-time market data retrieval
2. **TechnicalIndicatorsTool**: Comprehensive technical analysis
3. **NewsSentimentTool**: AI-powered news sentiment analysis
4. **RiskAnalyzerTool**: Multi-dimensional risk assessment
5. **TradingSignalsTool**: Intelligent signal generation
6. **PortfolioAnalyzerTool**: Portfolio optimization and analysis
7. **SymbolExtractorTool**: Natural language symbol extraction

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd /path/to/Agentic

# Install dependencies
source venv/bin/activate
pip install --index-url https://pypi.org/simple/ yfinance textblob pandas numpy aiohttp

# Optional: Set API keys for enhanced functionality
export ALPHA_VANTAGE_API_KEY="your_api_key"  # For news sentiment
export OPENAI_API_KEY="your_openai_key"      # For LLM analysis
```

### 2. Basic Usage

```python
from agents.implementations.trading_agent import TradingAgent

# Initialize the trading agent
agent = TradingAgent("agents/configs/trading_agent.yaml")

# Analyze a stock
response = await agent.process_message(
    "Analyze AAPL for potential investment opportunities"
)

print(response["response"])
```

### 3. Test the Agent

```bash
# Run comprehensive test suite
python test_trading_agent.py
```

## 📋 Usage Examples

### Single Stock Analysis
```python
# Comprehensive stock analysis
query = "Analyze TSLA stock. What are the technical indicators saying?"
response = await agent.process_message(query)

# Response includes:
# - Current price and market data
# - Technical indicator readings
# - News sentiment analysis
# - Risk assessment
# - Trading recommendations
```

### Multi-Stock Comparison
```python
# Compare multiple stocks
query = "Compare MSFT and GOOGL for my portfolio. Which has better risk-adjusted returns?"
response = await agent.process_message(query)

# Response includes:
# - Side-by-side comparison
# - Risk-return analysis
# - Portfolio fit assessment
# - Diversification impact
```

### Risk Assessment
```python
# Position sizing and risk analysis
query = "I want to invest $10,000 in NVDA. What's the appropriate position size?"
response = await agent.process_message(query)

# Response includes:
# - Risk level assessment
# - Position sizing recommendations
# - Stop-loss suggestions
# - Risk management advice
```

### Portfolio Analysis
```python
# Portfolio diversification analysis
query = "Analyze my portfolio with AAPL, MSFT, and TSLA. How's the diversification?"
response = await agent.process_message(query)

# Response includes:
# - Diversification score
# - Correlation analysis
# - Sector concentration
# - Rebalancing recommendations
```

## ⚙️ Configuration

### Risk Tolerance Settings
```yaml
risk_tolerance: "moderate"  # Options: conservative, moderate, aggressive

advanced_settings:
  max_position_size_pct: 10.0    # Maximum 10% per position
  stop_loss_default_pct: 8.0     # Default 8% stop loss
  risk_reward_ratio: 2.0         # Minimum 2:1 risk/reward
```

### Analysis Parameters
```yaml
analysis_timeframes:
  - "1d"    # Intraday analysis
  - "5d"    # Short-term analysis
  - "1mo"   # Medium-term analysis
  - "3mo"   # Longer-term context

confidence_threshold: 0.6  # Minimum confidence for signals
```

## 🔧 Advanced Features

### Custom Risk Parameters
- Adjustable risk tolerance levels
- Custom position sizing rules
- Configurable stop-loss percentages
- Risk-reward ratio requirements

### Multi-timeframe Analysis
- Intraday (1d) for short-term trading
- Short-term (5d) for swing trading
- Medium-term (1mo) for position trading
- Long-term (3mo+) for investment analysis

### Intelligent Symbol Extraction
- Natural language processing for symbol identification
- Company name to ticker mapping
- Context-aware symbol validation
- False positive filtering

### Comprehensive Error Handling
- Graceful degradation when APIs are unavailable
- Fallback data sources
- Detailed error reporting
- Confidence adjustment based on data quality

## 📊 Sample Analysis Output

```
**Market Overview:**
Apple Inc. (AAPL) is currently trading at $232.14 (-0.18%), showing consolidation
near key resistance levels. The stock demonstrates moderate volatility with strong
fundamental metrics.

**Technical Analysis:**
- RSI (14): 52.3 - Neutral territory, room for movement in either direction
- MACD: Bullish crossover with strengthening momentum
- Bollinger Bands: Price in middle region, approaching upper band
- Volume: Above average, confirming current price action

**Risk Assessment:**
- Risk Level: Medium (Score: 2.8/5.0)
- Recommended Position Size: 8% of portfolio
- Stop Loss: $213.57 (8% below current price)
- Target Price: $251.23 (2:1 risk-reward ratio)

**Trading Recommendation:**
Moderate Buy signal with 73% confidence. Technical indicators suggest bullish
momentum with manageable risk levels. Consider entry on any pullback to $225-228
support zone.

**Important Disclaimer:**
This analysis is for educational purposes only. Please conduct your own research
and consult with qualified financial advisors before making investment decisions.
```

## 🛡️ Risk Management & Disclaimers

### Built-in Safety Features
- **Automatic Risk Warnings**: Highlights high-risk assets and market conditions
- **Position Size Limits**: Prevents over-concentration in single positions
- **Stop-Loss Recommendations**: Automatic stop-loss calculations for risk management
- **Diversification Alerts**: Warns about sector concentration and correlation risks

### Important Disclaimers
- ⚠️ **Educational Purpose Only**: All analysis is for educational and informational purposes
- 📊 **Not Financial Advice**: Recommendations are not personalized financial advice
- 🔍 **Do Your Research**: Always conduct independent research and due diligence
- 👨‍💼 **Consult Professionals**: Seek advice from qualified financial advisors
- 📉 **Market Risks**: All investments carry risk of loss, past performance doesn't guarantee future results

## 🔮 Future Enhancements

### Planned Features
- **Real-time Alerts**: Price and technical indicator alerts
- **Backtesting Engine**: Historical strategy performance testing
- **Options Analysis**: Options pricing and Greeks analysis
- **Crypto Support**: Cryptocurrency market analysis
- **Chart Integration**: Visual chart analysis and pattern recognition
- **Portfolio Tracking**: Real-time portfolio performance monitoring

### API Integrations
- **Alpha Vantage**: Enhanced news and fundamental data
- **Polygon.io**: Real-time market data and options
- **Financial Modeling Prep**: Comprehensive financial statements
- **News APIs**: Expanded news source coverage

## 🤝 Contributing

The trading agent is built on a modular architecture that makes it easy to extend:

1. **Add New Indicators**: Extend `TechnicalIndicatorsTool` with additional indicators
2. **Enhance Risk Models**: Add new risk metrics to `RiskAnalyzerTool`
3. **Improve Sentiment**: Enhance news sources in `NewsSentimentTool`
4. **Custom Signals**: Create new signal generation strategies

## 📞 Support

For questions, issues, or contributions:
- Review the test suite in `test_trading_agent.py` for usage examples
- Check the configuration file `agents/configs/trading_agent.yaml` for customization options
- Examine individual tool implementations in `tools/financial/` for technical details

---

**⚠️ Final Disclaimer**: This trading agent is a sophisticated analysis tool designed for educational purposes. It provides data-driven insights to support investment research but should never be used as the sole basis for trading decisions. Always practice proper risk management, diversify your investments, and never invest more than you can afford to lose. The creators assume no responsibility for trading losses or investment decisions made based on this tool's output.
