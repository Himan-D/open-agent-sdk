"""Skill registry - Manages skills for agent extensibility."""

from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Skill:
    """A skill that can be loaded by an agent."""
    name: str
    description: str
    instructions: str
    file_path: Optional[str] = None
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    enabled: bool = True

    def to_markdown(self) -> str:
        """Convert skill to markdown format."""
        lines = [
            f"# Skill: {self.name}",
            "",
            self.description,
            "",
            "## Instructions",
            self.instructions,
        ]
        return "\n".join(lines)


@dataclass
class SkillInvocation:
    """A skill invocation/call."""
    skill_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


class SkillRegistry:
    """Registry for managing and invoking skills."""

    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = Path(workspace_path or "~/.open-agent/skills").expanduser()
        self.skills: Dict[str, Skill] = {}
        self._skill_handlers: Dict[str, Callable] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        """Load skills from the skills directory."""
        if not self.workspace_path.exists():
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            self._create_default_skills()
            return

        for md_file in self.workspace_path.glob("*.md"):
            try:
                skill = self._parse_skill_file(md_file)
                self.skills[skill.name] = skill
                logger.info("skill_loaded", name=skill.name, path=str(md_file))
            except Exception as e:
                logger.error("skill_load_error", path=str(md_file), error=str(e))

    def _create_default_skills(self) -> None:
        """Create default skills."""
        default_skills = [
            Skill(
                name="read_file",
                description="Read the contents of a file from the filesystem.",
                instructions="Use this skill to read file contents.",
                category="filesystem",
                tags=["file", "read", "filesystem"],
            ),
            Skill(
                name="write_file",
                description="Write content to a file.",
                instructions="Use this skill to write content to a file.",
                category="filesystem",
                tags=["file", "write", "filesystem"],
            ),
            Skill(
                name="search_web",
                description="Search the web for information.",
                instructions="Use this skill to search the web.",
                category="research",
                tags=["search", "web", "research"],
            ),
            Skill(
                name="run_code",
                description="Execute Python code in a sandbox.",
                instructions="Use this skill to run Python code.",
                category="execution",
                tags=["code", "python", "execute"],
            ),
            Skill(
                name="plan_task",
                description="Break down a complex task into steps.",
                instructions="Use this skill to create a plan.",
                category="planning",
                tags=["plan", "task", "steps"],
            ),
        ]

        for skill in default_skills:
            self.skills[skill.name] = skill
            skill_path = self.workspace_path / f"{skill.name}.md"
            skill_path.write_text(skill.to_markdown())

        logger.info("default_skills_created", count=len(default_skills))

    def _parse_skill_file(self, path: Path) -> Skill:
        """Parse a skill from a markdown file."""
        content = path.read_text()
        lines = content.split("\n")

        name = path.stem
        description = ""
        instructions = ""
        category = "general"
        tags = []

        current_section = "description"
        section_content: List[str] = []

        for line in lines:
            if line.startswith("# Skill:"):
                name = line.replace("# Skill:", "").strip()
            elif line.startswith("## "):
                if section_content and current_section == "description":
                    description = "\n".join(section_content).strip()
                section_content = []
                section = line[3:].lower()
                if "instruct" in section:
                    current_section = "instructions"
                elif "category" in section:
                    current_section = "category"
                elif "tag" in section:
                    current_section = "tags"
            elif line.strip():
                section_content.append(line.strip())

        if current_section == "description" and section_content:
            description = "\n".join(section_content).strip()
        elif current_section == "instructions" and section_content:
            instructions = "\n".join(section_content).strip()

        return Skill(
            name=name,
            description=description,
            instructions=instructions,
            file_path=str(path),
            category=category,
            tags=tags,
        )

    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self.skills.get(name)

    def list(self, category: Optional[str] = None) -> List[Skill]:
        """List all skills, optionally filtered by category."""
        skills = list(self.skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        return [s for s in skills if s.enabled]

    def list_categories(self) -> List[str]:
        """List all skill categories."""
        return list(set(s.category for s in self.skills.values()))

    def register_handler(self, skill_name: str, handler: Callable) -> None:
        """Register a handler function for a skill."""
        self._skill_handlers[skill_name] = handler

    async def invoke(self, skill_name: str, arguments: Dict[str, Any]) -> SkillInvocation:
        """Invoke a skill."""
        invocation = SkillInvocation(skill_name=skill_name, arguments=arguments)

        skill = self.skills.get(skill_name)
        if not skill:
            invocation.error = f"Skill '{skill_name}' not found"
            return invocation

        handler = self._skill_handlers.get(skill_name)
        if handler:
            try:
                result = handler(**arguments)
                if hasattr(result, "__await__"):
                    invocation.result = await result
                else:
                    invocation.result = str(result)
                invocation.success = True
            except Exception as e:
                invocation.error = str(e)
        else:
            invocation.result = f"[Skill '{skill_name}' loaded but no handler registered]"
            invocation.success = True

        return invocation

    def add_skill(self, skill: Skill) -> None:
        """Add a new skill."""
        self.skills[skill.name] = skill
        if skill.file_path:
            path = Path(skill.file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(skill.to_markdown())

    def remove_skill(self, name: str) -> bool:
        """Remove a skill."""
        if name in self.skills:
            del self.skills[name]
            return True
        return False
