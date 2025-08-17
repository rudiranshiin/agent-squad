#!/bin/bash

echo "🚀 Agentic Framework LLM Integration Setup"
echo "==========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🔑 API Key Setup"
echo "=================="

# Check for existing API keys
openai_key_set=false
anthropic_key_set=false

if [ ! -z "$OPENAI_API_KEY" ] || [ ! -z "$OPENAI_ENGINEERING_SANDBOX_APIKEY" ]; then
    echo "✅ OpenAI API key found in environment"
    openai_key_set=true
else
    echo "❌ No OpenAI API key found"
fi

if [ ! -z "$ANTHROPIC_API_KEY" ] || [ ! -z "$ANTHROPIC_ENGINEERING_SANDBOX_APIKEY" ]; then
    echo "✅ Anthropic API key found in environment"
    anthropic_key_set=true
else
    echo "❌ No Anthropic API key found"
fi

if [ "$openai_key_set" = false ] && [ "$anthropic_key_set" = false ]; then
    echo ""
    echo "⚠️  No API keys found! You need at least one LLM provider."
    echo ""
    echo "For OpenAI:"
    echo "  export OPENAI_API_KEY='your-api-key'"
    echo "  or"
    echo "  export OPENAI_ENGINEERING_SANDBOX_APIKEY='your-hubspot-sandbox-key'"
    echo ""
    echo "For Anthropic:"
    echo "  export ANTHROPIC_API_KEY='your-api-key'"
    echo "  or"
    echo "  export ANTHROPIC_ENGINEERING_SANDBOX_APIKEY='your-hubspot-sandbox-key'"
    echo ""

    read -p "Would you like to set up API keys now? (y/n): " setup_keys

    if [ "$setup_keys" = "y" ] || [ "$setup_keys" = "Y" ]; then
        echo ""
        echo "Choose your provider:"
        echo "1) OpenAI"
        echo "2) Anthropic"
        echo "3) Both"
        read -p "Enter choice (1-3): " provider_choice

        case $provider_choice in
            1)
                read -p "Enter your OpenAI API key: " openai_key
                echo "export OPENAI_API_KEY='$openai_key'" >> ~/.bashrc
                echo "export OPENAI_API_KEY='$openai_key'" >> ~/.zshrc
                export OPENAI_API_KEY="$openai_key"
                echo "✅ OpenAI API key set"
                ;;
            2)
                read -p "Enter your Anthropic API key: " anthropic_key
                echo "export ANTHROPIC_API_KEY='$anthropic_key'" >> ~/.bashrc
                echo "export ANTHROPIC_API_KEY='$anthropic_key'" >> ~/.zshrc
                export ANTHROPIC_API_KEY="$anthropic_key"
                echo "✅ Anthropic API key set"
                ;;
            3)
                read -p "Enter your OpenAI API key: " openai_key
                read -p "Enter your Anthropic API key: " anthropic_key
                echo "export OPENAI_API_KEY='$openai_key'" >> ~/.bashrc
                echo "export OPENAI_API_KEY='$openai_key'" >> ~/.zshrc
                echo "export ANTHROPIC_API_KEY='$anthropic_key'" >> ~/.bashrc
                echo "export ANTHROPIC_API_KEY='$anthropic_key'" >> ~/.zshrc
                export OPENAI_API_KEY="$openai_key"
                export ANTHROPIC_API_KEY="$anthropic_key"
                echo "✅ Both API keys set"
                ;;
            *)
                echo "❌ Invalid choice"
                ;;
        esac

        echo ""
        echo "⚠️  Please restart your terminal or run 'source ~/.bashrc' (or ~/.zshrc) to load the new environment variables."
    fi
fi

echo ""
echo "🧪 Running Integration Tests"
echo "============================"

python test_llm_integration.py

echo ""
echo "📚 Next Steps"
echo "============="
echo "1. Review the test results above"
echo "2. If tests pass, your agents now have LLM capabilities!"
echo "3. Try the agents:"
echo "   python -c \"import asyncio; from framework.core.agent_registry import AgentRegistry; asyncio.run((lambda: AgentRegistry().load_agent('agents/configs/british_teacher.yaml').process_message('Hello!'))())\""
echo "4. Read LLM_INTEGRATION_README.md for detailed usage"
echo ""
echo "�� Setup complete!"
