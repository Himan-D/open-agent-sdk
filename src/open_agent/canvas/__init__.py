"""Canvas module - Interactive code editing workspace.

This module provides canvas functionality similar to OpenClaw:
- Interactive code editing
- Multi-file workspace
- Syntax highlighting
- Code execution
"""

from open_agent.canvas.workspace import Canvas, CanvasFile, CanvasSession, create_canvas

__all__ = [
    "Canvas",
    "CanvasFile",
    "CanvasSession",
    "create_canvas",
]
