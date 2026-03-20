# OpenAgent

Multi-model AI agent orchestration framework with LangChain Deep Agents, NVIDIA OpenShell, and Nemotron.

## Features

- **NVIDIA Nemotron** - Advanced reasoning models
- **OpenShell** - Secure sandboxed execution
- **Deep Agents** - Planning, memory, tools, subagents
- **OpenClaw-style** - Gateway, sessions, multi-agent

## Installation

```bash
pip install -e .
export NVIDIA_API_KEY=your_key
```

## Quick Start

```python
from open_agent import create_deep_agent

agent = create_deep_agent(name="assistant")
await agent.initialize()
response = await agent.process_message("Hello!")
```
