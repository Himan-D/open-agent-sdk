"""Skills module - Loadable agent capabilities from markdown files.

This module provides a skills system similar to OpenClaw:
- Skills defined in markdown files
- Automatic skill loading from workspace
- Skill invocation and context
- Skill discovery and management
"""

from open_agent.agents.skills.registry import Skill, SkillRegistry, SkillInvocation

__all__ = [
    "Skill",
    "SkillRegistry", 
    "SkillInvocation",
]
