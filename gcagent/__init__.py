"""GCagent.ai skill framework.

Declarative capability manifest plus helpers to render system prompts and
route tasks to the appropriate core skill or pluggable skill module.
"""

from .capabilities import (
    Skill,
    SkillModule,
    SkillRegistry,
    load_registry,
    render_system_prompt,
)

__all__ = [
    "Skill",
    "SkillModule",
    "SkillRegistry",
    "load_registry",
    "render_system_prompt",
]
