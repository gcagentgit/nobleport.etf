"""Skill registry for GCagent.ai.

Loads the declarative manifest in `skills.yaml` and exposes typed accessors
plus a system-prompt renderer. Intentionally dependency-light: falls back to a
minimal YAML parser shim if PyYAML is unavailable, so this module can be
imported in sandboxed environments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:  # pragma: no cover - optional dep
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


MANIFEST_PATH = Path(__file__).parent / "skills.yaml"
SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.md"


@dataclass(frozen=True)
class Skill:
    """A single core capability."""

    id: str
    name: str
    summary: str
    competencies: tuple[str, ...] = ()
    patterns: tuple[str, ...] = ()
    frameworks: tuple[str, ...] = ()
    integrations: tuple[str, ...] = ()
    stores: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillModule:
    """A pluggable, domain-specific skill module composed from core skills."""

    id: str
    name: str
    requires: tuple[str, ...]


@dataclass
class SkillRegistry:
    agent_name: str
    agent_version: str
    agent_role: str
    core_skills: dict[str, Skill] = field(default_factory=dict)
    modules: dict[str, SkillModule] = field(default_factory=dict)
    capability_tags: tuple[str, ...] = ()

    def has(self, skill_id: str) -> bool:
        return skill_id in self.core_skills

    def resolve_module(self, module_id: str) -> list[Skill]:
        """Return the core skills required by a module, in declared order."""
        module = self.modules[module_id]
        missing = [r for r in module.requires if r not in self.core_skills]
        if missing:
            raise ValueError(
                f"Module '{module_id}' requires unknown skills: {missing}"
            )
        return [self.core_skills[r] for r in module.requires]

    def skills(self) -> Iterable[Skill]:
        return self.core_skills.values()


def _load_yaml(path: Path) -> dict:
    if yaml is None:  # pragma: no cover
        raise RuntimeError(
            "PyYAML is required to load the GCagent skill manifest. "
            "Install with `pip install pyyaml`."
        )
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _as_tuple(value) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(str(v) for v in value)


def load_registry(path: Path | str | None = None) -> SkillRegistry:
    """Parse `skills.yaml` into a typed SkillRegistry."""
    manifest_path = Path(path) if path else MANIFEST_PATH
    data = _load_yaml(manifest_path)

    agent = data.get("agent", {})
    registry = SkillRegistry(
        agent_name=agent.get("name", "GCagent.ai"),
        agent_version=str(agent.get("version", "0.0.0")),
        agent_role=agent.get("role", "").strip(),
        capability_tags=_as_tuple(data.get("capabilities")),
    )

    for entry in data.get("core_skills", []) or []:
        skill = Skill(
            id=entry["id"],
            name=entry["name"],
            summary=entry.get("summary", ""),
            competencies=_as_tuple(entry.get("competencies")),
            patterns=_as_tuple(entry.get("patterns")),
            frameworks=_as_tuple(entry.get("frameworks")),
            integrations=_as_tuple(entry.get("integrations")),
            stores=_as_tuple(entry.get("stores")),
            outputs=_as_tuple(entry.get("outputs")),
        )
        registry.core_skills[skill.id] = skill

    for entry in data.get("skill_modules", []) or []:
        module = SkillModule(
            id=entry["id"],
            name=entry["name"],
            requires=_as_tuple(entry.get("requires")),
        )
        registry.modules[module.id] = module

    return registry


def render_system_prompt(
    registry: SkillRegistry | None = None,
    *,
    include_modules: Iterable[str] = (),
) -> str:
    """Render the GCagent system prompt, optionally appending module sections.

    The base prompt lives in `system_prompt.md`. Requested modules are
    resolved against the registry and appended as a "Loaded modules" block.
    """
    registry = registry or load_registry()
    base = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    modules = list(include_modules)
    if not modules:
        return base

    lines = ["", "## Loaded modules", ""]
    for module_id in modules:
        module = registry.modules[module_id]
        requires = ", ".join(f"`{r}`" for r in module.requires)
        lines.append(f"- **{module.name}** (`{module.id}`) — requires {requires}.")
    return base.rstrip() + "\n" + "\n".join(lines) + "\n"


if __name__ == "__main__":  # pragma: no cover
    reg = load_registry()
    print(f"{reg.agent_name} v{reg.agent_version}")
    print(f"Core skills: {len(reg.core_skills)}")
    print(f"Modules:     {len(reg.modules)}")
    for skill in reg.skills():
        print(f"  - {skill.id}: {skill.name}")
