# SmithAI

Production-ready Python AI Agent Framework with NVIDIA Nemotron, Voice, Canvas, Browser Sandbox, and Multi-Channel Support.

## Features

- **NVIDIA Nemotron** - Advanced reasoning with LangChain integration
- **Voice** - Text-to-Speech and Speech-to-Text
- **Canvas** - Interactive code workspace with Python/JS execution
- **Browser Sandbox** - Playwright-based web automation
- **Multi-Channel** - WhatsApp, Signal, IRC, Matrix, Nostr, and more
- **Memory** - Persistent storage with MEMORY.md-style interface
- **Skills** - Markdown-based skill registry system
- **Gateway** - Message routing and session management
- **TUI** - Terminal user interface included

## Installation

```bash
pip install smith-ai
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
pip install smith-ai[voice]

# Browser automation
pip install smith-ai[browser]

# All extras
pip install smith-ai[all]
```

## Core Modules

| Module | Description |
|--------|-------------|
| `agents` | DeepAgent runtime with tool orchestration |
| `canvas` | Interactive code execution workspace |
| `channels` | Multi-platform messaging adapters |
| `gateway` | Routing, sessions, and auth |
| `memory` | Persistent knowledge storage |
| `sandbox` | Browser automation |
| `voice` | TTS/STT capabilities |

## License

MIT License - Himan D <himanshu@open.ai>
