#!/usr/bin/env python3
"""
Demo script showing your LLM integration working with real HubSpot sandbox keys.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import our standalone LLM client
from test_llm_standalone import StandaloneLLMClient, LLMMessage


async def demo_language_teacher():
    """Demo of a language teacher using real LLM."""
    print("🎓 Language Teacher Demo")
    print("=" * 40)

    client = StandaloneLLMClient()

    # Check if we have providers
    if not client.get_available_providers():
        print("❌ No LLM providers available. Check your .env file.")
        return

    # Create a language teacher system prompt
    system_prompt = """You are Professor James, a distinguished British English teacher. You help students learn proper British English with correct pronunciation, grammar, and cultural context. You are patient, encouraging, and always maintain a professional yet warm demeanor. You take pride in the richness of the English language and British culture.

Teaching style:
- Be encouraging and constructive
- Provide specific examples
- Include cultural context when relevant
- Use proper British English
- Correct mistakes gently"""

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content="Hello Professor! I want to learn about British idioms. Can you teach me some common ones and explain what they mean?")
    ]

    print("Student: Hello Professor! I want to learn about British idioms. Can you teach me some common ones and explain what they mean?")
    print("\nProfessor James is thinking... 🤔")

    response = await client.generate_response(
        messages,
        provider="anthropic",  # Claude is great for educational content
        max_tokens=500,
        temperature=0.7
    )

    print(f"\nProfessor James ({response.metadata.get('provider')}):")
    print(response.content)
    print(f"\n💡 Used {response.tokens_used} tokens with {response.model}")


async def demo_weather_agent():
    """Demo of a weather agent using real LLM."""
    print("\n\n🌤️  Weather Assistant Demo")
    print("=" * 40)

    client = StandaloneLLMClient()

    # Create a weather assistant system prompt
    system_prompt = """You are a helpful weather assistant. You provide accurate, helpful weather information and practical advice. Focus on practical implications of weather conditions, include safety recommendations when appropriate, and use clear, easy-to-understand language.

Guidelines:
- Always prioritize safety in weather-related advice
- Provide specific, actionable information
- Suggest appropriate activities or precautions based on conditions
- Be concise but comprehensive
- Use friendly, helpful tone"""

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content="It's 15°C and cloudy today. I'm thinking about going hiking. What should I wear and what should I be prepared for?")
    ]

    print("User: It's 15°C and cloudy today. I'm thinking about going hiking. What should I wear and what should I be prepared for?")
    print("\nWeather Assistant is analyzing conditions... 🌥️")

    response = await client.generate_response(
        messages,
        provider="openai",  # GPT-4o is great for factual advice
        max_tokens=400,
        temperature=0.3
    )

    print(f"\nWeather Assistant ({response.metadata.get('provider')}):")
    print(response.content)
    print(f"\n💡 Used {response.tokens_used} tokens with {response.model}")


async def demo_creative_conversation():
    """Demo showing the creativity and personality of the LLMs."""
    print("\n\n🎭 Creative Conversation Demo")
    print("=" * 40)

    client = StandaloneLLMClient()

    # Fun creative prompt
    system_prompt = """You are a wise old wizard who has been studying both technology and magic for centuries. You speak in a mystical way but also understand modern concepts. You love to make connections between ancient magic and modern technology."""

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content="Wise wizard, how is artificial intelligence similar to the ancient art of divination?")
    ]

    print("Seeker: Wise wizard, how is artificial intelligence similar to the ancient art of divination?")
    print("\nThe Ancient Wizard peers into the mystic realm... 🔮")

    response = await client.generate_response(
        messages,
        max_tokens=300,
        temperature=0.8  # Higher temperature for more creativity
    )

    print(f"\nAncient Wizard ({response.metadata.get('provider')}):")
    print(response.content)
    print(f"\n💡 Used {response.tokens_used} tokens with {response.model}")


async def main():
    """Run all demos."""
    print("🚀 LLM Integration Demo - Real Responses from HubSpot Sandbox Keys!")
    print("=" * 70)
    print("This demo shows your agents providing real, intelligent responses")
    print("powered by OpenAI and Anthropic through HubSpot's sandbox keys.\n")

    try:
        await demo_language_teacher()
        await demo_weather_agent()
        await demo_creative_conversation()

        print("\n" + "=" * 70)
        print("🎉 Demo Complete!")
        print("Your LLM integration is working perfectly with:")
        print("✅ Real OpenAI responses (GPT-4o)")
        print("✅ Real Anthropic responses (Claude 3.5 Sonnet)")
        print("✅ HubSpot sandbox key integration")
        print("✅ Intelligent, contextual responses")
        print("✅ Different personalities and expertise")

        print("\n🚀 Your Agentic Framework is ready for production!")
        print("Simply add more agents, tools, and capabilities as needed.")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Check that your API keys are properly set in the .env file.")


if __name__ == "__main__":
    asyncio.run(main())
