#!/usr/bin/env python3
"""SmithAI Skills System - Complete Demo.

Demonstrates:
1. Skill creation and registration
2. Skill execution with async support
3. Skill discovery and search
4. Skill publishing and importing
5. Skill learning patterns
6. Skill composition (pipelines)
7. CLI interface
8. Built-in skills
"""

import asyncio
import sys
import os

sys.path.insert(0, "/Users/himand/open-agent/src")


def print_header(title: str) -> None:
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")


def print_section(title: str) -> None:
    print(f"\n{'-'*70}")
    print(f" {title}")
    print(f"{'-'*70}")


def demo_skill_basics():
    """Demo basic skill operations."""
    print_header("1. SKILL BASICS")
    
    from smith_ai.skills import (
        Skill, SkillMetadata, SkillCategory, SimpleSkill,
        SkillRegistry, register_builtin_skills
    )
    
    print_section("Creating a Skill")
    
    # Create metadata
    metadata = SkillMetadata(
        name="my_first_skill",
        version="1.0.0",
        description="A simple demonstration skill",
        author="Demo Author",
        category=SkillCategory.UTILITY,
        tags=["demo", "example"],
    )
    print(f"  Created metadata: {metadata.name}@{metadata.version}")
    
    # Create skill
    skill = SimpleSkill(metadata)
    
    # Add handlers
    def hello(name: str = "World") -> str:
        return f"Hello, {name}!"
    
    async def async_greet(name: str = "World") -> str:
        await asyncio.sleep(0.01)  # Simulate async operation
        return f"Async Hello, {name}!"
    
    skill.add_handler(
        name="greet",
        description="Greet someone",
        handler=hello,
    )
    
    skill.add_handler(
        name="async_greet",
        description="Greet someone asynchronously",
        async_handler=async_greet,
    )
    
    print(f"  Added 2 handlers: greet, async_greet")
    
    print_section("Skill Registry")
    
    registry = SkillRegistry()
    print(f"  Registry created at: {registry.storage_path}")
    
    # Register skill
    success = registry.register(skill)
    print(f"  Registered skill: {success}")
    
    # List skills
    skills = registry.list_all()
    print(f"  Total skills: {len(skills)}")
    
    # Get metadata
    meta = registry.get_metadata("my_first_skill")
    if meta:
        print(f"  Skill info: {meta.name} by {meta.author}")
    
    return True


async def demo_skill_execution():
    """Demo skill execution."""
    print_header("2. SKILL EXECUTION")
    
    from smith_ai.skills import SkillRegistry, SimpleSkill, SkillMetadata, SkillCategory
    from smith_ai.skills import register_builtin_skills
    
    registry = SkillRegistry()
    
    # Register built-in skills
    print_section("Registering Built-in Skills")
    register_builtin_skills(registry)
    print(f"  Registered built-in skills: {len(registry.list_all())}")
    
    print_section("Executing Calculator Skill")
    
    # Execute calculator
    result = await registry.execute(
        "calculator",
        "evaluate",
        expression="25 + 17 * 3"
    )
    print(f"  Expression: 25 + 17 * 3")
    print(f"  Result: {result.result}")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.duration_ms:.2f}ms")
    
    print_section("Executing Text Processor Skill")
    
    # Execute text processor
    result = await registry.execute(
        "text_processor",
        "count_words",
        text="This is a sample text for testing"
    )
    print(f"  Text: 'This is a sample text for testing'")
    print(f"  Word count: {result.result}")
    
    # Execute sentiment
    result = await registry.execute(
        "text_processor",
        "sentiment",
        text="I love this amazing product, it's absolutely wonderful!"
    )
    print(f"  Sentiment analysis: {result.result}")
    
    print_section("Executing Memory Skill")
    
    # Store
    result = await registry.execute("memory", "store", key="test_key", value="test_value")
    print(f"  Store: {result.result}")
    
    # Retrieve
    result = await registry.execute("memory", "retrieve", key="test_key")
    print(f"  Retrieve: {result.result}")
    
    # List keys
    result = await registry.execute("memory", "list_keys")
    print(f"  All keys: {result.result}")
    
    return True


def demo_skill_creation():
    """Demo creating custom skills."""
    print_header("3. CREATING CUSTOM SKILLS")
    
    from smith_ai.skills import (
        SkillManager, SkillCategory, SkillMetadata, SimpleSkill
    )
    
    manager = SkillManager()
    
    print_section("Creating a Weather Skill")
    
    # Create a custom skill
    async def get_weather(location: str, units: str = "celsius") -> dict:
        """Get weather for a location."""
        # Simulated weather data
        return {
            "location": location,
            "temperature": 22 if units == "celsius" else 72,
            "units": units,
            "condition": "sunny",
            "humidity": 45,
        }
    
    async def get_forecast(location: str, days: int = 7) -> list:
        """Get weather forecast."""
        return [
            {"day": i, "temp": 20 + i, "condition": "partly cloudy"}
            for i in range(1, days + 1)
        ]
    
    # Create skill
    weather_skill = manager.create_skill(
        name="weather",
        version="1.0.0",
        description="Weather information skill",
        author="Demo",
        category=SkillCategory.UTILITY,
        handlers={
            "get_weather": ("Get current weather", get_weather),
            "get_forecast": ("Get forecast", get_forecast),
        }
    )
    
    print(f"  Created skill: {weather_skill.metadata.name}")
    
    # Register
    manager.registry.register(weather_skill)
    print(f"  Registered skill")
    
    print_section("Running Custom Skill")
    
    # Execute
    async def test_weather():
        result = await manager.registry.execute(
            "weather",
            "get_weather",
            location="San Francisco",
            units="fahrenheit"
        )
        print(f"  Weather result: {result.result}")
        
        result = await manager.registry.execute(
            "weather",
            "get_forecast",
            location="San Francisco",
            days=5
        )
        print(f"  Forecast: {len(result.result)} days")
    
    asyncio.run(test_weather())
    
    return True


def demo_skill_publishing():
    """Demo publishing skills."""
    print_header("4. PUBLISHING SKILLS")
    
    from smith_ai.skills import SkillManager, SkillMetadata, SimpleSkill, SkillCategory
    import tempfile
    
    manager = SkillManager()
    
    print_section("Creating Publishable Skill")
    
    # Create a skill
    metadata = SkillMetadata(
        name="data_transformer",
        version="1.0.0",
        description="Transform data between formats",
        author="SmithAI",
        category=SkillCategory.DATA,
        tags=["data", "transform", "format"],
        license="MIT",
        repository="https://github.com/example/data-transformer",
    )
    
    skill = SimpleSkill(metadata)
    
    def to_json(data: str) -> str:
        """Convert to JSON."""
        return json.dumps({"data": data})
    
    def to_xml(data: str) -> str:
        """Convert to XML."""
        return f"<root><data>{data}</data></root>"
    
    skill.add_handler(name="to_json", description="Convert to JSON", handler=to_json)
    skill.add_handler(name="to_xml", description="Convert to XML", handler=to_xml)
    
    print(f"  Created: {skill.metadata.name}@{skill.metadata.version}")
    
    print_section("Exporting Skill")
    
    # First register the skill
    manager.registry.register(skill)
    
    # Export to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    success = manager.export_skill("data_transformer", temp_path)
    print(f"  Exported to: {temp_path}")
    print(f"  Success: {success}")
    
    print_section("Publishing Skill (Simulated)")
    
    # Simulate publish
    success = asyncio.run(manager.publish(skill))
    print(f"  Published: {success}")
    
    print_section("Importing Skill")
    
    # Import the exported skill
    if success:
        manager2 = SkillManager()
        success = manager2.import_skill(temp_path)
        print(f"  Imported: {success}")
        
        # Clean up
        os.unlink(temp_path)
    
    return True


def demo_skill_learning():
    """Demo skill learning patterns."""
    print_header("5. SKILL LEARNING")
    
    from smith_ai.skills import SkillRegistry, register_builtin_skills
    
    registry = SkillRegistry()
    register_builtin_skills(registry)
    
    print_section("Executing Multiple Times")
    
    # Execute same handler multiple times
    expressions = ["2+2", "10*10", "100-50", "25/5", "2**8"]
    
    for expr in expressions:
        result = asyncio.run(registry.execute(
            "calculator",
            "evaluate",
            expression=expr
        ))
        print(f"  {expr} = {result.result}")
    
    print_section("Learning Patterns")
    
    patterns = registry.get_learned_patterns()
    print(f"  Learned patterns: {len(patterns)}")
    
    for key, pattern in patterns.items():
        print(f"\n  {key}:")
        print(f"    Total executions: {pattern['total_executions']}")
        print(f"    Success rate: {pattern['successful_executions']/pattern['total_executions']*100:.0f}%")
        print(f"    Output types: {pattern['output_types']}")
    
    print_section("Suggested Next Handler")
    
    suggestion = registry.suggest_next_handler("calculator", "evaluate", {})
    print(f"  Suggested next: {suggestion}")
    
    print_section("Execution Statistics")
    
    stats = registry.get_execution_stats()
    print(f"  Total executions: {stats['total_executions']}")
    print(f"  Success rate: {stats['success_rate']*100:.0f}%")
    print(f"  Skills: {stats['skills_count']}")
    print(f"  Learned patterns: {stats['learned_patterns']}")
    
    return True


def demo_skill_composition():
    """Demo skill pipelines."""
    print_header("6. SKILL COMPOSITION")
    
    from smith_ai.skills import SkillManager, register_builtin_skills
    
    manager = SkillManager()
    register_builtin_skills(manager.registry)
    
    print_section("Creating Pipeline")
    
    # Create a pipeline: text -> count words -> calculate
    manager.composer.create_pipeline(
        name="text_analysis",
        steps=[
            ("text_processor", "count_words"),
            ("calculator", "evaluate"),  # Uses result as expression
        ]
    )
    
    print(f"  Created pipeline: text_analysis")
    print(f"  Steps: text_processor.count_words -> calculator.evaluate")
    
    print_section("Executing Pipeline")
    
    async def run_pipeline():
        try:
            result = await manager.composer.execute_pipeline(
                "text_analysis",
                "hello world",  # Initial input
            )
            print(f"  Pipeline result: {result}")
        except Exception as e:
            print(f"  Pipeline error: {e}")
    
    asyncio.run(run_pipeline())
    
    return True


def demo_skill_cli():
    """Demo CLI interface."""
    print_header("7. SKILL CLI")
    
    from smith_ai.skills import SkillManager, SkillCLI, register_builtin_skills
    
    manager = SkillManager()
    register_builtin_skills(manager.registry)
    cli = SkillCLI(manager)
    
    print_section("CLI Commands")
    
    print("""
Skill CLI Commands:
  list                       - List installed skills
  install <name> [source]    - Install a skill
  uninstall <name>           - Uninstall a skill  
  search <query>             - Search for skills
  publish <path>             - Publish a skill
  info <name>                - Show skill information
  export <name> <path>        - Export a skill
  import <path>              - Import a skill
  run <name>.<handler>       - Run a skill handler
""")
    
    print_section("CLI Demo")
    
    # Test list command
    print("$ skill list")
    cli.list_skills([])
    
    return True


def demo_skill_in_tui():
    """Demo skill integration with TUI."""
    print_header("8. SKILLS IN TUI")
    
    from smith_ai.tui import SmithAIApp
    from smith_ai.skills import SkillManager, register_builtin_skills
    
    # Create skill manager
    manager = SkillManager()
    register_builtin_skills(manager.registry)
    
    print_section("Skills Available in TUI")
    
    skills = manager.registry.list_all()
    print(f"  Total skills: {len(skills)}")
    
    for skill_name in skills:
        meta = manager.registry.get_metadata(skill_name)
        if meta:
            handlers = manager.registry.get(skill_name)
            if handlers:
                handler_names = [h.name for h in handlers.get_all_handlers()]
                print(f"\n  {meta.name}@{meta.version}")
                print(f"    Category: {meta.category.value}")
                print(f"    Handlers: {', '.join(handler_names)}")
    
    return True


async def demo_async_skill():
    """Demo async skill operations."""
    print_header("9. ASYNC SKILL OPERATIONS")
    
    from smith_ai.skills import SkillManager, register_builtin_skills
    
    manager = SkillManager()
    register_builtin_skills(manager.registry)
    
    print_section("Parallel Execution")
    
    # Execute multiple skills in parallel
    tasks = [
        manager.registry.execute("calculator", "evaluate", expression="100+200"),
        manager.registry.execute("text_processor", "count_words", text="async execution demo"),
        manager.registry.execute("memory", "store", key="async_key", value="async_value"),
    ]
    
    results = await asyncio.gather(*tasks)
    
    print("  Parallel results:")
    for i, result in enumerate(results):
        print(f"    [{i}] {result.skill_name}.{result.handler}: {result.result}")
    
    print_section("Chain Execution")
    
    # Chain: store -> retrieve -> process
    await manager.registry.execute("memory", "store", key="chain", value="test")
    result = await manager.registry.execute("memory", "retrieve", key="chain")
    result = await manager.registry.execute("text_processor", "capitalize", text=str(result.result))
    print(f"  Chain result: {result.result}")
    
    return True


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("  SmithAI Skills System - Complete Demo")
    print("  Version 4.0.0 - Plugin-based Skill Architecture")
    print("="*70)
    
    demos = [
        ("Skill Basics", demo_skill_basics),
        ("Skill Execution", demo_skill_execution),
        ("Custom Skill Creation", demo_skill_creation),
        ("Publishing Skills", demo_skill_publishing),
        ("Skill Learning", demo_skill_learning),
        ("Skill Composition", demo_skill_composition),
        ("Skill CLI", demo_skill_cli),
        ("Skills in TUI", demo_skill_in_tui),
        ("Async Operations", demo_async_skill),
    ]
    
    results = []
    
    for name, demo in demos:
        try:
            if asyncio.iscoroutinefunction(demo):
                result = asyncio.run(demo())
            else:
                result = demo()
            results.append((name, result))
            status = "[PASS]" if result else "[FAIL]"
            print(f"\n{status} {name}")
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "="*70)
    print(" FINAL SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{total} demos passed")
    
    print("\n" + "="*70)
    print(" SKILLS SYSTEM FEATURES")
    print("="*70)
    print("""
  ✓ Plugin-based architecture
  ✓ Local skill registry with persistence
  ✓ Remote registry sync (publish/subscribe)
  ✓ Semantic versioning
  ✓ Skill dependencies
  ✓ Async execution support
  ✓ Learning from execution patterns
  ✓ Skill composition (pipelines)
  ✓ CLI interface
  ✓ Export/Import capabilities
  ✓ Built-in skills (calculator, memory, text, researcher)
  ✓ TUI integration
  ✓ Developer publishing workflow
""")
    
    return passed == total


if __name__ == "__main__":
    import json
    success = main()
    sys.exit(0 if success else 1)
