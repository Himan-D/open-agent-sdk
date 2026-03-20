# SmithAI

**Production-ready Python AI Agent Framework with Crew-style Multi-Agent Orchestration**

Built with NVIDIA Nemotron, OpenAI, Anthropic Claude, Google Gemini, and more.

## Features

- **Multi-LLM Support** - Seamlessly switch between NVIDIA, OpenAI, Anthropic, Google, Ollama
- **CrewAI-Style Agents** - Define agents with roles, goals, and backstories
- **Task Orchestration** - Sequential, parallel, and hierarchical execution
- **Tool System** - Calculator, web search, Python REPL, file operations
- **Persistent Memory** - MEMORY.md-style storage across sessions
- **Async-First** - Built on asyncio for high performance
- **Production Ready** - Type-safe, well-documented, stable

## Quick Start

### Installation

```bash
pip install smith-ai
```

### Environment Variables

```bash
# Choose your LLM provider
export NVIDIA_API_KEY=your_nvidia_key      # Recommended
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key
export GOOGLE_API_KEY=your_google_key

# Optional
export DEFAULT_LLM_PROVIDER=nvidia
export DEFAULT_MODEL=nvidia/nemotron-3-super-120b-a12b
```

### Basic Agent

```python
import asyncio
from smith_ai import create_agent

async def main():
    agent = await create_agent(
        name="assistant",
        role="AI Assistant",
        goal="Help users with their questions",
        backstory="You are a helpful AI assistant powered by NVIDIA Nemotron",
        provider="nvidia",
    )
    
    result = await agent.execute("What is machine learning?")
    print(result)

asyncio.run(main())
```

### Multi-Agent Crew

```python
import asyncio
from smith_ai import create_agent, create_crew, Task

async def main():
    # Create agents
    researcher = await create_agent(
        name="researcher",
        role="Researcher",
        goal="Research topics thoroughly",
        backstory="Expert researcher with decades of experience"
    )
    
    writer = await create_agent(
        name="writer",
        role="Content Writer",
        goal="Create engaging content",
        backstory="Skilled writer who transforms complex info into clear narratives"
    )
    
    # Create crew with tasks
    crew = create_crew(
        agents_config=[
            {"name": "researcher", "role": "Researcher", 
             "goal": "Research topics", "backstory": researcher.backstory},
            {"name": "writer", "role": "Writer",
             "goal": "Write content", "backstory": writer.backstory},
        ],
        tasks_config=[
            {"description": "Research AI trends 2025", "agent": "researcher",
             "expected_output": "Comprehensive research summary"},
            {"description": "Write article based on research", "agent": "writer",
             "expected_output": "Published article"},
        ],
        process="sequential",
        verbose=True,
    )
    
    # Execute
    results = await crew.kickoff()
    print(results)

asyncio.run(main())
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SmithAI                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    Crew     │  │   Agent     │  │       Task          │ │
│  │ Orchestrate │  │   Execute   │  │    Work Unit        │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                    │             │
│         ▼                ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   LLM Layer                         │    │
│  │  NVIDIA │ OpenAI │ Anthropic │ Google │ Ollama       │    │
│  └─────────────────────────────────────────────────────┘    │
│         │                │                    │             │
│         ▼                ▼                    ▼             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Tools     │  │   Memory     │  │     Config          │ │
│  │ Calculator  │  │  Persistent  │  │  Environment       │ │
│  │  WebSearch  │  │  Storage     │  │  Variables         │ │
│  │  Python     │  │              │  │                    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Agent

Autonomous unit with role, goal, and backstory:

```python
from smith_ai import Agent, AgentConfig, LLMFactory, LLMProvider

agent = Agent(AgentConfig(
    name="my_agent",
    role="Researcher",
    goal="Find information quickly",
    backstory="You are a research expert",
    llm=LLMFactory.create(LLMProvider.NVIDIA, api_key="..."),
))
```

### Crew

Orchestrates multiple agents with task management:

```python
from smith_ai import Crew

crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2, task3],
    process=Crew.Process.SEQUENTIAL,  # or PARALLEL, HIERARCHICAL
    verbose=True,
)

results = await crew.kickoff()
```

### Task

Work unit assigned to an agent:

```python
from smith_ai import Task

task = Task(
    description="Research the topic",
    agent=researcher,
    expected_output="Summary of key findings",
    context=[previous_task],  # Pass context from other tasks
)
```

### LLM Providers

```python
from smith_ai import LLMFactory, LLMProvider

# NVIDIA Nemotron (recommended)
llm = LLMFactory.create(LLMProvider.NVIDIA, 
    api_key="...", 
    model="nvidia/nemotron-3-super-120b-a12b")

# OpenAI GPT
llm = LLMFactory.create(LLMProvider.OPENAI,
    api_key="...",
    model="gpt-4o")

# Anthropic Claude
llm = LLMFactory.create(LLMProvider.ANTHROPIC,
    api_key="...",
    model="claude-3-5-sonnet-20241022")

# Google Gemini
llm = LLMFactory.create(LLMProvider.GOOGLE,
    api_key="...",
    model="gemini-2.0-flash-exp")

# Ollama (local)
llm = LLMFactory.create(LLMProvider.OLLAMA,
    model="llama3.2",
    base_url="http://localhost:11434")
```

### Tools

```python
from smith_ai import (
    CalculatorTool,
    WebSearchTool,
    PythonREPLTool,
    FileReadTool,
    FileWriteTool,
    WebFetchTool,
    get_default_tools,
)

# All default tools
tools = get_default_tools()

# Specific tools
tools = [
    CalculatorTool(),
    WebSearchTool(),
    PythonREPLTool(),
]
```

## Examples

Run the examples:

```bash
# Test all LLM providers
python examples/04_test_llms.py

# Basic agent
python examples/01_basic_agent.py

# Multi-agent crew
python examples/02_crew_pipeline.py

# Parallel execution
python examples/03_parallel_tasks.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NVIDIA_API_KEY` | NVIDIA NGC API key | Required for NVIDIA |
| `OPENAI_API_KEY` | OpenAI API key | Required for OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required for Anthropic |
| `GOOGLE_API_KEY` | Google AI API key | Required for Google |
| `DEFAULT_LLM_PROVIDER` | Default provider | `nvidia` |
| `DEFAULT_MODEL` | Default model | `nvidia/nemotron-3-super-120b-a12b` |

### Python API

```python
from smith_ai import Config, get_config

config = Config(
    nvidia_api_key="your-key",
    default_provider="nvidia",
    verbose=True,
)
```

## Supported Models

### NVIDIA NIM
- nemotron-3-super-120b-a12b
- nemotron-3-ultra-405b
- llama-3.1-405b-instruct
- mixtral-8x7b-instruct

### OpenAI
- gpt-4o
- gpt-4o-mini
- gpt-4-turbo
- o1-preview
- o1-mini

### Anthropic
- claude-3-5-sonnet-20241022
- claude-3-opus-20240229
- claude-3-haiku-20240307

### Google
- gemini-2.0-flash-exp
- gemini-1.5-pro
- gemini-1.5-flash

## License

MIT License - Himan D <himanshu@open.ai>
