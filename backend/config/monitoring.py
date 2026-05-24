"""
Monitoring Stack — Canonical Direction

Defines the observability and monitoring toolchain for the NoblePort
platform. Even if not all tools are deployed yet, this establishes
canonical direction so that future implementation is coherent.

This replaces any [TBD] monitoring references with concrete choices.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MonitoringStatus(str, Enum):
    DEPLOYED = "deployed"
    SELECTED = "selected"
    EVALUATING = "evaluating"


@dataclass(frozen=True)
class MonitoringTool:
    function: str
    tool: str
    status: MonitoringStatus
    rationale: str
    alternative: str


MONITORING_STACK: tuple[MonitoringTool, ...] = (
    MonitoringTool(
        function="Backend APM",
        tool="Datadog",
        status=MonitoringStatus.SELECTED,
        rationale="Full-stack traces, Python/FastAPI native, auto-instrumentation",
        alternative="New Relic",
    ),
    MonitoringTool(
        function="Uptime Monitoring",
        tool="BetterStack",
        status=MonitoringStatus.SELECTED,
        rationale="Simple incident pages, heartbeat checks, on-call rotation",
        alternative="Pingdom",
    ),
    MonitoringTool(
        function="Error Tracking",
        tool="Sentry",
        status=MonitoringStatus.DEPLOYED,
        rationale="Python + Next.js SDKs, source maps, release tracking",
        alternative="Bugsnag",
    ),
    MonitoringTool(
        function="Structured Logging",
        tool="OpenTelemetry + Loki",
        status=MonitoringStatus.SELECTED,
        rationale="Vendor-neutral collection, Grafana-native querying",
        alternative="Datadog Logs",
    ),
    MonitoringTool(
        function="Metrics & Dashboards",
        tool="Prometheus + Grafana",
        status=MonitoringStatus.SELECTED,
        rationale="Industry standard, self-hostable, PromQL for custom alerts",
        alternative="Datadog Metrics",
    ),
    MonitoringTool(
        function="Voice Pipeline Telemetry",
        tool="LiveKit Analytics + Custom",
        status=MonitoringStatus.DEPLOYED,
        rationale="Native LiveKit room/participant metrics, custom latency tracking",
        alternative="Custom WebRTC stats",
    ),
    MonitoringTool(
        function="AI Agent Observability",
        tool="LangSmith",
        status=MonitoringStatus.SELECTED,
        rationale="LangChain-native tracing, prompt versioning, eval datasets",
        alternative="Helicone",
    ),
    MonitoringTool(
        function="Infrastructure Alerts",
        tool="Grafana Alerting",
        status=MonitoringStatus.SELECTED,
        rationale="Unified alert rules across Prometheus + Loki sources",
        alternative="PagerDuty",
    ),
    MonitoringTool(
        function="Database Monitoring",
        tool="pg_stat_statements + Grafana",
        status=MonitoringStatus.SELECTED,
        rationale="Native Postgres query performance, no external agent needed",
        alternative="Datadog DBM",
    ),
    MonitoringTool(
        function="Deployment Pipeline",
        tool="Vercel Analytics + GitHub Actions",
        status=MonitoringStatus.DEPLOYED,
        rationale="Native Vercel build/deploy metrics, CI/CD observability",
        alternative="CircleCI",
    ),
)


def get_deployed_tools() -> list[MonitoringTool]:
    return [t for t in MONITORING_STACK if t.status == MonitoringStatus.DEPLOYED]


def get_stack_summary() -> dict[str, str]:
    """Function → Tool mapping for quick reference."""
    return {t.function: t.tool for t in MONITORING_STACK}
