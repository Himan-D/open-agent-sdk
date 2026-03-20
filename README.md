# SmithAI

**Production AI Agent Framework - CrewAI-style Multi-Agent Orchestration with Full Browser Automation**

Built with NVIDIA Nemotron, OpenAI, Anthropic, Google Gemini + Complete Browser Automation.

## Features

### 🤖 Multi-Agent System
- **Crew Orchestration** - Sequential, Parallel, Hierarchical execution
- **Subagent Spawning** - Agents can delegate to specialized subagents
- **Context Passing** - Tasks share context between agents
- **Role-Based Agents** - Define agents with roles, goals, backstories

### 🌐 Browser Automation (Browserbase-like)
- **Full DOM Manipulation** - Click, hover, scroll, drag
- **Form Handling** - Fill, submit, select options
- **Web Scraping** - Extract data with CSS selectors
- **Screenshot & PDF** - Capture pages
- **JavaScript Execution** - Run custom JS in browser

### 🛠️ Tool System
- **Modular Tools** - Create custom tools with `@tool` decorator
- **Tool Registry** - Dynamic tool registration
- **20+ Built-in Tools** - Calculator, web search, file ops, code execution

### 💻 Multi-LLM Support
- **NVIDIA Nemotron** (recommended)
- **OpenAI GPT-4/4o**
- **Anthropic Claude**
- **Google Gemini**
- **Ollama** (local)

## Quick Start

```bash
pip install smith-ai
```

### Basic Agent
```python
import asyncio
from open_agent import create_agent

async def main():
    agent = await create_agent(
        name="assistant",
        role="AI Assistant",
        goal="Help users",
        provider="nvidia"  # or "openai", "anthropic", "google"
    )
    result = await agent.execute("What is 2+2?")
    print(result)

asyncio.run(main())
```

### Multi-Agent Crew
```python
from open_agent import create_crew, Task

crew = create_crew(
    agents_config=[
        {"name": "researcher", "role": "Researcher", "goal": "Research", "backstory": "..."},
        {"name": "writer", "role": "Writer", "goal": "Write", "backstory": "..."},
    ],
    tasks_config=[
        {"description": "Research AI trends", "agent": "researcher"},
        {"description": "Write article", "agent": "writer"},
    ],
    process="sequential"
)

results = await crew.kickoff()
```

### Browser Automation
```python
from open_agent.automation.browser import BrowserTool

browser = BrowserTool()

# Navigate
await browser.execute("navigate:https://github.com")

# Fill form
await browser.execute("fill:input[name='q']|search term")

# Click
await browser.execute("click:button[type='submit']")

# Screenshot
await browser.execute("screenshot:mypage.png")

# Scrape
await browser.execute("scrape:https://example.com|h1,p,a")
```

### Custom Tools
```python
from open_agent import tool, ToolRegistry

@tool(name="my_tool", description="Does something")
def my_function(input: str) -> str:
    return f"Processed: {input}"

registry = ToolRegistry.get_instance()
registry.register(my_function)
```

## Browser Commands

| Command | Description |
|---------|-------------|
| `navigate:<url>` | Go to URL |
| `click:<selector>` | Click element |
| `fill:<selector>\|<text>` | Fill input |
| `type:<selector>\|<text>` | Type with delay |
| `select:<selector>\|<value>` | Select dropdown |
| `screenshot` | Take screenshot |
| `content` | Get HTML |
| `text:<selector>` | Get element text |
| `scrape:<selector>` | Scrape elements |
| `evaluate:<js>` | Run JavaScript |
| `wait:<seconds>` | Wait |
| `screenshot:<path>` | Save screenshot |
| `click:<selector>` | Click element |
| `hover:<selector>` | Hover element |
| `scroll:<selector>` | Scroll to element |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Crew                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │ Agent 1 │→ │ Agent 2 │→ │ Agent 3 │             │
│  └─────────┘  └─────────┘  └─────────┘             │
│       ↓            ↓            ↓                       │
│  ┌─────────────────────────────────────────┐       │
│  │           LLM Layer                        │       │
│  │  NVIDIA │ OpenAI │ Anthropic │ Google   │       │
│  └─────────────────────────────────────────┘       │
│       ↓            ↓            ↓                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ Browser  │  │  Tools   │  │ Memory  │         │
│  │ (Playwright)│ │ Registry │  │ Storage │         │
│  └─────────┘  └─────────┘  └─────────┘         │
└─────────────────────────────────────────────────────┘
```

## Examples

```bash
# Test LLM providers
python examples/04_test_llms.py

# Basic agent
python examples/01_basic_agent.py

# Multi-agent crew
python examples/02_crew_pipeline.py

# Browser automation
python examples/browser_demo.py
```

## Installation

```bash
pip install smith-ai
pip install smith-ai[browser]  # With browser automation
pip install smith-ai[all]     # All extras
```

## Environment Variables

```bash
export NVIDIA_API_KEY=your_nvidia_key     # Recommended
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key
export GOOGLE_API_KEY=your_google_key
```

## License

MIT License - Himan D <himanshu@open.ai>
