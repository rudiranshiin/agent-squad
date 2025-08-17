"""
LLM Client for integrating with various Language Learning Models.
Supports OpenAI and Anthropic APIs using HubSpot sandbox keys.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio
import json
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Manual .env loading fallback
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    try:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value.strip('"\'')
                    except ValueError:
                        pass

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

            # Make API call (synchronous - OpenAI client handles async internally)
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


class LLMClient:
    """
    Main LLM client that manages multiple providers and handles fallbacks.
    """

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
                logger.info("OpenAI provider initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI provider: {e}")

        # Anthropic setup
        anthropic_key = self._get_api_key("anthropic")
        if anthropic_key:
            try:
                anthropic_model = self.config.get("anthropic_model", "claude-3-5-sonnet-latest")
                self.providers["anthropic"] = AnthropicProvider(anthropic_key, anthropic_model)
                if not self.default_provider:
                    self.default_provider = "anthropic"
                logger.info("Anthropic provider initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic provider: {e}")

        if not self.providers:
            logger.warning("No LLM providers available. Check API key configuration.")

    def _get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for provider from environment or config.

        Priority:
        1. Environment variables
        2. Config file
        3. HubSpot sandbox keys (simulated)
        """

        # Environment variables
        env_keys = {
            "openai": ["OPENAI_API_KEY", "OPENAI_ENGINEERING_SANDBOX_APIKEY"],
            "anthropic": ["ANTHROPIC_API_KEY", "ANTHROPIC_ENGINEERING_SANDBOX_APIKEY"]
        }

        for env_var in env_keys.get(provider, []):
            key = os.getenv(env_var)
            if key:
                logger.info(f"Using {provider} API key from environment: {env_var}")
                return key

        # Config file
        config_key = self.config.get(f"{provider}_api_key")
        if config_key:
            logger.info(f"Using {provider} API key from config")
            return config_key

        # For HubSpot integration, you would implement vault key retrieval here
        # Example:
        # if self.config.get("use_hubspot_vault", False):
        #     return self._get_vault_key(provider)

        logger.warning(f"No API key found for {provider}")
        return None

    def _get_vault_key(self, provider: str) -> Optional[str]:
        """
        Get API key from HubSpot Vault (placeholder implementation).

        In a real HubSpot environment, this would use the Vault client:

        from vault_client import VaultClient
        vault_client = VaultClient("hs-engineering")

        vault_keys = {
            "openai": "openai.engineering.sandbox.apikey",
            "anthropic": "anthropic.engineering.sandbox.apikey"
        }

        vault_key = vault_keys.get(provider)
        if vault_key:
            return vault_client.get_secret(vault_key)
        """
        logger.info(f"Vault key retrieval for {provider} not implemented in this environment")
        return None

    async def generate_response(
        self,
        messages: Union[List[LLMMessage], str],
        provider: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response using specified or default provider.

        Args:
            messages: List of LLMMessage objects or a simple string
            provider: Specific provider to use ("openai", "anthropic")
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse object
        """

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
            logger.warning(f"Requested provider not available, using: {provider}")

        # Generate response
        try:
            response = await self.providers[provider].generate_response(
                messages, max_tokens, temperature, **kwargs
            )
            logger.debug(f"Generated response using {provider}: {len(response.content)} chars")
            return response

        except Exception as e:
            logger.error(f"Error with provider {provider}: {e}")

            # Try fallback provider
            fallback_providers = [p for p in self.providers.keys() if p != provider]
            if fallback_providers:
                fallback = fallback_providers[0]
                logger.info(f"Attempting fallback to {fallback}")
                try:
                    return await self.providers[fallback].generate_response(
                        messages, max_tokens, temperature, **kwargs
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback provider {fallback} also failed: {fallback_error}")

            raise e

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.providers.keys())

    def get_provider_info(self, provider: str = None) -> Dict[str, Any]:
        """Get information about a provider."""
        provider = provider or self.default_provider
        if provider not in self.providers:
            return {}

        provider_obj = self.providers[provider]
        return {
            "provider": provider,
            "model": provider_obj.model,
            "available": True
        }

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


# Global LLM client instance
_llm_client = None


def get_llm_client(config: Dict[str, Any] = None) -> LLMClient:
    """Get or create global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(config)
    return _llm_client


def reset_llm_client():
    """Reset global LLM client (useful for testing or config changes)."""
    global _llm_client
    _llm_client = None
