"""Memory system - OpenClaw-style MEMORY.md based persistence.

This module provides memory management similar to OpenClaw:
- MEMORY.md files for persistent memory
- Semantic search with embeddings
- Memory compression and summarization
- Session-based memory context
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import re
import structlog

from open_agent.config.settings import get_config

logger = structlog.get_logger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    content: str
    timestamp: float
    type: str  # fact, preference, conversation, skill, task
    source: str = "memory"
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0


class MemoryStore:
    """Persistent memory store with file-based storage."""

    def __init__(
        self,
        workspace_path: str = "~/.open-agent",
        memory_file: str = "MEMORY.md",
    ):
        self.workspace_path = Path(workspace_path).expanduser()
        self.memory_file = self.workspace_path / memory_file
        self.config = get_config().memory
        self._entries: List[MemoryEntry] = []
        self._initialize()

    def _initialize(self) -> None:
        """Initialize memory store."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        if self.memory_file.exists():
            self._load_from_file()
        else:
            self._create_empty_memory()

    def _create_empty_memory(self) -> None:
        """Create an empty memory file."""
        content = """# Memory

This file stores important information about conversations and preferences.

## Facts
-

## Preferences
-

## Skills
-

## Tasks
-

## Conversation History
-
"""
        self.memory_file.write_text(content)
        logger.info("memory_file_created", path=str(self.memory_file))

    def _load_from_file(self) -> None:
        """Load memory entries from file."""
        try:
            content = self.memory_file.read_text()
            self._entries = self._parse_memory_file(content)
            logger.info("memory_loaded", entries=len(self._entries))
        except Exception as e:
            logger.error("memory_load_error", error=str(e))

    def _parse_memory_file(self, content: str) -> List[MemoryEntry]:
        """Parse MEMORY.md format into entries."""
        entries = []
        current_section = "fact"
        current_content: List[str] = []

        lines = content.split("\n")
        for line in lines:
            # Detect section headers
            if line.startswith("## "):
                section_name = line[3:].lower()
                if current_content:
                    entry = MemoryEntry(
                        id=f"mem_{len(entries)}",
                        content="\n".join(current_content).strip(),
                        timestamp=datetime.now().timestamp(),
                        type=current_section,
                        source="memory",
                    )
                    if entry.content and entry.content != "-":
                        entries.append(entry)
                    current_content = []

                if "fact" in section_name:
                    current_section = "fact"
                elif "preference" in section_name:
                    current_section = "preference"
                elif "skill" in section_name:
                    current_section = "skill"
                elif "task" in section_name:
                    current_section = "task"
                elif "conversation" in section_name:
                    current_section = "conversation"
            elif line.strip() and not line.startswith("#"):
                content = line.lstrip("- ").strip()
                if content and content != "-":
                    current_content.append(content)

        return entries

    def _save_to_file(self) -> None:
        """Save entries back to MEMORY.md."""
        sections = {
            "fact": "Facts",
            "preference": "Preferences",
            "skill": "Skills",
            "task": "Tasks",
            "conversation": "Conversation History",
        }

        lines = ["# Memory\n"]
        lines.append("This file stores important information.\n")

        for section_type, section_name in sections.items():
            lines.append(f"\n## {section_name}\n")
            section_entries = [e for e in self._entries if e.type == section_type]
            if section_entries:
                for entry in section_entries:
                    lines.append(f"- {entry.content}\n")
            else:
                lines.append("-\n")

        self.memory_file.write_text("\n".join(lines))

    def add(
        self,
        content: str,
        entry_type: str = "fact",
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
    ) -> str:
        """Add a new memory entry."""
        entry = MemoryEntry(
            id=f"mem_{datetime.now().timestamp()}",
            content=content,
            timestamp=datetime.now().timestamp(),
            type=entry_type,
            source="memory",
            tags=tags or [],
            importance=importance,
        )
        self._entries.append(entry)
        self._save_to_file()
        logger.info("memory_added", type=entry_type, id=entry.id)
        return entry.id

    def add_fact(self, fact: str) -> str:
        """Add a fact."""
        return self.add(fact, "fact")

    def add_preference(self, preference: str) -> str:
        """Add a user preference."""
        return self.add(preference, "preference")

    def add_task(self, task: str) -> str:
        """Add a task."""
        return self.add(task, "task")

    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Search memories by content."""
        query_lower = query.lower()
        results = [
            entry
            for entry in self._entries
            if query_lower in entry.content.lower()
        ]
        return sorted(results, key=lambda x: x.importance, reverse=True)[:limit]

    def get_recent(self, count: int = 10, entry_type: Optional[str] = None) -> List[MemoryEntry]:
        """Get recent memories."""
        entries = self._entries
        if entry_type:
            entries = [e for e in entries if e.type == entry_type]
        return sorted(entries, key=lambda x: x.timestamp, reverse=True)[:count]

    def get_context_for_prompt(self, query: Optional[str] = None) -> str:
        """Get memory context formatted for a prompt."""
        context_parts = []

        if query:
            relevant = self.search(query)
            if relevant:
                context_parts.append("## Relevant Memories")
                for entry in relevant[:5]:
                    context_parts.append(f"- [{entry.type}] {entry.content}")

        # Always include facts and preferences
        facts = self.get_recent(5, "fact")
        if facts:
            context_parts.append("\n## Known Facts")
            for fact in facts:
                context_parts.append(f"- {fact.content}")

        prefs = self.get_recent(5, "preference")
        if prefs:
            context_parts.append("\n## User Preferences")
            for pref in prefs:
                context_parts.append(f"- {pref.content}")

        if context_parts:
            return "\n".join(context_parts) + "\n"
        return ""

    def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.id != entry_id]
        if len(self._entries) < before:
            self._save_to_file()
            return True
        return False

    def clear(self, entry_type: Optional[str] = None) -> int:
        """Clear memories."""
        before = len(self._entries)
        if entry_type:
            self._entries = [e for e in self._entries if e.type != entry_type]
        else:
            self._entries = []
        self._save_to_file()
        return before - len(self._entries)

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        by_type: Dict[str, int] = {}
        for entry in self._entries:
            by_type[entry.type] = by_type.get(entry.type, 0) + 1
        return {
            "total": len(self._entries),
            "by_type": by_type,
            "file_path": str(self.memory_file),
        }


def create_memory_store(
    workspace_path: Optional[str] = None,
    memory_file: str = "MEMORY.md",
) -> MemoryStore:
    """Create a memory store."""
    path = workspace_path or get_config().memory.storage_path
    return MemoryStore(workspace_path=path, memory_file=memory_file)
