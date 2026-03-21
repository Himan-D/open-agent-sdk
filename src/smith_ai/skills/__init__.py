"""SmithAI Skills System - Plugin-based skill architecture.

Skills are reusable, composable units that extend SmithAI capabilities.
Like OpenClaw, developers can publish skills to a registry.

Features:
- Skill definition with metadata, handlers, and dependencies
- Local skill registry with caching
- Remote registry sync (PyPI-like)
- Skill discovery and installation
- Version management
- Skill composition ( chaining skills)
- Learning from skill execution patterns
"""

from __future__ import annotations

import os
import sys
import json
import asyncio
import hashlib
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
import importlib.util
import zipfile
import tempfile


class SkillCategory(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    INTEGRATION = "integration"
    MEMORY = "memory"
    REASONING = "reasoning"
    BROWSER = "browser"
    DATA = "data"
    UTILITY = "utility"
    CUSTOM = "custom"


class SkillStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    BLOCKED = "blocked"


@dataclass
class SkillDependency:
    name: str
    version: str
    optional: bool = False


@dataclass
class SkillMetadata:
    name: str
    version: str
    description: str
    author: str
    category: SkillCategory
    tags: List[str] = field(default_factory=list)
    dependencies: List[SkillDependency] = field(default_factory=list)
    skills_required: List[str] = field(default_factory=list)
    min_smithai_version: str = "4.0.0"
    license: str = "MIT"
    homepage: str = ""
    repository: str = ""
    keywords: List[str] = field(default_factory=list)
    published_at: Optional[datetime] = None
    downloads: int = 0
    rating: float = 0.0


@dataclass
class SkillHandler:
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None
    async_handler: Optional[Callable] = None


@dataclass
class SkillEvent:
    timestamp: datetime
    event_type: str
    skill_name: str
    handler: str
    success: bool
    duration_ms: float
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Any = None
    error: Optional[str] = None


@dataclass
class SkillExecutionResult:
    skill_name: str
    handler: str
    success: bool
    result: Any
    duration_ms: float
    cached: bool = False
    events: List[SkillEvent] = field(default_factory=list)
    error: Optional[str] = None


class Skill(ABC):
    """Base class for all skills.
    
    Skills extend SmithAI by providing:
    - Handlers (functions that can be called)
    - Initialization logic
    - Cleanup logic
    - Dependencies
    """
    
    metadata: SkillMetadata
    handlers: Dict[str, SkillHandler] = {}
    
    def __init__(self):
        self._initialized = False
        self._state: Dict[str, Any] = {}
    
    @abstractmethod
    def setup(self) -> None:
        """Initialize the skill. Called when skill is loaded."""
        pass
    
    @abstractmethod
    def teardown(self) -> None:
        """Cleanup the skill. Called when skill is unloaded."""
        pass
    
    def get_handler(self, name: str) -> Optional[SkillHandler]:
        """Get a handler by name."""
        return self.handlers.get(name)
    
    def get_all_handlers(self) -> List[SkillHandler]:
        """Get all handlers."""
        return list(self.handlers.values())
    
    def save_state(self) -> Dict[str, Any]:
        """Save skill state for persistence."""
        return self._state.copy()
    
    def load_state(self, state: Dict[str, Any]) -> None:
        """Load skill state from persistence."""
        self._state = state.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert skill to dictionary."""
        return {
            "metadata": asdict(self.metadata) if self.metadata else {},
            "handlers": [asdict(h) for h in self.handlers.values()],
            "state": self._state,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Create skill from dictionary."""
        # This should be overridden by subclasses
        raise NotImplementedError


class SkillRegistry:
    """Local registry for skills.
    
    Manages:
    - Installed skills
    - Skill versions
    - Skill states
    - Skill dependencies
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            storage_path = os.path.expanduser("~/.smithai/skills")
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._skills: Dict[str, Skill] = {}
        self._metadata: Dict[str, SkillMetadata] = {}
        self._states: Dict[str, Dict[str, Any]] = {}
        self._execution_history: List[SkillEvent] = []
        self._learned_patterns: Dict[str, Any] = {}
        
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load registry from disk."""
        registry_file = self.storage_path / "registry.json"
        if registry_file.exists():
            try:
                with open(registry_file) as f:
                    data = json.load(f)
                    self._metadata = {
                        k: SkillMetadata(**v) for k, v in data.get("metadata", {}).items()
                    }
                    self._states = data.get("states", {})
                    self._learned_patterns = data.get("learned_patterns", {})
            except Exception:
                pass
    
    def _save_registry(self) -> None:
        """Save registry to disk."""
        registry_file = self.storage_path / "registry.json"
        data = {
            "metadata": {k: asdict(v) for k, v in self._metadata.items()},
            "states": self._states,
            "learned_patterns": self._learned_patterns,
        }
        with open(registry_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def register(self, skill: Skill) -> bool:
        """Register a skill."""
        try:
            name = skill.metadata.name
            version = skill.metadata.version
            
            # Check for existing version
            if name in self._metadata:
                existing = self._metadata[name]
                if self._compare_versions(version, existing.version) <= 0:
                    return False  # Don't downgrade
            
            # Initialize skill
            skill.setup()
            skill._initialized = True
            
            # Load saved state
            if name in self._states:
                skill.load_state(self._states[name])
            
            # Register
            self._skills[name] = skill
            self._metadata[name] = skill.metadata
            self._save_registry()
            
            return True
        except Exception as e:
            return False
    
    def unregister(self, name: str) -> bool:
        """Unregister a skill."""
        if name in self._skills:
            skill = self._skills[name]
            skill.teardown()
            
            # Save state before removing
            self._states[name] = skill.save_state()
            
            del self._skills[name]
            if name in self._metadata:
                del self._metadata[name]
            
            self._save_registry()
            return True
        return False
    
    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(name)
    
    def get_metadata(self, name: str) -> Optional[SkillMetadata]:
        """Get skill metadata."""
        return self._metadata.get(name)
    
    def list_all(self) -> List[str]:
        """List all registered skill names."""
        return list(self._skills.keys())
    
    def list_by_category(self, category: SkillCategory) -> List[str]:
        """List skills by category."""
        return [
            name for name, meta in self._metadata.items()
            if meta.category == category
        ]
    
    async def execute(
        self,
        skill_name: str,
        handler: str,
        **kwargs: Any
    ) -> SkillExecutionResult:
        """Execute a skill handler."""
        start_time = datetime.now()
        event = SkillEvent(
            timestamp=start_time,
            event_type="execute",
            skill_name=skill_name,
            handler=handler,
            success=False,
            duration_ms=0,
            input_data=kwargs,
        )
        
        skill = self.get(skill_name)
        if not skill:
            event.error = f"Skill not found: {skill_name}"
            self._execution_history.append(event)
            return SkillExecutionResult(
                skill_name=skill_name,
                handler=handler,
                success=False,
                result=None,
                duration_ms=0,
                events=[event],
            )
        
        skill_handler = skill.get_handler(handler)
        if not skill_handler:
            event.error = f"Handler not found: {handler}"
            self._execution_history.append(event)
            return SkillExecutionResult(
                skill_name=skill_name,
                handler=handler,
                success=False,
                result=None,
                duration_ms=0,
                events=[event],
            )
        
        try:
            # Execute handler
            if skill_handler.async_handler:
                result = await skill_handler.async_handler(**kwargs)
            elif skill_handler.handler:
                result = skill_handler.handler(**kwargs)
            else:
                result = None
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            event.success = True
            event.duration_ms = duration_ms
            event.output_data = result
            
            # Learn from execution
            self._learn_pattern(skill_name, handler, kwargs, result, True)
            
            self._execution_history.append(event)
            self._save_registry()
            
            return SkillExecutionResult(
                skill_name=skill_name,
                handler=handler,
                success=True,
                result=result,
                duration_ms=duration_ms,
                events=[event],
            )
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            event.success = False
            event.duration_ms = duration_ms
            event.error = str(e)
            
            self._learn_pattern(skill_name, handler, kwargs, None, False)
            self._execution_history.append(event)
            
            return SkillExecutionResult(
                skill_name=skill_name,
                handler=handler,
                success=False,
                result=None,
                duration_ms=duration_ms,
                error=str(e),
                events=[event],
            )
    
    def _learn_pattern(
        self,
        skill_name: str,
        handler: str,
        inputs: Dict[str, Any],
        result: Any,
        success: bool
    ) -> None:
        """Learn from skill execution patterns."""
        pattern_key = f"{skill_name}.{handler}"
        
        if pattern_key not in self._learned_patterns:
            self._learned_patterns[pattern_key] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "avg_duration_ms": 0,
                "common_inputs": [],
                "output_types": [],
            }
        
        pattern = self._learned_patterns[pattern_key]
        pattern["total_executions"] += 1
        if success:
            pattern["successful_executions"] += 1
        else:
            pattern["failed_executions"] += 1
        
        # Track output type
        output_type = type(result).__name__ if result is not None else "None"
        if output_type not in pattern["output_types"]:
            pattern["output_types"].append(output_type)
    
    def get_learned_patterns(self, skill_name: Optional[str] = None) -> Dict[str, Any]:
        """Get learned patterns."""
        if skill_name:
            return {
                k: v for k, v in self._learned_patterns.items()
                if k.startswith(f"{skill_name}.")
            }
        return self._learned_patterns.copy()
    
    def suggest_next_handler(
        self,
        skill_name: str,
        current_handler: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Suggest next handler based on learned patterns."""
        patterns = self.get_learned_patterns(skill_name)
        
        # Find handlers that commonly follow current handler
        suggestions = []
        for key, pattern in patterns.items():
            if key.endswith(f".{current_handler}"):
                continue
            
            success_rate = (
                pattern["successful_executions"] / pattern["total_executions"]
                if pattern["total_executions"] > 0 else 0
            )
            suggestions.append((key.split(".")[1], success_rate))
        
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        if suggestions:
            return suggestions[0][0]
        return None
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare semantic versions. Returns -1, 0, or 1."""
        def parse(v: str) -> List[int]:
            return [int(x) for x in v.split(".")[:3]]
        
        p1, p2 = parse(v1), parse(v2)
        for i, j in zip(p1, p2):
            if i < j:
                return -1
            elif i > j:
                return 1
        return 0
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        total = len(self._execution_history)
        successful = sum(1 for e in self._execution_history if e.success)
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "skills_count": len(self._skills),
            "learned_patterns": len(self._learned_patterns),
        }


class RemoteSkillRegistry:
    """Remote registry for syncing skills.
    
    Simulates a registry server (like npm/PyPI).
    In production, this would connect to a real server.
    """
    
    def __init__(self, base_url: str = "https://registry.smithai.dev"):
        self.base_url = base_url
        self._cache: Dict[str, SkillMetadata] = {}
        self._sync_interval = 3600  # 1 hour
        self._last_sync: Optional[datetime] = None
    
    async def search(
        self,
        query: str,
        category: Optional[SkillCategory] = None,
        limit: int = 20
    ) -> List[SkillMetadata]:
        """Search for skills in the registry."""
        # Simulated search - in production would hit API
        results = []
        query_lower = query.lower()
        
        for meta in self._cache.values():
            if query_lower in meta.name.lower() or query_lower in meta.description.lower():
                if category is None or meta.category == category:
                    results.append(meta)
                    if len(results) >= limit:
                        break
        
        return results
    
    async def get_metadata(self, name: str) -> Optional[SkillMetadata]:
        """Get skill metadata from registry."""
        return self._cache.get(name)
    
    async def publish(self, skill: Skill, api_key: Optional[str] = None) -> bool:
        """Publish a skill to the registry."""
        # In production, would upload to server
        skill.metadata.status = SkillStatus.PUBLISHED
        skill.metadata.published_at = datetime.now()
        self._cache[skill.metadata.name] = skill.metadata
        return True
    
    async def download(self, name: str, version: str = "latest") -> Optional[bytes]:
        """Download a skill package."""
        # In production, would download from server
        return None
    
    async def sync(self) -> int:
        """Sync with remote registry."""
        # In production, would fetch latest from server
        self._last_sync = datetime.now()
        return len(self._cache)


class SkillLoader:
    """Loads skills from various sources."""
    
    @staticmethod
    def from_file(path: str) -> Skill:
        """Load skill from Python file."""
        spec = importlib.util.spec_from_file_location("skill", path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find skill class in module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Skill) and attr != Skill:
                    return attr()
        
        raise ValueError(f"No skill class found in {path}")
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Skill:
        """Load skill from dictionary."""
        metadata = SkillMetadata(**data.get("metadata", {}))
        
        # Create skill instance based on category
        category = metadata.category
        
        skill = SimpleSkill(metadata)
        
        # Load handlers
        for handler_data in data.get("handlers", []):
            skill.add_handler(
                name=handler_data["name"],
                description=handler_data.get("description", ""),
                handler=handler_data.get("handler"),
                async_handler=handler_data.get("async_handler"),
            )
        
        return skill
    
    @staticmethod
    def from_package(data: bytes) -> Skill:
        """Load skill from package (zip)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "skill.zip"
            with open(zip_path, "wb") as f:
                f.write(data)
            
            with zipfile.ZipFile(zip_path) as zf:
                # Extract manifest
                manifest = json.loads(zf.read("manifest.json"))
                
                # Extract code files
                code_files = {}
                for name in zf.namelist():
                    if name.startswith("code/"):
                        code_files[name[5:]] = zf.read(name).decode()
                
                return SkillLoader.from_dict({
                    "metadata": manifest,
                    "code": code_files,
                })


class SimpleSkill(Skill):
    """A simple skill implementation for easy creation."""
    
    def __init__(self, metadata: SkillMetadata):
        self.metadata = metadata
        self.handlers: Dict[str, SkillHandler] = {}
        self._initialized = False
        self._state: Dict[str, Any] = {}
    
    def setup(self) -> None:
        """Setup the skill."""
        pass
    
    def teardown(self) -> None:
        """Teardown the skill."""
        pass
    
    def add_handler(
        self,
        name: str,
        description: str = "",
        handler: Optional[Callable] = None,
        async_handler: Optional[Callable] = None,
    ) -> None:
        """Add a handler to the skill."""
        self.handlers[name] = SkillHandler(
            name=name,
            description=description,
            handler=handler,
            async_handler=async_handler,
        )


class SkillComposer:
    """Composes multiple skills into pipelines."""
    
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self._pipelines: Dict[str, List[Tuple[str, str]]] = {}
    
    def create_pipeline(
        self,
        name: str,
        steps: List[Tuple[str, str]]
    ) -> None:
        """Create a pipeline of skill handlers."""
        self._pipelines[name] = steps
    
    async def execute_pipeline(
        self,
        name: str,
        initial_input: Any,
        **kwargs: Any
    ) -> Any:
        """Execute a pipeline."""
        if name not in self._pipelines:
            raise ValueError(f"Pipeline not found: {name}")
        
        result = initial_input
        context = kwargs.copy()
        
        for skill_name, handler in self._pipelines[name]:
            exec_result = await self.registry.execute(
                skill_name,
                handler,
                input=result,
                **context
            )
            
            if not exec_result.success:
                raise RuntimeError(
                    f"Pipeline failed at {skill_name}.{handler}: {exec_result.error}"
                )
            
            result = exec_result.result
            context[f"previous_result"] = result
        
        return result
    
    def list_pipelines(self) -> List[str]:
        """List all pipelines."""
        return list(self._pipelines.keys())


class SkillManager:
    """High-level skill management."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.registry = SkillRegistry(storage_path)
        self.remote = RemoteSkillRegistry()
        self.loader = SkillLoader()
        self.composer = SkillComposer(self.registry)
    
    async def install(
        self,
        name: str,
        version: str = "latest",
        source: str = "local"
    ) -> bool:
        """Install a skill."""
        if source == "local":
            skill_path = Path(self.registry.storage_path) / f"{name}.json"
            if skill_path.exists():
                with open(skill_path) as f:
                    data = json.load(f)
                    skill = self.loader.from_dict(data)
                    return self.registry.register(skill)
        elif source == "remote":
            meta = await self.remote.get_metadata(name)
            if meta:
                # Download and install
                package = await self.remote.download(name, version)
                if package:
                    skill = self.loader.from_package(package)
                    return self.registry.register(skill)
        
        return False
    
    async def uninstall(self, name: str) -> bool:
        """Uninstall a skill."""
        return self.registry.unregister(name)
    
    async def update(self, name: str) -> bool:
        """Update a skill to latest version."""
        await self.remote.sync()
        meta = await self.remote.get_metadata(name)
        if meta:
            return await self.install(name, meta.version, "remote")
        return False
    
    async def publish(
        self,
        skill: Skill,
        api_key: Optional[str] = None
    ) -> bool:
        """Publish a skill to remote registry."""
        return await self.remote.publish(skill, api_key)
    
    async def search(
        self,
        query: str,
        category: Optional[SkillCategory] = None
    ) -> List[SkillMetadata]:
        """Search for skills."""
        await self.remote.sync()
        return await self.remote.search(query, category)
    
    def create_skill(
        self,
        name: str,
        version: str,
        description: str,
        author: str,
        category: SkillCategory,
        handlers: Dict[str, Tuple[str, Callable]],
    ) -> Skill:
        """Create a new skill programmatically."""
        metadata = SkillMetadata(
            name=name,
            version=version,
            description=description,
            author=author,
            category=category,
        )
        
        skill = SimpleSkill(metadata)
        for handler_name, (desc, func) in handlers.items():
            skill.add_handler(
                name=handler_name,
                description=desc,
                handler=func if not asyncio.iscoroutinefunction(func) else None,
                async_handler=func if asyncio.iscoroutinefunction(func) else None,
            )
        
        return skill
    
    def export_skill(self, name: str, path: str) -> bool:
        """Export a skill to a file."""
        skill = self.registry.get(name)
        if not skill:
            return False
        
        data = skill.to_dict()
        export_path = Path(path)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(export_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        return True
    
    def import_skill(self, path: str) -> bool:
        """Import a skill from a file."""
        with open(path) as f:
            data = json.load(f)
        
        skill = self.loader.from_dict(data)
        return self.registry.register(skill)


# Built-in skills

def create_calculator_skill() -> Skill:
    """Create the calculator skill."""
    metadata = SkillMetadata(
        name="calculator",
        version="1.0.0",
        description="Mathematical expression evaluator",
        author="SmithAI",
        category=SkillCategory.TOOL,
        tags=["math", "calculator"],
    )
    
    skill = SimpleSkill(metadata)
    
    def evaluate(expression: str) -> str:
        """Evaluate a mathematical expression."""
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"Error: {e}"
    
    skill.add_handler(
        name="evaluate",
        description="Evaluate a mathematical expression",
        handler=evaluate,
    )
    
    skill.add_handler(
        name="calculate",
        description="Calculate with given numbers",
        async_handler=lambda a, b, operation="add": _calculate(a, b, operation),
    )
    
    return skill


async def _calculate(a: float, b: float, operation: str = "add") -> float:
    """Async calculate helper."""
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else 0,
        "power": a ** b,
    }
    return operations.get(operation, 0)


def create_researcher_skill() -> Skill:
    """Create the researcher skill."""
    metadata = SkillMetadata(
        name="researcher",
        version="1.0.0",
        description="Research and analyze topics",
        author="SmithAI",
        category=SkillCategory.AGENT,
        tags=["research", "analysis", "agent"],
    )
    
    skill = SimpleSkill(metadata)
    
    async def research(topic: str, depth: int = 1) -> Dict[str, Any]:
        """Research a topic."""
        return {
            "topic": topic,
            "depth": depth,
            "findings": [
                f"Finding 1 about {topic}",
                f"Finding 2 about {topic}",
            ],
            "summary": f"Summary of research on {topic}",
        }
    
    async def analyze(text: str, analysis_type: str = "basic") -> Dict[str, Any]:
        """Analyze text."""
        return {
            "text": text,
            "type": analysis_type,
            "word_count": len(text.split()),
            "sentiment": "neutral",
        }
    
    skill.add_handler(
        name="research",
        description="Research a topic",
        async_handler=research,
    )
    
    skill.add_handler(
        name="analyze",
        description="Analyze text",
        async_handler=analyze,
    )
    
    return skill


def create_memory_skill() -> Skill:
    """Create the memory skill."""
    metadata = SkillMetadata(
        name="memory",
        version="1.0.0",
        description="Persistent memory storage",
        author="SmithAI",
        category=SkillCategory.MEMORY,
        tags=["memory", "storage", "persistence"],
    )
    
    skill = SimpleSkill(metadata)
    _memory_store: Dict[str, Any] = {}
    
    def store(key: str, value: Any) -> str:
        """Store a value."""
        _memory_store[key] = value
        return f"Stored: {key}"
    
    def retrieve(key: str) -> Any:
        """Retrieve a value."""
        return _memory_store.get(key, None)
    
    def list_keys() -> List[str]:
        """List all keys."""
        return list(_memory_store.keys())
    
    def delete(key: str) -> bool:
        """Delete a key."""
        if key in _memory_store:
            del _memory_store[key]
            return True
        return False
    
    skill.add_handler(name="store", description="Store a value", handler=store)
    skill.add_handler(name="retrieve", description="Retrieve a value", handler=retrieve)
    skill.add_handler(name="list_keys", description="List all keys", handler=list_keys)
    skill.add_handler(name="delete", description="Delete a key", handler=delete)
    
    return skill


def create_text_skill() -> Skill:
    """Create the text processing skill."""
    metadata = SkillMetadata(
        name="text_processor",
        version="1.0.0",
        description="Text processing utilities",
        author="SmithAI",
        category=SkillCategory.UTILITY,
        tags=["text", "nlp", "processing"],
    )
    
    skill = SimpleSkill(metadata)
    
    def count_words(text: str) -> int:
        return len(text.split())
    
    def count_chars(text: str) -> int:
        return len(text)
    
    def reverse_text(text: str) -> str:
        return text[::-1]
    
    def capitalize(text: str) -> str:
        return text.upper()
    
    def sentiment(text: str) -> Dict[str, Any]:
        positive = sum(1 for w in ["good", "great", "excellent", "love", "amazing"] if w in text.lower())
        negative = sum(1 for w in ["bad", "terrible", "hate", "awful", "worst"] if w in text.lower())
        return {
            "positive": positive,
            "negative": negative,
            "sentiment": "positive" if positive > negative else "negative" if negative > positive else "neutral",
        }
    
    skill.add_handler(name="count_words", description="Count words", handler=count_words)
    skill.add_handler(name="count_chars", description="Count characters", handler=count_chars)
    skill.add_handler(name="reverse", description="Reverse text", handler=reverse_text)
    skill.add_handler(name="capitalize", description="Capitalize text", handler=capitalize)
    skill.add_handler(name="sentiment", description="Analyze sentiment", handler=sentiment)
    
    return skill


def register_builtin_skills(registry: SkillRegistry) -> None:
    """Register all built-in skills."""
    skills = [
        create_calculator_skill(),
        create_researcher_skill(),
        create_memory_skill(),
        create_text_skill(),
    ]
    
    for skill in skills:
        registry.register(skill)


# CLI for skill management

class SkillCLI:
    """Command-line interface for skill management."""
    
    def __init__(self, manager: SkillManager):
        self.manager = manager
    
    def run(self, args: List[str]) -> None:
        """Run CLI command."""
        if not args:
            self.help()
            return
        
        command = args[0]
        
        if command == "list":
            self.list_skills(args[1:])
        elif command == "install":
            self.install_skill(args[1:])
        elif command == "uninstall":
            self.uninstall_skill(args[1:])
        elif command == "search":
            self.search_skills(args[1:])
        elif command == "publish":
            self.publish_skill(args[1:])
        elif command == "info":
            self.skill_info(args[1:])
        elif command == "export":
            self.export_skill(args[1:])
        elif command == "import":
            self.import_skill(args[1:])
        elif command == "run":
            self.run_skill(args[1:])
        elif command in ("help", "--help", "-h"):
            self.help()
        else:
            print(f"Unknown command: {command}")
            self.help()
    
    def help(self) -> None:
        """Show help."""
        print("""
SmithAI Skill CLI

Commands:
  list                       List installed skills
  install <name> [source]     Install a skill
  uninstall <name>           Uninstall a skill
  search <query>             Search for skills
  publish <path>             Publish a skill
  info <name>                Show skill information
  export <name> <path>       Export a skill
  import <path>              Import a skill
  run <name>.<handler>       Run a skill handler
  help                       Show this help

Examples:
  smithai-skill list
  smithai-skill install calculator
  smithai-skill search research
  smithai-skill run calculator.evaluate --expression "2+2"
""")
    
    def list_skills(self, args: List[str]) -> None:
        """List installed skills."""
        skills = self.manager.registry.list_all()
        if not skills:
            print("No skills installed.")
            return
        
        print(f"Installed skills ({len(skills)}):")
        for name in skills:
            meta = self.manager.registry.get_metadata(name)
            if meta:
                print(f"  {meta.name}@{meta.version} [{meta.category.value}]")
    
    def install_skill(self, args: List[str]) -> None:
        """Install a skill."""
        if not args:
            print("Usage: install <name> [source]")
            return
        
        name = args[0]
        source = args[1] if len(args) > 1 else "local"
        
        print(f"Installing {name} from {source}...")
        success = asyncio.run(self.manager.install(name, source=source))
        
        if success:
            print(f"✓ Installed {name}")
        else:
            print(f"✗ Failed to install {name}")
    
    def uninstall_skill(self, args: List[str]) -> None:
        """Uninstall a skill."""
        if not args:
            print("Usage: uninstall <name>")
            return
        
        name = args[0]
        success = asyncio.run(self.manager.uninstall(name))
        
        if success:
            print(f"✓ Uninstalled {name}")
        else:
            print(f"✗ Failed to uninstall {name}")
    
    async def _search(self, args: List[str]) -> None:
        """Search for skills."""
        if not args:
            print("Usage: search <query>")
            return
        
        query = " ".join(args)
        results = await self.manager.search(query)
        
        if not results:
            print(f"No skills found for '{query}'")
            return
        
        print(f"Found {len(results)} skills:")
        for meta in results:
            print(f"  {meta.name}@{meta.version} - {meta.description}")
    
    def search_skills(self, args: List[str]) -> None:
        asyncio.run(self._search(args))
    
    async def _publish(self, args: List[str]) -> None:
        """Publish a skill."""
        if not args:
            print("Usage: publish <path> [api_key]")
            return
        
        path = args[0]
        api_key = args[1] if len(args) > 1 else None
        
        with open(path) as f:
            data = json.load(f)
        
        skill = self.manager.loader.from_dict(data)
        success = await self.manager.publish(skill, api_key)
        
        if success:
            print(f"✓ Published {skill.metadata.name}")
        else:
            print(f"✗ Failed to publish")
    
    def publish_skill(self, args: List[str]) -> None:
        asyncio.run(self._publish(args))
    
    def skill_info(self, args: List[str]) -> None:
        """Show skill information."""
        if not args:
            print("Usage: info <name>")
            return
        
        name = args[0]
        meta = self.manager.registry.get_metadata(name)
        
        if not meta:
            print(f"Skill not found: {name}")
            return
        
        print(f"""
Name: {meta.name}
Version: {meta.version}
Description: {meta.description}
Author: {meta.author}
Category: {meta.category.value}
Tags: {', '.join(meta.tags)}
License: {meta.license}
Downloads: {meta.downloads}
Rating: {meta.rating}
""")
        
        skill = self.manager.registry.get(name)
        if skill:
            print("Handlers:")
            for handler in skill.get_all_handlers():
                print(f"  - {handler.name}: {handler.description}")
    
    def export_skill(self, args: List[str]) -> None:
        """Export a skill."""
        if len(args) < 2:
            print("Usage: export <name> <path>")
            return
        
        name, path = args[0], args[1]
        success = self.manager.export_skill(name, path)
        
        if success:
            print(f"✓ Exported {name} to {path}")
        else:
            print(f"✗ Failed to export {name}")
    
    def import_skill(self, args: List[str]) -> None:
        """Import a skill."""
        if not args:
            print("Usage: import <path>")
            return
        
        path = args[0]
        success = self.manager.import_skill(path)
        
        if success:
            print(f"✓ Imported skill from {path}")
        else:
            print(f"✗ Failed to import")
    
    async def _run(self, args: List[str]) -> None:
        """Run a skill handler."""
        if not args:
            print("Usage: run <name>.<handler> [args...]")
            return
        
        parts = args[0].split(".")
        if len(parts) != 2:
            print("Usage: run <name>.<handler> [args...]")
            return
        
        name, handler = parts
        params = {}
        
        for arg in args[1:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                try:
                    params[key] = json.loads(value)
                except:
                    params[key] = value
        
        result = await self.manager.registry.execute(name, handler, **params)
        
        if result.success:
            print(f"Result: {result.result}")
        else:
            print(f"Error: {result.error}")
    
    def run_skill(self, args: List[str]) -> None:
        asyncio.run(self._run(args))


__all__ = [
    "Skill",
    "SkillCategory",
    "SkillStatus",
    "SkillMetadata",
    "SkillDependency",
    "SkillHandler",
    "SkillEvent",
    "SkillRegistry",
    "RemoteSkillRegistry",
    "SkillLoader",
    "SkillManager",
    "SkillComposer",
    "SkillCLI",
    "SimpleSkill",
    "create_calculator_skill",
    "create_researcher_skill",
    "create_memory_skill",
    "create_text_skill",
    "register_builtin_skills",
]
