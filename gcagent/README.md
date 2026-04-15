# GCagent.ai — Skill Framework

A structured, declarative skill framework for **GCagent.ai**, the technical
collaborator agent used across the Noble Port ecosystem.

This module is the source of truth for:

- **What GCagent can do** — core capabilities and pluggable skill modules.
- **How GCagent presents itself** — drop-in system prompt for OpenAI,
  Anthropic, or LangChain-style runtimes.
- **How callers route tasks** — short capability tags consumed by orchestrators.

## Layout

```
gcagent/
├── README.md            # this file
├── skills.yaml          # declarative capability manifest
├── system_prompt.md     # drop-in system prompt
├── capabilities.py      # Python registry + prompt renderer
├── __init__.py
└── modules/             # reserved for per-module scaffolds
```

## Core skills

Twelve always-on capabilities defined in `skills.yaml`:

| Tag                         | Focus                                                   |
|-----------------------------|---------------------------------------------------------|
| `agent_architecture`        | Single- and multi-agent design, roles, comms.           |
| `tool_integration`          | Function/tool calling, schemas, routing, auth.          |
| `workflow_orchestration`    | LangChain, LangGraph, AutoGen, CrewAI, custom.          |
| `memory_management`         | Short-/long-term memory, vector stores, windowing.      |
| `rag_systems`               | Ingestion, chunking, hybrid retrieval, grounding.       |
| `debugging_observability`   | Traces, evals, regression testing.                      |
| `prompt_engineering`        | System prompts, few-shot, guardrails, modularization.   |
| `backend_infrastructure`    | APIs, queues, containers, serverless, k8s.              |
| `reliability_safety`        | Validation, rate limits, fallbacks, safe completion.    |
| `performance_optimization`  | Token, latency, caching, model selection.               |
| `workflow_automation`       | Autonomous pipelines, cron/event, HITL.                 |
| `developer_experience`      | Boilerplate, refactors, code review.                    |

## Skill modules (pluggable)

Domain-specific extensions declared in `skills.yaml` under `skill_modules`.
Each module names the core skills it requires, so callers can validate that
a target runtime is provisioned before loading the module.

- `multi_agent_negotiation`
- `autonomous_research`
- `code_generation`
- `devops_automation`
- `customer_support`
- `internal_knowledgebase`

## Usage

### Load the registry

```python
from gcagent import load_registry

reg = load_registry()
print(reg.agent_name, reg.agent_version)
for skill in reg.skills():
    print(skill.id, "-", skill.name)
```

### Render the system prompt

```python
from gcagent import load_registry, render_system_prompt

reg = load_registry()

# Base prompt only
prompt = render_system_prompt(reg)

# Base prompt + resolved module sections
prompt = render_system_prompt(reg, include_modules=["autonomous_research"])
```

### Validate a module's requirements

```python
from gcagent import load_registry

reg = load_registry()
required_skills = reg.resolve_module("devops_automation")
# -> [Skill(backend_infrastructure), Skill(workflow_automation), Skill(reliability_safety)]
```

## Extending

1. Add a new entry under `core_skills` or `skill_modules` in `skills.yaml`.
2. If the module needs runtime scaffolding (sub-agents, tools, prompts),
   create a package under `gcagent/modules/<module_id>/`.
3. Re-run `python -m gcagent.capabilities` to sanity-check the manifest.

## Design notes

- The manifest is **declarative-first**. Python types in `capabilities.py`
  mirror the YAML rather than the other way around, so non-Python callers
  (Node, shell scripts, CI jobs) can consume the same source of truth.
- Modules declare `requires:` against core skill IDs. This keeps composition
  explicit and lets orchestrators refuse to load a module on a runtime that
  lacks the underlying capability.
- The system prompt is kept in Markdown, not Python string literals, so it can
  be reviewed, diffed, and edited without touching code.
