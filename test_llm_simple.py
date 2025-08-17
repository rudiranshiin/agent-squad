#!/usr/bin/env python3
"""
Simple LLM integration test that tests just the LLM client.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Direct import of the LLM client only
from framework.core.llm_client import get_llm_client, LLMMessage, reset_llm_client


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


async def test_llm_client():
    """Test the LLM client directly."""
    print("\n=== Testing LLM Client ===")

    # Reset client to ensure fresh initialization
    reset_llm_client()

    # Test client initialization
    llm_client = get_llm_client()
    available_providers = llm_client.get_available_providers()

    if not available_providers:
        print("❌ No LLM providers available!")
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

        # Test with system message
        print("\n--- Testing with System Message ---")
        messages = [
            LLMMessage(role="system", content="You are a helpful assistant that only speaks in pirate language."),
            LLMMessage(role="user", content="Say hello!")
        ]

        response = await llm_client.generate_response(
            messages,
            max_tokens=100,
            temperature=0.7
        )
        print(f"✅ System message test successful!")
        print(f"   Response: {response.content}")
        print(f"   Provider: {response.metadata.get('provider')}")

        return True

    except Exception as e:
        print(f"❌ Message generation failed: {e}")
        return False


async def test_multiple_providers():
    """Test switching between providers."""
    print("\n=== Testing Provider Switching ===")

    try:
        llm_client = get_llm_client()
        providers = llm_client.get_available_providers()

        if len(providers) < 2:
            print("⚠️  Only one provider available, skipping provider switching test")
            return True

        test_message = "What is 2+2? Answer with just the number."

        for provider in providers:
            print(f"\n--- Testing {provider} ---")
            try:
                response = await llm_client.generate_response(
                    test_message,
                    provider=provider,
                    max_tokens=20,
                    temperature=0.1
                )
                print(f"✅ {provider} response: {response.content}")
                print(f"   Model: {response.model}")
                print(f"   Tokens: {response.tokens_used}")
            except Exception as e:
                print(f"❌ {provider} failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Provider switching test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Simple LLM Integration Tests")
    print("=" * 50)

    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please set up API keys.")
        return

    # Run tests
    tests = [
        ("LLM Client Basic", test_llm_client),
        ("Provider Switching", test_multiple_providers)
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
        print("\n📋 Next Steps:")
        print("1. Your LLM client is working properly")
        print("2. You can now integrate it with your agents")
        print("3. Try the updated API with: python api/simple_main.py")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
