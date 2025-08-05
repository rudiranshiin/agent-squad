#!/usr/bin/env python3
"""
Agent Creation Script

A utility to create new agent configurations easily through command-line interface.
"""

import argparse
import yaml
import os
from pathlib import Path
import sys


def create_agent_config():
    """Create a new agent configuration based on user input."""
    parser = argparse.ArgumentParser(
        description='Create a new agent configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a weather agent
  python scripts/create_agent.py --name "WeatherBot" --type "weather_assistant" --personality "Friendly meteorologist"

  # Create a language teacher
  python scripts/create_agent.py --name "Teacher Alice" --type "language_teacher" --personality "Patient and encouraging"

  # Create a custom agent with tools
  python scripts/create_agent.py --name "CookingBot" --type "cooking_assistant" --tools recipe_search nutrition_calculator
        """
    )

    # Required arguments
    parser.add_argument('--name', required=True, help='Agent name (e.g., "Professor James")')
    parser.add_argument('--type', required=True, help='Agent type (e.g., "language_teacher", "weather_assistant")')

    # Optional arguments
    parser.add_argument('--personality', help='Agent personality description')
    parser.add_argument('--tools', nargs='*', help='List of tools to include')
    parser.add_argument('--system-prompt', help='Custom system prompt for the agent')
    parser.add_argument('--output-dir', default='agents/configs', help='Output directory for config file')
    parser.add_argument('--implementation', help='Custom implementation class path')
    parser.add_argument('--collaborate-with', nargs='*', help='List of agents this agent can collaborate with')
    parser.add_argument('--memory-context-window', type=int, default=5, help='Memory context window size')
    parser.add_argument('--max-context-length', type=int, default=4000, help='Maximum context length')

    args = parser.parse_args()

    # Create config structure
    config = create_base_config(args)

    # Save config
    save_agent_config(config, args)

    print_success_message(args, config)


def create_base_config(args):
    """Create the base configuration structure."""
    # Determine implementation path
    implementation = args.implementation
    if not implementation:
        implementation_map = {
            "language_teacher": "agents.implementations.language_teacher.LanguageTeacherAgent",
            "weather_assistant": "agents.implementations.weather_agent.WeatherAgent",
            "cooking_assistant": "agents.implementations.cooking_assistant.CookingAssistantAgent",
            "general_assistant": "agents.implementations.general_agent.GeneralAgent"
        }
        implementation = implementation_map.get(args.type, f"agents.implementations.{args.type}.{args.type.title().replace('_', '')}Agent")

    # Create config structure
    config = {
        'name': args.name,
        'type': args.type,
        'implementation': implementation,
        'personality': create_personality_config(args),
        'system_prompt': create_system_prompt(args),
        'tools': create_tools_config(args),
        'memory_config': {
            'remember_conversations': True,
            'context_window': args.memory_context_window,
            'importance_threshold': 0.5
        },
        'collaboration': {
            'can_collaborate_with': args.collaborate_with or [],
            'collaboration_style': 'helpful'
        },
        'max_context_length': args.max_context_length,
        'max_context_items': 100,
        'max_memories': 1000
    }

    # Add type-specific configurations
    add_type_specific_config(config, args)

    return config


def create_personality_config(args):
    """Create personality configuration."""
    if args.personality:
        return {'style': args.personality}

    # Default personalities based on agent type
    personality_defaults = {
        'language_teacher': {'style': 'Patient and encouraging educator', 'tone': 'Supportive'},
        'weather_assistant': {'style': 'Friendly meteorologist', 'tone': 'Informative and helpful'},
        'cooking_assistant': {'style': 'Experienced chef', 'tone': 'Warm and encouraging'},
        'general_assistant': {'style': 'Professional and helpful', 'tone': 'Friendly'}
    }

    return personality_defaults.get(args.type, {'style': 'Professional and helpful'})


def create_system_prompt(args):
    """Create system prompt for the agent."""
    if args.system_prompt:
        return args.system_prompt

    # Default system prompts based on agent type
    prompt_templates = {
        'language_teacher': f"""You are {args.name}, an experienced language teacher who helps students learn
languages effectively. You provide clear explanations, constructive feedback, and cultural context to enhance
the learning experience. You are patient, encouraging, and adapt your teaching style to each student's needs.""",

        'weather_assistant': f"""You are {args.name}, a knowledgeable weather assistant with expertise in
meteorology and climate science. You provide accurate weather information, forecasts, and weather-related
advice. You help users plan activities based on weather conditions and provide safety recommendations.""",

        'cooking_assistant': f"""You are {args.name}, an experienced cooking assistant who helps users with
recipes, cooking techniques, and meal planning. You provide clear instructions, ingredient substitutions,
and cooking tips to help users create delicious meals.""",

        'general_assistant': f"""You are {args.name}, a helpful AI assistant who provides information and
assistance across a wide range of topics. You are knowledgeable, friendly, and always aim to be helpful
while maintaining accuracy."""
    }

    return prompt_templates.get(args.type, f"You are {args.name}, a helpful AI assistant.")


def create_tools_config(args):
    """Create tools configuration."""
    if not args.tools:
        # Default tools based on agent type
        default_tools = {
            'language_teacher': [
                {
                    'name': 'progress_tracker',
                    'class': 'tools.language_learning.progress_tracker.ProgressTracker',
                    'parameters': {
                        'focus_areas': ['vocabulary', 'grammar', 'pronunciation', 'cultural_understanding']
                    }
                },
                {
                    'name': 'grammar_checker',
                    'class': 'tools.language_learning.grammar_tool.GrammarTool',
                    'parameters': {'language': 'auto'}
                }
            ],
            'weather_assistant': [
                {
                    'name': 'weather_api',
                    'class': 'tools.weather.weather_api_tool.WeatherAPITool',
                    'parameters': {
                        'api_key': '${WEATHER_API_KEY}',
                        'default_units': 'metric'
                    }
                },
                {
                    'name': 'location_resolver',
                    'class': 'tools.weather.location_tool.LocationTool',
                    'parameters': {'geocoding_service': 'openweather'}
                }
            ]
        }

        return default_tools.get(args.type, [])

    # Create tools from command line arguments
    tools = []
    for tool in args.tools:
        tool_config = {
            'name': tool,
            'class': f'tools.{args.type}.{tool}.{tool.title().replace("_", "")}Tool'
        }
        tools.append(tool_config)

    return tools


def add_type_specific_config(config, args):
    """Add type-specific configuration options."""
    if args.type == 'language_teacher':
        config['language_config'] = {
            'primary_language': 'en',
            'specialties': ['grammar', 'vocabulary', 'pronunciation'],
            'teaching_methodology': 'communicative_approach'
        }
        config['teaching_preferences'] = {
            'feedback_style': 'constructive_and_encouraging',
            'correction_approach': 'gentle_guidance'
        }

    elif args.type == 'weather_assistant':
        config['weather_specialties'] = [
            'current_conditions',
            'forecasts',
            'severe_weather',
            'activity_planning'
        ]
        config['response_formats'] = {
            'brief': 'Quick weather summary',
            'detailed': 'Comprehensive weather analysis',
            'forecast': 'Multi-day weather outlook'
        }

    elif args.type == 'cooking_assistant':
        config['cooking_specialties'] = [
            'recipe_suggestions',
            'cooking_techniques',
            'ingredient_substitutions',
            'meal_planning'
        ]


def save_agent_config(config, args):
    """Save the agent configuration to a YAML file."""
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    safe_name = args.name.lower().replace(' ', '_').replace('-', '_')
    filename = f"{safe_name}.yaml"
    config_path = output_dir / filename

    # Save configuration
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2, sort_keys=False)

    print(f"✅ Agent configuration saved: {config_path}")


def print_success_message(args, config):
    """Print success message with next steps."""
    print("\n" + "="*60)
    print(f"🎉 Successfully created agent: {args.name}")
    print("="*60)

    print(f"\n📋 Agent Details:")
    print(f"   Name: {config['name']}")
    print(f"   Type: {config['type']}")
    print(f"   Implementation: {config['implementation']}")
    print(f"   Tools: {len(config['tools'])} configured")
    print(f"   Collaboration: {len(config['collaboration']['can_collaborate_with'])} partners")

    print(f"\n🚀 Next Steps:")
    print(f"   1. Review and customize the configuration file")
    print(f"   2. Implement the agent class if using a custom implementation:")
    print(f"      {config['implementation'].replace('.', '/')}.py")
    print(f"   3. Create required tools in: tools/{args.type}/")
    print(f"   4. Test the agent:")
    safe_name = args.name.lower().replace(' ', '_').replace('-', '_')
    print(f"      python scripts/run_agent.py --config agents/configs/{safe_name}.yaml --interactive")
    print(f"   5. Start the API server and test via HTTP:")
    print(f"      uvicorn api.main:app --reload")

    print(f"\n📚 Documentation:")
    print(f"   - Agent Development Guide: docs/agent-development.md")
    print(f"   - Tool Development Guide: docs/tool-development.md")
    print(f"   - API Documentation: http://localhost:8000/docs")


def validate_inputs(args):
    """Validate user inputs."""
    # Validate agent name
    if not args.name.strip():
        raise ValueError("Agent name cannot be empty")

    # Validate agent type
    if not args.type.strip():
        raise ValueError("Agent type cannot be empty")

    # Check for valid characters in type
    if not args.type.replace('_', '').isalnum():
        raise ValueError("Agent type should only contain letters, numbers, and underscores")


if __name__ == "__main__":
    try:
        create_agent_config()
    except KeyboardInterrupt:
        print("\n❌ Agent creation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error creating agent: {e}")
        sys.exit(1)
