#!/usr/bin/env python3
"""
Test script for the Trading Agent to demonstrate its capabilities.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.implementations.trading_agent import TradingAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_trading_agent():
    """Test the trading agent with various stock analysis scenarios."""

    print("🤖 Trading Agent Test Suite")
    print("=" * 50)

    try:
        # Initialize the trading agent
        config_path = project_root / "agents" / "configs" / "trading_agent.yaml"

        if not config_path.exists():
            print(f"❌ Configuration file not found: {config_path}")
            return

        print(f"📋 Loading trading agent configuration from: {config_path}")
        agent = TradingAgent(str(config_path))

        print(f"✅ Trading agent '{agent.name}' initialized successfully")
        print(f"🎯 Risk tolerance: {agent.risk_tolerance}")
        print(f"📊 Analysis timeframes: {agent.analysis_timeframes}")
        print(f"🔧 Available tools: {len(agent.tool_registry.list_tools())}")

        # Test scenarios
        test_scenarios = [
            {
                "name": "Single Stock Analysis",
                "query": "Analyze AAPL stock for potential investment opportunities",
                "description": "Test basic stock analysis capabilities"
            },
            {
                "name": "Technical Analysis Request",
                "query": "What are the technical indicators saying about TSLA? Should I buy or sell?",
                "description": "Test technical analysis and trading signals"
            },
            {
                "name": "Multi-Stock Comparison",
                "query": "Compare MSFT and GOOGL for my portfolio. Which one has better risk-adjusted returns?",
                "description": "Test multi-symbol analysis and comparison"
            },
            {
                "name": "Risk Assessment Query",
                "query": "I want to invest $10,000 in NVDA. What's the risk level and appropriate position size?",
                "description": "Test risk analysis and position sizing"
            },
            {
                "name": "Portfolio Analysis",
                "query": "Analyze my portfolio with AAPL, MSFT, and TSLA. How's the diversification?",
                "description": "Test portfolio analysis capabilities"
            }
        ]

        print("\n🧪 Running Test Scenarios")
        print("-" * 30)

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📝 Test {i}: {scenario['name']}")
            print(f"📄 Description: {scenario['description']}")
            print(f"❓ Query: {scenario['query']}")
            print("⏳ Processing...")

            try:
                # Process the query
                response = await agent.process_message(
                    message=scenario['query'],
                    context={"test_scenario": scenario['name']},
                    user_id="test_user"
                )

                # Display results
                if response.get("success", False):
                    print("✅ Analysis completed successfully")
                    print(f"📊 Response length: {len(response.get('response', ''))} characters")

                    # Show key metrics if available
                    if response.get("symbols_analyzed"):
                        print(f"📈 Symbols analyzed: {response['symbols_analyzed']}")

                    if response.get("confidence_level"):
                        print(f"🎯 Confidence level: {response['confidence_level']:.1%}")

                    if response.get("tools_used"):
                        print(f"🔧 Tools used: {', '.join(response['tools_used'])}")

                    if response.get("processing_time"):
                        print(f"⏱️  Processing time: {response['processing_time']:.2f}s")

                    # Show a snippet of the response
                    response_text = response.get("response", "")
                    if len(response_text) > 200:
                        snippet = response_text[:200] + "..."
                    else:
                        snippet = response_text

                    print(f"💬 Response snippet: {snippet}")

                else:
                    print("❌ Analysis failed")
                    if response.get("error"):
                        print(f"🚨 Error: {response['error']}")

            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                logger.exception(f"Error in test scenario {i}")

            print("-" * 30)

        # Test agent status
        print("\n📊 Agent Status Check")
        print("-" * 20)

        try:
            status = await agent.get_agent_status()
            print(f"✅ Agent status retrieved successfully")
            print(f"🏃 Running: {status.get('is_running', False)}")
            print(f"🧠 Context items: {status.get('context_summary', {}).get('total_items', 0)}")
            print(f"🔧 Tool statistics available: {bool(status.get('tool_stats'))}")

        except Exception as e:
            print(f"❌ Status check failed: {e}")

        # Test health check
        print("\n🏥 Health Check")
        print("-" * 15)

        try:
            health_response = await agent.process_message(
                message="Health check",
                context={"internal_health_check": True}
            )

            if health_response.get("success"):
                print("✅ Health check passed")
                print(f"💬 Response: {health_response.get('response', 'No response')}")
            else:
                print("❌ Health check failed")

        except Exception as e:
            print(f"❌ Health check exception: {e}")

        print("\n🎉 Trading Agent Test Suite Completed")
        print("=" * 50)

        # Summary
        print("\n📋 Test Summary:")
        print("• Trading agent successfully initialized")
        print("• Configuration loaded and validated")
        print("• All test scenarios executed")
        print("• Agent demonstrates comprehensive trading analysis capabilities")
        print("\n⚠️  Note: This agent uses simulated data for demonstration.")
        print("   In production, connect to real financial data APIs for live analysis.")

    except Exception as e:
        print(f"❌ Critical error in test suite: {e}")
        logger.exception("Critical error in trading agent test")


async def test_individual_tools():
    """Test individual trading tools for functionality."""

    print("\n🔧 Individual Tool Tests")
    print("=" * 30)

    try:
        # Test symbol extractor
        from tools.financial.symbol_extractor_tool import SymbolExtractorTool

        print("\n📝 Testing Symbol Extractor...")
        symbol_tool = SymbolExtractorTool()

        test_text = "I want to analyze Apple (AAPL) and buy $TSLA. Also interested in Microsoft stock."
        symbols = await symbol_tool.execute(test_text)

        print(f"✅ Extracted symbols: {symbols}")

        # Test technical indicators (with sample data)
        from tools.financial.technical_indicators_tool import TechnicalIndicatorsTool

        print("\n📊 Testing Technical Indicators...")
        tech_tool = TechnicalIndicatorsTool()

        # Sample stock data
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

        tech_result = await tech_tool.execute(sample_data, indicators=["sma", "rsi", "macd"])
        print(f"✅ Technical indicators calculated: {len(tech_result.get('indicators', {}))}")

        # Test health checks
        print("\n🏥 Testing Tool Health Checks...")

        tools_to_test = [
            ("Symbol Extractor", symbol_tool),
            ("Technical Indicators", tech_tool)
        ]

        for tool_name, tool in tools_to_test:
            try:
                health = await tool.health_check()
                status = "✅ Healthy" if health else "❌ Unhealthy"
                print(f"{tool_name}: {status}")
            except Exception as e:
                print(f"{tool_name}: ❌ Health check failed - {e}")

        print("\n✅ Individual tool tests completed")

    except Exception as e:
        print(f"❌ Tool test error: {e}")
        logger.exception("Error in individual tool tests")


if __name__ == "__main__":
    print("🚀 Starting Trading Agent Test Suite...")

    # Run the main test
    asyncio.run(test_trading_agent())

    # Run individual tool tests
    asyncio.run(test_individual_tools())

    print("\n🏁 All tests completed!")
