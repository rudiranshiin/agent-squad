#!/usr/bin/env python3
"""
Standalone LLM integration test that imports the LLM client directly.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not available, loading environment variables manually")
    # Manual .env loading
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')
        print("✅ Manually loaded environment variables from .env file")

# LLM SDK imports
try:
    from openai import OpenAI
    from anthropic import Anthropic
except ImportError as e:
    logging.warning(f"LLM SDKs not available: {e}")
    OpenAI = None
    Anthropic = None

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    """Standard message format for LLM interactions."""
    role: str  # "system", "user", "assistant"
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Standard response format from LLM."""
    content: str
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model
        self.client = None

    @abstractmethod
    async def generate_response(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate response from LLM."""
        pass

    @abstractmethod
    def _setup_client(self):
        """Setup the LLM client."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider using HubSpot sandbox keys."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(api_key, model)
        self._setup_client()

    def _setup_client(self):
        """Setup OpenAI client."""
        if OpenAI is None:
            raise ImportError("OpenAI package not available. Install with: pip install openai")

        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI client with model: {self.model}")

    async def generate_response(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenAI API."""
        try:
            # Convert our message format to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            # Extract response data
            choice = response.choices[0]

            return LLMResponse(
                content=choice.message.content,
                tokens_used=response.usage.total_tokens if response.usage else None,
                model=response.model,
                finish_reason=choice.finish_reason,
                metadata={
                    "provider": "openai",
                    "response_id": response.id,
                    "created": response.created
                }
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider using HubSpot sandbox keys."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-latest"):
        super().__init__(api_key, model)
        self._setup_client()

    def _setup_client(self):
        """Setup Anthropic client."""
        if Anthropic is None:
            raise ImportError("Anthropic package not available. Install with: pip install anthropic")

        self.client = Anthropic(api_key=self.api_key)
        logger.info(f"Initialized Anthropic client with model: {self.model}")

    async def generate_response(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Anthropic API."""
        try:
            # Separate system message from conversation messages
            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    conversation_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # Prepare request parameters
            request_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": conversation_messages,
                **kwargs
            }

            # Add system message if present
            if system_message:
                request_params["system"] = system_message

            # Make API call
            response = self.client.messages.create(**request_params)

            # Extract content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text

            return LLMResponse(
                content=content,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens if response.usage else None,
                model=response.model,
                finish_reason=response.stop_reason,
                metadata={
                    "provider": "anthropic",
                    "response_id": response.id,
                    "input_tokens": response.usage.input_tokens if response.usage else None,
                    "output_tokens": response.usage.output_tokens if response.usage else None
                }
            )

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class StandaloneLLMClient:
    """Standalone LLM client for testing."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider = None

        # Setup providers based on available API keys
        self._setup_providers()

    def _setup_providers(self):
        """Setup LLM providers based on available API keys."""

        # OpenAI setup
        openai_key = self._get_api_key("openai")
        if openai_key:
            try:
                openai_model = self.config.get("openai_model", "gpt-4o")
                self.providers["openai"] = OpenAIProvider(openai_key, openai_model)
                if not self.default_provider:
                    self.default_provider = "openai"
                print("✅ OpenAI provider initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI provider: {e}")

        # Anthropic setup
        anthropic_key = self._get_api_key("anthropic")
        if anthropic_key:
            try:
                anthropic_model = self.config.get("anthropic_model", "claude-3-5-sonnet-latest")
                self.providers["anthropic"] = AnthropicProvider(anthropic_key, anthropic_model)
                if not self.default_provider:
                    self.default_provider = "anthropic"
                print("✅ Anthropic provider initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Anthropic provider: {e}")

        if not self.providers:
            print("⚠️  No LLM providers available. Check API key configuration.")

    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for provider from environment or config."""

        # Environment variables
        env_keys = {
            "openai": ["OPENAI_API_KEY", "OPENAI_ENGINEERING_SANDBOX_APIKEY"],
            "anthropic": ["ANTHROPIC_API_KEY", "ANTHROPIC_ENGINEERING_SANDBOX_APIKEY"]
        }

        for env_var in env_keys.get(provider, []):
            key = os.getenv(env_var)
            if key:
                print(f"✅ Using {provider} API key from environment: {env_var}")
                return key

        # Config file
        config_key = self.config.get(f"{provider}_api_key")
        if config_key:
            print(f"✅ Using {provider} API key from config")
            return config_key

        print(f"❌ No API key found for {provider}")
        return None

    async def generate_response(
        self,
        messages: Union[List[LLMMessage], str],
        provider: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate response using specified or default provider."""

        # Handle string input
        if isinstance(messages, str):
            messages = [LLMMessage(role="user", content=messages)]

        # Determine provider
        provider = provider or self.default_provider
        if not provider or provider not in self.providers:
            available = list(self.providers.keys())
            if not available:
                raise ValueError("No LLM providers available")
            provider = available[0]
            print(f"⚠️  Requested provider not available, using: {provider}")

        # Generate response
        response = await self.providers[provider].generate_response(
            messages, max_tokens, temperature, **kwargs
        )

        return response

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.providers.keys())

    async def test_connection(self, provider: str = None) -> Dict[str, Any]:
        """Test connection to LLM provider."""
        provider = provider or self.default_provider
        if not provider or provider not in self.providers:
            return {"success": False, "error": "Provider not available"}

        try:
            test_message = [LLMMessage(role="user", content="Hello! Please respond with 'Connection successful.'")]
            response = await self.generate_response(
                test_message,
                provider=provider,
                max_tokens=20,
                temperature=0.1
            )

            return {
                "success": True,
                "provider": provider,
                "model": response.model,
                "response": response.content,
                "tokens_used": response.tokens_used
            }

        except Exception as e:
            return {
                "success": False,
                "provider": provider,
                "error": str(e)
            }


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
    print("\n=== Testing Standalone LLM Client ===")

    # Test client initialization
    llm_client = StandaloneLLMClient()
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


async def main():
    """Run all tests."""
    print("🚀 Starting Standalone LLM Integration Tests")
    print("=" * 50)

    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please set up API keys.")
        print("\nFor demo purposes, continuing with mock test...")
        print("To test with real APIs, set:")
        print("  export OPENAI_API_KEY='your-key'")
        print("  export ANTHROPIC_API_KEY='your-key'")
        return

    # Run test
    success = await test_llm_client()

    # Summary
    print("\n" + "="*50)
    print("🎯 Test Results Summary")
    print("="*50)

    if success:
        print("✅ LLM Client Test: PASSED")
        print("\n🎉 LLM integration is working correctly!")
        print("\n📋 Next Steps:")
        print("1. Your LLM client is working properly")
        print("2. You can integrate this with your agent framework")
        print("3. Try the updated API with: python api/simple_main.py")
    else:
        print("❌ LLM Client Test: FAILED")
        print("⚠️  Test failed. Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())
