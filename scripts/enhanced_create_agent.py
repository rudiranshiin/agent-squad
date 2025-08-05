#!/usr/bin/env python3
"""
Enhanced Agent Creation Tool

A comprehensive utility for creating agents using the new modular system.
Supports templates, validation, interactive mode, and complete module generation.
"""

import argparse
import asyncio
import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import rich
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework.core.agent_module import global_module_manager, AgentModuleInfo
from framework.utils.config_loader import ConfigLoader

console = Console()


@dataclass
class AgentTemplate:
    """Template for agent creation."""
    name: str
    description: str
    agent_types: List[str]
    default_tools: List[str]
    default_personality: Dict[str, str]
    config_template: Dict[str, Any]
    module_template: Optional[str] = None


class AgentValidator:
    """Validates agent configurations and ensures they're correct."""

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """Validate agent configuration and return list of errors."""
        errors = []

        # Required fields
        required_fields = ["name", "type"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # Name validation
        if "name" in config:
            name = config["name"]
            if not isinstance(name, str) or len(name.strip()) == 0:
                errors.append("Agent name must be a non-empty string")
            elif len(name) > 50:
                errors.append("Agent name must be 50 characters or less")

        # Type validation
        if "type" in config:
            agent_type = config["type"]
            if not isinstance(agent_type, str) or not agent_type.replace("_", "").isalnum():
                errors.append("Agent type must be alphanumeric with underscores")

        # Personality validation
        if "personality" in config and not isinstance(config["personality"], dict):
            errors.append("Personality must be a dictionary")

        # Tools validation
        if "tools" in config:
            if not isinstance(config["tools"], list):
                errors.append("Tools must be a list")
            else:
                for tool in config["tools"]:
                    if not isinstance(tool, dict) or "name" not in tool:
                        errors.append("Each tool must be a dictionary with a 'name' field")

        return errors

    @staticmethod
    def validate_module_config(config: Dict[str, Any]) -> List[str]:
        """Validate module configuration."""
        errors = []

        required_fields = ["name", "version", "description", "agent_types"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required module field: {field}")

        return errors


class TemplateManager:
    """Manages agent templates."""

    def __init__(self):
        self.templates = self._load_builtin_templates()

    def _load_builtin_templates(self) -> Dict[str, AgentTemplate]:
        """Load built-in agent templates."""
        return {
            "language_teacher": AgentTemplate(
                name="Language Teacher",
                description="AI agent for teaching languages with pronunciation, grammar, and cultural context",
                agent_types=["language_teacher"],
                default_tools=["pronunciation_tool", "grammar_checker", "progress_tracker", "cultural_context"],
                default_personality={
                    "style": "Patient and encouraging",
                    "tone": "Formal but friendly",
                    "expertise": "Language education"
                },
                config_template={
                    "language_config": {
                        "primary_language": "en-US",
                        "specialties": ["pronunciation", "grammar", "cultural_context"]
                    }
                }
            ),
            "cooking_assistant": AgentTemplate(
                name="Cooking Assistant",
                description="AI chef that helps with recipes, nutrition, and cooking techniques",
                agent_types=["cooking_assistant"],
                default_tools=["recipe_search", "nutrition_analyzer", "cooking_timer"],
                default_personality={
                    "style": "Warm and enthusiastic",
                    "tone": "Friendly and encouraging",
                    "expertise": "Culinary arts"
                },
                config_template={
                    "cuisine_preferences": ["international"],
                    "dietary_considerations": ["all"]
                },
                module_template="cooking"
            ),
            "weather_assistant": AgentTemplate(
                name="Weather Assistant",
                description="AI meteorologist for weather information and planning",
                agent_types=["weather_assistant"],
                default_tools=["weather_api", "location_resolver", "weather_alerts"],
                default_personality={
                    "style": "Informative and reliable",
                    "tone": "Professional",
                    "expertise": "Meteorology"
                },
                config_template={
                    "default_units": "metric",
                    "forecast_days": 5
                }
            ),
            "fitness_coach": AgentTemplate(
                name="Fitness Coach",
                description="AI personal trainer for workout plans and health advice",
                agent_types=["fitness_coach"],
                default_tools=["workout_planner", "nutrition_tracker", "progress_monitor"],
                default_personality={
                    "style": "Motivational and supportive",
                    "tone": "Energetic",
                    "expertise": "Fitness and wellness"
                },
                config_template={
                    "fitness_level": "beginner",
                    "goals": ["general_fitness"]
                }
            ),
            "study_buddy": AgentTemplate(
                name="Study Buddy",
                description="AI tutor for learning assistance and study planning",
                agent_types=["study_assistant"],
                default_tools=["quiz_generator", "study_planner", "research_helper"],
                default_personality={
                    "style": "Encouraging and methodical",
                    "tone": "Supportive",
                    "expertise": "Education and learning"
                },
                config_template={
                    "subjects": ["general"],
                    "learning_style": "adaptive"
                }
            )
        }

    def get_template(self, template_name: str) -> Optional[AgentTemplate]:
        """Get a template by name."""
        return self.templates.get(template_name)

    def list_templates(self) -> List[str]:
        """List available template names."""
        return list(self.templates.keys())

    def display_templates(self):
        """Display available templates in a nice format."""
        table = Table(title="Available Agent Templates")
        table.add_column("Template", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Types", style="green")
        table.add_column("Default Tools", style="yellow")

        for name, template in self.templates.items():
            table.add_row(
                name,
                template.description,
                ", ".join(template.agent_types),
                ", ".join(template.default_tools[:3]) + ("..." if len(template.default_tools) > 3 else "")
            )

        console.print(table)


class EnhancedAgentCreator:
    """Enhanced agent creation tool with full module support."""

    def __init__(self):
        self.template_manager = TemplateManager()
        self.validator = AgentValidator()

    async def create_agent_interactive(self) -> Dict[str, Any]:
        """Interactive agent creation wizard."""
        console.print(Panel.fit("🤖 Agent Creation Wizard", style="bold blue"))

        # Show available templates
        console.print("\n📋 Available Templates:")
        self.template_manager.display_templates()

        # Choose creation method
        console.print("\n🛠️  Creation Methods:")
        console.print("1. Use a template (recommended)")
        console.print("2. Create from scratch")
        console.print("3. Create complete module")

        method = Prompt.ask("Choose creation method", choices=["1", "2", "3"], default="1")

        if method == "1":
            return await self._create_from_template()
        elif method == "2":
            return await self._create_from_scratch()
        else:
            return await self._create_complete_module()

    async def _create_from_template(self) -> Dict[str, Any]:
        """Create agent from template."""
        template_names = self.template_manager.list_templates()

        template_name = Prompt.ask(
            "Choose template",
            choices=template_names,
            default=template_names[0]
        )

        template = self.template_manager.get_template(template_name)

        # Get basic info
        agent_name = Prompt.ask("Agent name", default=f"My {template.name}")

        # Customize personality
        console.print(f"\n🎭 Personality (default: {template.default_personality})")
        customize_personality = Confirm.ask("Customize personality?", default=False)

        personality = template.default_personality.copy()
        if customize_personality:
            personality["style"] = Prompt.ask("Style", default=personality["style"])
            personality["tone"] = Prompt.ask("Tone", default=personality["tone"])
            personality["expertise"] = Prompt.ask("Expertise", default=personality["expertise"])

        # Select tools
        console.print(f"\n🛠️  Tools (default: {template.default_tools})")
        customize_tools = Confirm.ask("Customize tools?", default=False)

        tools = []
        if customize_tools:
            for tool_name in template.default_tools:
                if Confirm.ask(f"Include {tool_name}?", default=True):
                    tools.append({"name": tool_name, "class": f"tools.{template_name}.{tool_name}.{tool_name.title()}Tool"})
        else:
            tools = [{"name": tool, "class": f"tools.{template_name}.{tool}.{tool.title()}Tool"} for tool in template.default_tools]

        # Build configuration
        config = {
            "name": agent_name,
            "type": template.agent_types[0],
            "implementation": f"agents.implementations.{template.agent_types[0]}.{template.agent_types[0].title()}Agent",
            "personality": personality,
            "system_prompt": f"You are {agent_name}, a {template.description.lower()}.",
            "tools": tools,
            "memory_config": {
                "remember_conversations": True,
                "context_window": 5,
                "importance_threshold": 0.5
            },
            "collaboration": {
                "can_collaborate_with": [],
                "collaboration_style": "helpful"
            },
            "max_context_length": 4000
        }

        # Add template-specific config
        config.update(template.config_template)

        return config

    async def _create_from_scratch(self) -> Dict[str, Any]:
        """Create agent from scratch."""
        console.print(Panel.fit("🔨 Creating Agent from Scratch", style="bold green"))

        # Basic info
        agent_name = Prompt.ask("Agent name")
        agent_type = Prompt.ask("Agent type (e.g., 'my_assistant')")
        description = Prompt.ask("Agent description")

        # Personality
        console.print("\n🎭 Personality:")
        style = Prompt.ask("Style", default="Professional and helpful")
        tone = Prompt.ask("Tone", default="Friendly")
        expertise = Prompt.ask("Area of expertise", default="General assistance")

        # Tools
        console.print("\n🛠️  Tools:")
        tools = []
        while True:
            tool_name = Prompt.ask("Tool name (or 'done' to finish)", default="done")
            if tool_name.lower() == "done":
                break

            tool_class = Prompt.ask("Tool class path", default=f"tools.{agent_type}.{tool_name}.{tool_name.title()}Tool")
            tools.append({"name": tool_name, "class": tool_class})

        # Build configuration
        config = {
            "name": agent_name,
            "type": agent_type,
            "implementation": f"agents.implementations.{agent_type}.{agent_type.title()}Agent",
            "personality": {
                "style": style,
                "tone": tone,
                "expertise": expertise
            },
            "system_prompt": f"You are {agent_name}, {description}.",
            "tools": tools,
            "memory_config": {
                "remember_conversations": True,
                "context_window": 5,
                "importance_threshold": 0.5
            },
            "collaboration": {
                "can_collaborate_with": [],
                "collaboration_style": "helpful"
            },
            "max_context_length": 4000
        }

        return config

    async def _create_complete_module(self) -> Dict[str, Any]:
        """Create a complete agent module."""
        console.print(Panel.fit("📦 Creating Complete Agent Module", style="bold magenta"))

        # Module info
        module_name = Prompt.ask("Module name")
        version = Prompt.ask("Version", default="1.0.0")
        description = Prompt.ask("Module description")
        author = Prompt.ask("Author", default="Agent Developer")

        # Agent types
        agent_types = []
        console.print("\n🤖 Agent Types:")
        while True:
            agent_type = Prompt.ask("Agent type (or 'done' to finish)", default="done")
            if agent_type.lower() == "done":
                break
            agent_types.append(agent_type)

        if not agent_types:
            agent_types = [f"{module_name}_assistant"]

        # Tools
        tools = []
        console.print("\n🛠️  Tools:")
        while True:
            tool_name = Prompt.ask("Tool name (or 'done' to finish)", default="done")
            if tool_name.lower() == "done":
                break
            tools.append(tool_name)

        # Create module using template
        template_name = None
        if module_name.lower() in self.template_manager.list_templates():
            template_name = module_name.lower()

        # Install module
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating module...", total=None)

            try:
                module_config = {
                    "name": module_name,
                    "version": version,
                    "description": description,
                    "author": author,
                    "agent_types": agent_types,
                    "tools": tools
                }

                if template_name:
                    module_path = await global_module_manager.install_module_from_template(
                        template_name, module_name, module_config
                    )
                else:
                    # Create basic module structure
                    module_path = await self._create_basic_module(module_name, module_config)

                progress.update(task, description="Loading module...")
                await global_module_manager.load_module(module_path)

                console.print(f"✅ Module '{module_name}' created and loaded successfully!")

                return {
                    "module_created": True,
                    "module_name": module_name,
                    "module_path": module_path,
                    "agent_types": agent_types
                }

            except Exception as e:
                console.print(f"❌ Error creating module: {e}")
                return {"error": str(e)}

    async def _create_basic_module(self, module_name: str, config: Dict[str, Any]) -> str:
        """Create a basic module structure."""
        # This would create a basic module template
        # For now, we'll use the cooking template as a base
        return await global_module_manager.install_module_from_template(
            "cooking", module_name, config
        )

    def save_config(self, config: Dict[str, Any], output_path: str = None) -> str:
        """Save agent configuration to file."""
        if output_path is None:
            agent_name = config["name"].lower().replace(" ", "_").replace("-", "_")
            output_path = f"agents/configs/{agent_name}.yaml"

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Validate before saving
        errors = self.validator.validate_config(config)
        if errors:
            console.print("❌ Configuration validation errors:")
            for error in errors:
                console.print(f"  • {error}")
            raise ValueError("Configuration validation failed")

        # Save configuration
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        return output_path

    def display_config_preview(self, config: Dict[str, Any]):
        """Display a preview of the configuration."""
        console.print(Panel.fit("📋 Configuration Preview", style="bold cyan"))

        # Basic info
        console.print(f"🤖 Name: {config['name']}")
        console.print(f"🏷️  Type: {config['type']}")
        console.print(f"💭 Personality: {config.get('personality', {})}")

        # Tools
        tools = config.get('tools', [])
        if tools:
            console.print(f"🛠️  Tools ({len(tools)}):")
            for tool in tools[:5]:  # Show first 5 tools
                console.print(f"   • {tool.get('name', 'Unknown')}")
            if len(tools) > 5:
                console.print(f"   ... and {len(tools) - 5} more")

        # Memory config
        memory_config = config.get('memory_config', {})
        console.print(f"🧠 Memory: {memory_config.get('context_window', 5)} items, remember conversations: {memory_config.get('remember_conversations', True)}")


async def main():
    """Main function for the enhanced agent creation tool."""
    parser = argparse.ArgumentParser(
        description="Enhanced Agent Creation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended)
  python scripts/enhanced_create_agent.py

  # Create from template
  python scripts/enhanced_create_agent.py --template cooking_assistant --name "Chef Bot"

  # Create module
  python scripts/enhanced_create_agent.py --create-module --name "fitness_module"

  # List templates
  python scripts/enhanced_create_agent.py --list-templates
        """
    )

    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--template", help="Use specified template")
    parser.add_argument("--name", help="Agent name")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--create-module", action="store_true", help="Create a complete module")
    parser.add_argument("--list-templates", action="store_true", help="List available templates")
    parser.add_argument("--validate", help="Validate an existing config file")

    args = parser.parse_args()

    creator = EnhancedAgentCreator()

    try:
        if args.list_templates:
            creator.template_manager.display_templates()
            return

        if args.validate:
            with open(args.validate, 'r') as f:
                config = yaml.safe_load(f)

            errors = creator.validator.validate_config(config)
            if errors:
                console.print("❌ Validation errors:")
                for error in errors:
                    console.print(f"  • {error}")
            else:
                console.print("✅ Configuration is valid!")
            return

        if args.interactive or not any([args.template, args.create_module]):
            config = await creator.create_agent_interactive()
        elif args.create_module:
            config = await creator._create_complete_module()
            return  # Module creation handles everything
        elif args.template:
            template = creator.template_manager.get_template(args.template)
            if not template:
                console.print(f"❌ Template '{args.template}' not found")
                return

            agent_name = args.name or f"My {template.name}"
            config = {
                "name": agent_name,
                "type": template.agent_types[0],
                "implementation": f"agents.implementations.{template.agent_types[0]}.{template.agent_types[0].title()}Agent",
                "personality": template.default_personality,
                "system_prompt": f"You are {agent_name}, a {template.description.lower()}.",
                "tools": [{"name": tool, "class": f"tools.{args.template}.{tool}.{tool.title()}Tool"} for tool in template.default_tools],
                "memory_config": {
                    "remember_conversations": True,
                    "context_window": 5,
                    "importance_threshold": 0.5
                },
                "max_context_length": 4000
            }
            config.update(template.config_template)

        # Preview and save
        creator.display_config_preview(config)

        if Confirm.ask("Save this configuration?", default=True):
            output_path = creator.save_config(config, args.output)
            console.print(f"✅ Configuration saved to: {output_path}")

            # Optional: Load the agent
            if Confirm.ask("Load the agent now?", default=True):
                try:
                    from framework.core.agent_registry import AgentRegistry
                    agent = await AgentRegistry.create_agent_from_config(output_path)
                    console.print(f"🚀 Agent '{agent.name}' loaded successfully!")
                except Exception as e:
                    console.print(f"⚠️  Agent saved but failed to load: {e}")

    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
    except Exception as e:
        console.print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
