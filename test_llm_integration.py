#!/usr/bin/env python3
"""
Test script for LLM integration with the Agentic framework.
This script tests the LLM client and agent integration.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from framework.core.llm_client import get_llm_client, LLMMessage, reset_llm_client
from framework.core.agent_registry import AgentRegistry

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_llm_client():
    """Test the LLM client directly."""
    print("=== Testing LLM Client ===")

    # Reset client to ensure fresh initialization
    reset_llm_client()

    # Test client initialization
    llm_client = get_llm_client()
    available_providers = llm_client.get_available_providers()

    if not available_providers:
        print("❌ No LLM providers available!")
        print("Please set up API keys in environment variables:")
        print("  - OPENAI_API_KEY or OPENAI_ENGINEERING_SANDBOX_APIKEY")
        print("  - ANTHROPIC_API_KEY or ANTHROPIC_ENGINEERING_SANDBOX_APIKEY")
        return False

    print(f"✅ Available providers: {available_providers}")

    # Test each provider
    for provider in available_providers:
        print(f"\n--- Testing {provider} ---")

        try:
            # Test connection
            connection_test = await llm_client.test_connection(provider)
            if connection_test["success"]:
                print(f"✅ {provider} connection successful!")
                print(f"   Model: {connection_test['model']}")
                print(f"   Response: {connection_test['response'][:50]}...")
                print(f"   Tokens used: {connection_test['tokens_used']}")
            else:
                print(f"❌ {provider} connection failed: {connection_test['error']}")

        except Exception as e:
            print(f"❌ {provider} test error: {e}")

    print("\n--- Testing Message Generation ---")
    try:
        # Test simple message
        response = await llm_client.generate_response(
            "Hello! Please respond with exactly: 'LLM integration successful!'",
            max_tokens=50,
            temperature=0.1
        )
        print(f"✅ Simple message test successful!")
        print(f"   Response: {response.content}")
        print(f"   Provider: {response.metadata.get('provider')}")
        print(f"   Tokens: {response.tokens_used}")

    except Exception as e:
        print(f"❌ Message generation failed: {e}")
        return False

    return True


async def test_agent_integration():
    """Test LLM integration with agents."""
    print("\n=== Testing Agent Integration ===")

    try:
        # Initialize agent registry
        registry = AgentRegistry()

        # Load agents
        config_dir = project_root / "agents" / "configs"
        agents_to_test = [
            ("british_teacher.yaml", "Professor James"),
            ("weather_agent.yaml", "Weather Assistant")
        ]

        for config_file, expected_name in agents_to_test:
            config_path = config_dir / config_file
            if not config_path.exists():
                print(f"❌ Config file not found: {config_path}")
                continue

            print(f"\n--- Testing {config_file} ---")

            try:
                # Load agent
                agent = registry.load_agent(str(config_path))
                print(f"✅ Agent loaded: {agent.name}")

                # Test health check
                health_response = await agent.process_message(
                    "Hello!",
                    context={"internal_health_check": True}
                )

                if health_response.get("success"):
                    print(f"✅ Health check passed: {health_response['response']}")
                else:
                    print(f"❌ Health check failed: {health_response.get('error')}")
                    continue

                # Test actual LLM response
                test_message = "Hello! Can you introduce yourself briefly?"

                print(f"   Sending test message: '{test_message}'")
                response = await agent.process_message(test_message)

                if response.get("success"):
                    print(f"✅ LLM response successful!")
                    print(f"   Response: {response['response'][:100]}...")
                    print(f"   Processing time: {response.get('processing_time', 0):.2f}s")

                    # Check if LLM was used
                    context_summary = response.get("context_summary", {})
                    tool_contexts = context_summary.get("tool_contexts", [])
                    llm_used = any("llm_client" in str(ctx) for ctx in tool_contexts)

                    if llm_used:
                        print(f"✅ LLM client was used successfully")
                    else:
                        print(f"⚠️  LLM client may not have been used (check fallback)")

                else:
                    print(f"❌ Agent response failed: {response.get('error')}")

            except Exception as e:
                print(f"❌ Error testing agent {config_file}: {e}")

        return True

    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False


async def test_specific_scenarios():
    """Test specific agent scenarios."""
    print("\n=== Testing Specific Scenarios ===")

    try:
        registry = AgentRegistry()

        # Test language teacher
        print("\n--- Language Teacher Scenario ---")
        config_path = project_root / "agents" / "configs" / "british_teacher.yaml"
        if config_path.exists():
            agent = registry.load_agent(str(config_path))

            response = await agent.process_message(
                "I want to learn about British idioms. Can you teach me some common ones?"
            )

            if response.get("success"):
                print(f"✅ Language teaching response:")
                print(f"   {response['response'][:200]}...")
            else:
                print(f"❌ Language teaching failed: {response.get('error')}")

        # Test weather agent
        print("\n--- Weather Agent Scenario ---")
        config_path = project_root / "agents" / "configs" / "weather_agent.yaml"
        if config_path.exists():
            agent = registry.load_agent(str(config_path))

            response = await agent.process_message(
                "What should I wear today if it's 15°C and cloudy?"
            )

            if response.get("success"):
                print(f"✅ Weather response:")
                print(f"   {response['response'][:200]}...")
            else:
                print(f"❌ Weather response failed: {response.get('error')}")

        return True

    except Exception as e:
        print(f"❌ Specific scenarios test failed: {e}")
        return False


def check_environment():
    """Check if required environment variables are set."""
    print("=== Environment Check ===")

    # Check for API keys
    openai_keys = ["OPENAI_API_KEY", "OPENAI_ENGINEERING_SANDBOX_APIKEY"]
    anthropic_keys = ["ANTHROPIC_API_KEY", "ANTHROPIC_ENGINEERING_SANDBOX_APIKEY"]

    openai_available = any(os.getenv(key) for key in openai_keys)
    anthropic_available = any(os.getenv(key) for key in anthropic_keys)

    if openai_available:
        print("✅ OpenAI API key found")
    else:
        print("❌ No OpenAI API key found")
        print(f"   Set one of: {', '.join(openai_keys)}")

    if anthropic_available:
        print("✅ Anthropic API key found")
    else:
        print("❌ No Anthropic API key found")
        print(f"   Set one of: {', '.join(anthropic_keys)}")

    if not openai_available and not anthropic_available:
        print("\n⚠️  No API keys found! Please set up at least one LLM provider.")
        print("For testing, you can use:")
        print("  export OPENAI_API_KEY='your-openai-key'")
        print("  export ANTHROPIC_API_KEY='your-anthropic-key'")
        return False

    return True


async def main():
    """Run all tests."""
    print("🚀 Starting LLM Integration Tests")
    print("=" * 50)

    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please set up API keys.")
        return

    # Run tests
    tests = [
        ("LLM Client", test_llm_client),
        ("Agent Integration", test_agent_integration),
        ("Specific Scenarios", test_specific_scenarios)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*50)
    print("🎯 Test Results Summary")
    print("="*50)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! LLM integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
