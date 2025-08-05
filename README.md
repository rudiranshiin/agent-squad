# Agentic AI Framework

A sophisticated framework for building context-engineered AI agents with MCP (Model Context Protocol) tool integration and inter-agent communication capabilities.

## 🏗️ Architecture Overview

This framework provides a modular, scalable foundation for creating specialized AI agents that can:
- **Context Engineering**: Intelligent context management with priority-based optimization
- **MCP Tool Integration**: Seamless integration with Model Context Protocol tools
- **Inter-Agent Communication**: Agents can collaborate and share information
- **Third-Party Integration**: Easy integration with external APIs and services
- **Configuration-Driven**: Create new agents through YAML configuration
- **Memory Management**: Persistent conversation memory with relevance scoring

## 🚀 Key Features

### Context Engineering
- **Dynamic Context Optimization**: Automatically manages context window size and relevance
- **Priority-Based Context**: System, user, agent, and memory contexts with intelligent prioritization
- **Memory Integration**: Retrieves and incorporates relevant historical context
- **Token Management**: Optimizes context to stay within LLM token limits

### Agent Framework
- **Base Agent Class**: Extensible foundation for all agent implementations
- **Personality System**: Configure agent behavior, tone, and expertise
- **Tool Integration**: Automatic tool loading and execution
- **Collaboration**: Built-in inter-agent communication protocols

### MCP Tool System
- **Tool Registry**: Central registry for all available tools
- **Dynamic Loading**: Load tools from configuration
- **Shared Tools**: Tools can be shared across multiple agents
- **Third-Party Integration**: Easy integration with external services

## 📁 Project Structure

```
agentic-framework/
├── framework/                  # Core framework components
│   ├── core/                  # Base classes and engines
│   │   ├── agent_base.py     # Base agent implementation
│   │   ├── context_engine.py # Context management system
│   │   ├── memory_manager.py # Conversation memory
│   │   ├── tool_registry.py  # Tool management
│   │   └── agent_registry.py # Agent lifecycle management
│   ├── mcp/                  # MCP integration layer
│   │   ├── client.py         # MCP client implementation
│   │   ├── server.py         # MCP server implementation
│   │   └── tools/            # MCP tool implementations
│   ├── communication/        # Inter-agent communication
│   │   ├── inter_agent.py   # Agent collaboration protocols
│   │   └── protocols.py     # Communication protocols
│   └── utils/               # Utilities and helpers
│       ├── config_loader.py # Configuration management
│       ├── logging.py       # Logging utilities
│       └── validators.py    # Input validation
├── agents/                  # Agent implementations
│   ├── configs/            # Agent configuration files
│   ├── contexts/           # Agent-specific context managers
│   └── implementations/    # Concrete agent classes
├── tools/                  # Tool implementations
│   ├── language_learning/  # Language learning tools
│   ├── weather/           # Weather-related tools
│   └── shared/            # Shared utility tools
├── api/                   # REST/WebSocket API
│   ├── main.py           # FastAPI application
│   ├── routes/           # API route definitions
│   └── middleware/       # API middleware
├── database/             # Data persistence layer
├── configs/              # Global configuration files
├── tests/               # Test suite
└── scripts/             # Utility scripts
    ├── create_agent.py  # Agent creation script
    └── run_agent.py     # Agent execution script
```

## 🎯 Agent Examples

### British Teacher Agent
- **Specialization**: British English teaching with cultural context
- **Personality**: Professional, patient, encouraging
- **Tools**: Pronunciation checker, grammar analysis, cultural context
- **Features**: Accent-specific feedback, British idioms, formal language structure

### Chinese Teacher Agent
- **Specialization**: Mandarin Chinese language instruction
- **Personality**: Warm, encouraging, culturally aware
- **Tools**: Pinyin converter, character recognition, cultural context
- **Features**: Tone analysis, character stroke order, cultural nuances

### Weather Agent
- **Specialization**: Weather information and forecasting
- **Personality**: Friendly, informative, practical
- **Tools**: Weather API, location resolution, activity recommendations
- **Features**: Real-time data, forecasting, weather-based advice

## 🛠️ Technology Stack

- **Language**: Python 3.9+
- **Framework**: FastAPI for REST API
- **Database**: SQLAlchemy with PostgreSQL/SQLite
- **Configuration**: YAML-based configuration system
- **Testing**: pytest with async support
- **Containerization**: Docker and Docker Compose
- **MCP**: Model Context Protocol integration
- **LLM Integration**: OpenAI, Anthropic, or custom LLM providers

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd agentic-framework

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 2. Create Your First Agent

```bash
# Create a weather agent
python scripts/create_agent.py \
    --name "WeatherBot" \
    --type "weather_assistant" \
    --personality "Friendly meteorologist" \
    --tools weather_api location_resolver

# This creates: agents/configs/weatherbot.yaml
```

### 3. Run the Agent

```bash
# Interactive mode
python scripts/run_agent.py \
    --config agents/configs/weatherbot.yaml \
    --interactive

# Or start the API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test Agent Communication

```bash
# Send message to agent via API
curl -X POST "http://localhost:8000/agents/WeatherBot/message" \
     -H "Content-Type: application/json" \
     -d '{"text": "What is the weather like in London?"}'

# Agent collaboration
curl -X POST "http://localhost:8000/agents/Professor James/collaborate/WeatherBot" \
     -H "Content-Type: application/json" \
     -d '{"text": "What is the weather like for outdoor English lessons?"}'
```

## 🔧 Configuration Examples

### Agent Configuration (YAML)

```yaml
name: "Professor James"
type: "language_teacher"
implementation: "agents.implementations.language_teacher.LanguageTeacherAgent"

personality:
  style: "British gentleman"
  tone: "Patient and encouraging"
  cultural_background: "UK"
  formality: "formal"

system_prompt: |
  You are Professor James, a distinguished British English teacher...

tools:
  - name: "british_pronunciation"
    class: "tools.language_learning.pronunciation_tool.BritishPronunciationTool"
    parameters:
      accent: "received_pronunciation"

memory_config:
  remember_conversations: true
  context_window: 10
  importance_threshold: 0.6

collaboration:
  can_collaborate_with: ["chinese_teacher", "weather_agent"]
```

## 🧩 Extending the Framework

### Creating a New Agent Type

1. **Create Configuration**:
   ```bash
   python scripts/create_agent.py --name "CookingBot" --type "cooking_assistant"
   ```

2. **Implement Agent Class**:
   ```python
   # agents/implementations/cooking_assistant.py
   from framework.core.agent_base import BaseAgent

   class CookingAssistantAgent(BaseAgent):
       async def generate_response(self, message: str, context: dict) -> dict:
           # Implement cooking-specific logic
           pass
   ```

3. **Add Specialized Tools**:
   ```python
   # tools/cooking/recipe_tool.py
   from framework.mcp.tools.base_tool import BaseTool

   class RecipeTool(BaseTool):
       async def execute(self, **kwargs):
           # Implement recipe search logic
           pass
   ```

### Adding MCP Tools

```python
from framework.mcp.tools.base_tool import BaseTool

class CustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="Description of what the tool does"
        )

    async def execute(self, **parameters):
        # Tool implementation
        return result

    def get_parameter_schema(self):
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param1"]
        }
```

## 📊 Context Engineering

The framework includes sophisticated context management:

### Context Types
- **System Context**: Agent personality, instructions, capabilities
- **User Context**: Current and recent user interactions
- **Memory Context**: Relevant historical conversations
- **Agent Context**: Inter-agent communication context
- **Tool Context**: Tool execution results and feedback

### Context Optimization
- **Priority Scoring**: Automatic relevance scoring for context items
- **Token Management**: Intelligent truncation to fit LLM limits
- **Memory Retrieval**: Semantic search for relevant past interactions
- **Context Compression**: Summarization of older context when needed

## 🤝 Inter-Agent Communication

Agents can collaborate through:
- **Direct Messaging**: Send messages to other agents
- **Shared Context**: Access shared conversation history
- **Tool Sharing**: Use tools from other agents
- **Collaborative Tasks**: Work together on complex requests

## 🔐 Security and Privacy

- **API Authentication**: Token-based authentication for API access
- **Data Encryption**: Encrypted storage of sensitive conversation data
- **Privacy Controls**: User data retention and deletion policies
- **Audit Logging**: Comprehensive logging of all agent interactions

## 📈 Monitoring and Analytics

- **Performance Metrics**: Response times, token usage, error rates
- **Conversation Analytics**: User satisfaction, task completion rates
- **Agent Performance**: Individual agent effectiveness metrics
- **Tool Usage**: Most used tools and success rates

## 🔄 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale agents
docker-compose up -d --scale agent-worker=3
```

### Production Configuration

- **Load Balancing**: Multiple agent instances behind a load balancer
- **Database Clustering**: Distributed database for high availability
- **Monitoring**: Prometheus/Grafana for metrics and alerting
- **Logging**: Centralized logging with ELK stack

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/agents/

# Run with coverage
pytest --cov=framework tests/
```

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running the server
- **Agent Development Guide**: Detailed guide for creating custom agents
- **Tool Development Guide**: Instructions for creating MCP tools
- **Deployment Guide**: Production deployment instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Submit a pull request with detailed description

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Community discussions via GitHub Discussions
- **Documentation**: Comprehensive docs at [docs-url]

---

**Built with ❤️ for the AI Agent community**
