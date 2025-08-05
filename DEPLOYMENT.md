# Agentic AI Framework - Deployment Guide

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/memory
mkdir -p logs
```

### 2. Environment Setup

Create a `.env` file:

```bash
# API Keys (if using external services)
WEATHER_API_KEY=your_weather_api_key_here
OPENAI_API_KEY=your_openai_key_here

# Database configuration
DATABASE_URL=sqlite:///./data/agentic.db

# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 3. Test the Framework

#### Start the API Server

```bash
# Start the server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# The server will automatically load agents from agents/configs/
```

#### Test Agent Interactions

```bash
# Test Professor James (British Teacher)
curl -X POST "http://localhost:8000/agents/Professor James/message" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, I want to learn British English pronunciation."}'

# Test Teacher Li (Chinese Teacher)
curl -X POST "http://localhost:8000/agents/Teacher Li/message" \
     -H "Content-Type: application/json" \
     -d '{"text": "Can you help me learn Chinese characters?"}'

# Test WeatherBot
curl -X POST "http://localhost:8000/agents/WeatherBot/message" \
     -H "Content-Type: application/json" \
     -d '{"text": "What is the weather like in London today?"}'
```

#### Test Agent Collaboration

```bash
# Make agents collaborate
curl -X POST "http://localhost:8000/agents/Professor James/collaborate/WeatherBot" \
     -H "Content-Type: application/json" \
     -d '{"text": "What is the weather like for outdoor English lessons in London?"}'
```

### 4. Create New Agents

#### Using the Script

```bash
# Create a cooking assistant
python scripts/create_agent.py \
    --name "Chef Mario" \
    --type "cooking_assistant" \
    --personality "Experienced Italian chef, warm and encouraging" \
    --collaborate-with "Professor James" "WeatherBot"

# Create a fitness coach
python scripts/create_agent.py \
    --name "Coach Alex" \
    --type "fitness_coach" \
    --personality "Motivational fitness expert" \
    --tools exercise_planner nutrition_tracker
```

#### Manual Configuration

Create `agents/configs/your_agent.yaml`:

```yaml
name: "Your Agent Name"
type: "your_agent_type"
implementation: "agents.implementations.your_agent.YourAgentClass"

personality:
  style: "Your agent's personality"
  tone: "Communication style"

system_prompt: |
  You are [Agent Name], a [description]. You help users with [capabilities].

tools:
  - name: "tool_name"
    class: "tools.category.tool_file.ToolClass"
    parameters:
      param1: "value1"

memory_config:
  remember_conversations: true
  context_window: 5
  importance_threshold: 0.6

collaboration:
  can_collaborate_with: ["other_agent_names"]

max_context_length: 4000
```

## Production Deployment

### 1. Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  agentic-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/agentic
      - WEATHER_API_KEY=${WEATHER_API_KEY}
    volumes:
      - ./data:/app/data
      - ./agents/configs:/app/agents/configs
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: agentic
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentic-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentic-api
  template:
    metadata:
      labels:
        app: agentic-api
    spec:
      containers:
      - name: agentic-api
        image: agentic-framework:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: agentic-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### 3. Environment Variables

Production environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/agentic
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
WEATHER_API_KEY=your_weather_api_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=INFO

# Performance
MAX_WORKERS=4
WORKER_CONNECTIONS=1000
```

## Development Workflow

### 1. Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with development settings
uvicorn api.main:app --reload --log-level debug
```

### 2. Creating Custom Agents

1. **Design the Agent**
   - Define the agent's purpose and capabilities
   - Identify required tools and integrations
   - Plan collaboration with other agents

2. **Create Configuration**
   ```bash
   python scripts/create_agent.py --name "YourAgent" --type "your_type"
   ```

3. **Implement Agent Class**
   ```python
   # agents/implementations/your_agent.py
   from framework.core.agent_base import BaseAgent

   class YourAgent(BaseAgent):
       async def generate_response(self, message: str, context: dict) -> dict:
           # Your agent logic here
           return {"response": "Agent response", "success": True}
   ```

4. **Create Tools**
   ```python
   # tools/your_category/your_tool.py
   from framework.mcp.tools.base_tool import BaseTool

   class YourTool(BaseTool):
       async def execute(self, **parameters):
           # Tool implementation
           return {"result": "tool output"}
   ```

5. **Test the Agent**
   ```bash
   # Test individually
   python scripts/run_agent.py --config agents/configs/youragent.yaml --interactive

   # Test via API
   curl -X POST "http://localhost:8000/agents/YourAgent/message" \
        -H "Content-Type: application/json" \
        -d '{"text": "test message"}'
   ```

### 3. Tool Development

Tools are the core of agent capabilities. Create tools for:
- **Data Processing**: Analysis, transformation, validation
- **External APIs**: Weather, translation, search services
- **File Operations**: Reading, writing, parsing documents
- **Communication**: Email, messaging, notifications
- **Specialized Functions**: Domain-specific operations

### 4. Testing Strategy

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Agent tests
pytest tests/agents/

# API tests
pytest tests/api/

# Load tests
pytest tests/load/
```

## Monitoring and Maintenance

### 1. Health Monitoring

```bash
# Check framework health
curl http://localhost:8000/health

# Check individual agents
curl http://localhost:8000/agents/AgentName

# Get statistics
curl http://localhost:8000/stats
```

### 2. Log Management

```python
# Configure structured logging
import structlog

logger = structlog.get_logger()
logger.info("Agent interaction", agent="AgentName", user="user123")
```

### 3. Performance Monitoring

- Monitor response times for agent interactions
- Track memory usage for context engines
- Monitor tool execution performance
- Set up alerting for failed agent health checks

### 4. Backup and Recovery

```bash
# Backup agent configurations
tar -czf configs-backup-$(date +%Y%m%d).tar.gz agents/configs/

# Backup memory data
tar -czf memory-backup-$(date +%Y%m%d).tar.gz data/memory/

# Database backup (if using PostgreSQL)
pg_dump agentic > backup-$(date +%Y%m%d).sql
```

## Troubleshooting

### Common Issues

1. **Agent Not Loading**
   - Check configuration file syntax
   - Verify implementation class path
   - Check tool dependencies

2. **Memory Issues**
   - Adjust context window sizes
   - Monitor memory usage patterns
   - Configure memory cleanup intervals

3. **Tool Failures**
   - Verify API keys and credentials
   - Check network connectivity
   - Review tool parameter schemas

4. **Performance Issues**
   - Profile agent response times
   - Optimize context management
   - Consider async tool execution

### Debug Mode

```bash
# Start with debug logging
LOG_LEVEL=DEBUG uvicorn api.main:app --reload

# Test agent with verbose output
python scripts/run_agent.py --config config.yaml --debug --interactive
```

## Security Considerations

1. **API Security**
   - Implement authentication and authorization
   - Use HTTPS in production
   - Rate limiting and request validation

2. **Data Privacy**
   - Encrypt sensitive data in memory storage
   - Implement data retention policies
   - User consent and data deletion

3. **Agent Isolation**
   - Sandboxed tool execution
   - Resource limits and quotas
   - Audit logging for all interactions

4. **Configuration Security**
   - Secure credential management
   - Environment-based configuration
   - Regular security updates

---

For more detailed information, see the full documentation at `/docs` when running the API server.
