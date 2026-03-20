# OpenAgent SDK

OpenClaw-inspired AI Agent Framework with NVIDIA Nemotron, Voice, Canvas, Browser Sandbox, and Multi-Channel Support.

## Features

- **NVIDIA Nemotron** - Advanced reasoning with LangChain integration
- **Voice** - Text-to-Speech and Speech-to-Text
- **Canvas** - Interactive code workspace with execution
- **Browser Sandbox** - Playwright-based web automation
- **Multi-Channel** - WhatsApp, Signal, IRC, Matrix, Nostr, and more
- **Memory** - Persistent MEMORY.md-style storage
- **Skills** - Markdown-based skill system
- **TUI** - Terminal user interface included

## Installation

```bash
pip install open-agent-sdk
```

## Quick Start

```python
from open_agent import create_deep_agent

agent = create_deep_agent(name="assistant")
await agent.initialize()
response = await agent.process_message("Hello!")
print(response)
```

## Environment Variables

```bash
export NVIDIA_API_KEY=your_nvidia_api_key
```

## Optional Dependencies

```bash
# Voice support
pip install open-agent-sdk[voice]

# Browser automation
pip install open-agent-sdk[browser]

# All extras
pip install open-agent-sdk[all]
```

## License

MIT License - Himan D <himanshu@open.ai>
