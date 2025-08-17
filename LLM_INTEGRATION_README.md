# LLM Integration for Agentic Framework

This document explains how to integrate and use Large Language Models (LLMs) with the Agentic framework, including support for OpenAI and Anthropic APIs using HubSpot sandbox keys.

## Overview

The framework now supports real LLM responses from:
- **OpenAI** (GPT-4, GPT-4o, GPT-3.5-turbo)
- **Anthropic** (Claude 3.5 Sonnet, Claude 3 Haiku)

## Quick Setup

### 1. Install Dependencies

The required packages are already included in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

Choose one of the following methods:

#### Option A: Environment Variables (Recommended)
```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Or for HubSpot sandbox keys
export OPENAI_ENGINEERING_SANDBOX_APIKEY="your-hubspot-openai-key"
export ANTHROPIC_ENGINEERING_SANDBOX_APIKEY="your-hubspot-anthropic-key"
```

#### Option B: .env File
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 3. Test the Integration

Run the test script to verify everything works:
```bash
python test_llm_integration.py
```

## For HubSpot Users

### Using HubSpot Sandbox Keys

The framework is designed to work with HubSpot's engineering sandbox API keys:

1. **OpenAI Sandbox Key**: `openai.engineering.sandbox.apikey`
2. **Anthropic Sandbox Key**: `anthropic.engineering.sandbox.apikey`

Set these as environment variables:
```bash
export OPENAI_ENGINEERING_SANDBOX_APIKEY="your-sandbox-key"
export ANTHROPIC_ENGINEERING_SANDBOX_APIKEY="your-sandbox-key"
```

### Vault Integration (Future)

The framework includes placeholder code for HubSpot Vault integration. In a real HubSpot environment, you would:

```python
from vault_client import VaultClient

vault_client = VaultClient("hs-engineering")
openai_key = vault_client.get_secret("openai.engineering.sandbox.apikey")
```

## Configuration

### Agent-Level Configuration

Each agent can specify its LLM preferences in its config file:

```yaml
# agents/configs/british_teacher.yaml
llm_config:
  preferred_provider: "anthropic"  # or "openai"
  max_response_tokens: 800
  response_temperature: 0.7
```

### Global Configuration

Create a global config file (see `config/llm_config_example.yaml`):

```yaml
llm_config:
  preferred_provider: "openai"
  openai_model: "gpt-4o"
  anthropic_model: "claude-3-5-sonnet-latest"
```

## Usage Examples

### Basic Agent Interaction

```python
from framework.core.agent_registry import AgentRegistry

# Load an agent
registry = AgentRegistry()
agent = registry.load_agent("agents/configs/british_teacher.yaml")

# Send a message (now uses real LLM!)
response = await agent.process_message("Teach me about British idioms")
print(response["response"])
```

### Direct LLM Client Usage

```python
from framework.core.llm_client import get_llm_client, LLMMessage

llm_client = get_llm_client()

# Simple string message
response = await llm_client.generate_response("Hello, world!")

# Advanced message with system prompt
messages = [
    LLMMessage(role="system", content="You are a helpful assistant"),
    LLMMessage(role="user", content="Explain quantum computing")
]
response = await llm_client.generate_response(messages, max_tokens=500)
```

## Agent Capabilities

### Language Teacher Agent

The language teacher now provides:
- **Real conversational responses** using Claude or GPT
- **Cultural context** and explanations
- **Grammar correction** with detailed feedback
- **Pronunciation guidance**
- **Personalized learning suggestions**

Example:
```python
agent = registry.load_agent("agents/configs/british_teacher.yaml")
response = await agent.process_message(
    "I want to learn about the difference between 'lorry' and 'truck'"
)
# Gets detailed explanation with cultural context
```

### Weather Agent

The weather agent now provides:
- **Contextual weather advice** using GPT or Claude
- **Activity recommendations** based on conditions
- **Safety warnings** with explanations
- **Personalized responses** based on user queries

Example:
```python
agent = registry.load_agent("agents/configs/weather_agent.yaml")
response = await agent.process_message(
    "Should I go hiking today if it's 15°C and cloudy?"
)
# Gets detailed advice about hiking in those conditions
```

## Model Selection Guide

### OpenAI Models
- **GPT-4o**: Best for complex reasoning, factual information
- **GPT-4**: Excellent for analysis and detailed responses
- **GPT-3.5-turbo**: Fast, cost-effective for simpler tasks

### Anthropic Models
- **Claude 3.5 Sonnet**: Excellent for creative, educational content
- **Claude 3 Haiku**: Fast, good for simple interactions

### Recommended by Agent Type

| Agent Type | Recommended Provider | Model | Temperature |
|------------|---------------------|-------|-------------|
| Language Teacher | Anthropic | Claude 3.5 Sonnet | 0.7 |
| Weather Agent | OpenAI | GPT-4o | 0.3 |
| Technical Agent | OpenAI | GPT-4 | 0.2 |
| Creative Agent | Anthropic | Claude 3.5 Sonnet | 0.8 |

## Error Handling

The framework includes robust error handling:

1. **Provider Fallback**: If preferred provider fails, tries backup
2. **Graceful Degradation**: Falls back to template responses if all LLMs fail
3. **Retry Logic**: Automatically retries failed requests
4. **Rate Limiting**: Respects API rate limits

## Monitoring and Logging

The framework logs LLM usage for monitoring:

```python
# Logs include:
# - Provider used (OpenAI/Anthropic)
# - Model used
# - Tokens consumed
# - Response time
# - Error details
```

## Testing

### Run Tests

```bash
# Test everything
python test_llm_integration.py

# Test specific agent
python -c "
import asyncio
from framework.core.agent_registry import AgentRegistry

async def test():
    registry = AgentRegistry()
    agent = registry.load_agent('agents/configs/british_teacher.yaml')
    response = await agent.process_message('Hello!')
    print(response['response'])

asyncio.run(test())
"
```

### Test Results

The test script checks:
- ✅ API key configuration
- ✅ LLM provider connectivity
- ✅ Agent loading and initialization
- ✅ Real LLM response generation
- ✅ Context and memory integration

## Troubleshooting

### Common Issues

1. **No LLM providers available**
   - Solution: Set API keys in environment variables

2. **Rate limit errors**
   - Solution: Reduce temperature or add delays between requests

3. **Agent falls back to template responses**
   - Solution: Check API keys and network connectivity

4. **Import errors**
   - Solution: Ensure `openai` and `anthropic` packages are installed

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger("framework.core.llm_client").setLevel(logging.DEBUG)
```

## Performance Considerations

- **Token Usage**: Monitor token consumption for cost control
- **Response Time**: Claude tends to be faster for educational content
- **Caching**: Future versions will include response caching
- **Batch Processing**: Consider batching multiple requests

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure vaults
- Rotate keys regularly
- Monitor usage for unexpected patterns

## Future Enhancements

- [ ] Response caching
- [ ] Streaming responses
- [ ] Local model support (Ollama)
- [ ] Advanced prompt engineering tools
- [ ] Usage analytics dashboard

## Support

For issues or questions:
1. Check the test script output
2. Review agent configurations
3. Verify API key setup
4. Check the logs for detailed error messages

The framework now provides rich, contextual responses powered by state-of-the-art language models while maintaining fallback capabilities for reliability.
