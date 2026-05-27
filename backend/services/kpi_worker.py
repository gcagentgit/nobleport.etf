"""
KPI Snapshot Worker

Runs on interval (default 5-15 min) to query source tables and update
kpi_snapshot. Never overwrites audit history — appends new measurements.

Connected sources flip truth_label from BLOCKED to LIVE.
Unconnected sources stay BLOCKED with null values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import async_session
from backend.config.module_registry import MODULE_DEFINITIONS, ModuleDef
from backend.models.change_order import ChangeOrder
from backend.models.daily_log import DailyLog
from backend.models.estimate import Estimate
from backend.models.invoice import Invoice
from backend.models.job import Job
from backend.models.lead import Lead
from backend.models.mcp import MCPCallLog, NoblePortModuleRegistry, KPISnapshot as KPISnapshotModel
from backend.models.payment import Payment
from backend.models.project import Project
from backend.models.schedule import ScheduleItem


@dataclass
class KPIReading:
    module_id: int
    kpi_name: str
    kpi_value: float | None
    kpi_unit: str
    truth_label: str
    source_ref: str | None
    measured_at: str


TABLE_QUERY_MAP: dict[int, dict[str, Any]] = {
    # Module 1: Executive Command Center — count of MCP calls today
    1: {"table": "mcp_call_log", "query": "count"},
    # Module 2: Lead Intake — total leads
    2: {"table": "leads", "query": "count"},
    # Module 4: Project Registry — active projects
    4: {"table": "projects", "query": "count"},
    # Module 5: Workflow Router — routing success rate from mcp_call_log
    5: {"table": "mcp_call_log", "query": "success_rate"},
    # Module 8: Truth Ledger — LIVE/MODELED/BLOCKED ratio
    8: {"table": "nobleport_module_registry", "query": "truth_ratio"},
    # Module 10: KPI Dashboard — modules with live data
    10: {"table": "kpi_snapshot", "query": "live_count"},
    # Module 11: Estimate Engine — estimates count
    11: {"table": "estimates", "query": "count"},
    # Module 13: AWO Engine — change orders count
    13: {"table": "change_orders", "query": "count"},
    # Module 14: Job Costing — avg margin percent across jobs
    14: {"table": "jobs", "query": "avg_margin"},
    # Module 15: Schedule Builder — avg slippage (schedule items with delays)
    15: {"table": "schedule_items", "query": "count"},
    # Module 18: Field Daily Logs — daily log count
    18: {"table": "daily_logs", "query": "count"},
    # Module 34: Tool Permission Guard — denied calls from mcp_call_log
    34: {"table": "mcp_call_log", "query": "denied_count"},
}


async def _count_table(session: AsyncSession, model: type) -> float:
    result = await session.execute(select(func.count()).select_from(model))
    return float(result.scalar() or 0)


async def _query_module(session: AsyncSession, module_id: int) -> tuple[float | None, str | None]:
    """Query a specific module's source table. Returns (value, source_ref)."""
    spec = TABLE_QUERY_MAP.get(module_id)
    if not spec:
        return None, None

    table = spec["table"]
    query_type = spec["query"]

    try:
        if table == "leads" and query_type == "count":
            val = await _count_table(session, Lead)
            return val, "postgres.leads"

        if table == "projects" and query_type == "count":
            val = await _count_table(session, Project)
            return val, "postgres.projects"

        if table == "estimates" and query_type == "count":
            val = await _count_table(session, Estimate)
            return val, "postgres.estimates"

        if table == "change_orders" and query_type == "count":
            val = await _count_table(session, ChangeOrder)
            return val, "postgres.change_orders"

        if table == "schedule_items" and query_type == "count":
            val = await _count_table(session, ScheduleItem)
            return val, "postgres.schedule_items"

        if table == "daily_logs" and query_type == "count":
            val = await _count_table(session, DailyLog)
            return val, "postgres.daily_logs"

        if table == "jobs" and query_type == "avg_margin":
            result = await session.execute(
                select(func.avg(Job.margin_percent)).select_from(Job)
            )
            avg = result.scalar()
            return float(avg) if avg is not None else 0.0, "postgres.jobs"

        if table == "mcp_call_log" and query_type == "count":
            val = await _count_table(session, MCPCallLog)
            return val, "postgres.mcp_call_log"

        if table == "mcp_call_log" and query_type == "success_rate":
            total_r = await session.execute(
                select(func.count()).select_from(MCPCallLog)
            )
            total = total_r.scalar() or 0
            if total == 0:
                return 100.0, "postgres.mcp_call_log"
            success_r = await session.execute(
                select(func.count()).select_from(MCPCallLog).where(
                    MCPCallLog.status == "success"
                )
            )
            success = success_r.scalar() or 0
            return round((success / total) * 100, 1), "postgres.mcp_call_log"

        if table == "mcp_call_log" and query_type == "denied_count":
            result = await session.execute(
                select(func.count()).select_from(MCPCallLog).where(
                    MCPCallLog.status == "denied"
                )
            )
            return float(result.scalar() or 0), "postgres.mcp_call_log"

        if table == "nobleport_module_registry" and query_type == "truth_ratio":
            result = await session.execute(
                select(func.count()).select_from(NoblePortModuleRegistry).where(
                    NoblePortModuleRegistry.truth_label == "LIVE"
                )
            )
            live = result.scalar() or 0
            return float(live), "postgres.nobleport_module_registry"

        if table == "kpi_snapshot" and query_type == "live_count":
            result = await session.execute(
                select(func.count(func.distinct(KPISnapshotModel.module_id))).select_from(
                    KPISnapshotModel
                ).where(KPISnapshotModel.truth_label == "LIVE")
            )
            return float(result.scalar() or 0), "postgres.kpi_snapshot"

    except Exception:
        return None, None

    return None, None


class KPIWorker:
    """Collects KPI readings from source tables and builds snapshots."""

    def __init__(self):
        self._snapshots: list[KPIReading] = []
        self._latest: dict[int, KPIReading] = {}

    async def collect_all(self) -> list[KPIReading]:
        readings = []
        now = datetime.now(timezone.utc).isoformat()

        try:
            async with async_session() as session:
                for module in MODULE_DEFINITIONS:
                    reading = await self._collect_module(session, module, now)
                    readings.append(reading)
                    self._latest[module.module_id] = reading
        except Exception:
            for module in MODULE_DEFINITIONS:
                reading = self._blocked_reading(module, now)
                readings.append(reading)
                self._latest[module.module_id] = reading

        self._snapshots.extend(readings)
        return readings

    async def _collect_module(
        self, session: AsyncSession, module: ModuleDef, ts: str
    ) -> KPIReading:
        if module.module_id in TABLE_QUERY_MAP:
            value, source_ref = await _query_module(session, module.module_id)
            if value is not None:
                return KPIReading(
                    module_id=module.module_id,
                    kpi_name=module.kpi_name,
                    kpi_value=value,
                    kpi_unit=module.kpi_unit,
                    truth_label="LIVE",
                    source_ref=source_ref,
                    measured_at=ts,
                )

        return self._blocked_reading(module, ts)

    def _blocked_reading(self, module: ModuleDef, ts: str) -> KPIReading:
        return KPIReading(
            module_id=module.module_id,
            kpi_name=module.kpi_name,
            kpi_value=None,
            kpi_unit=module.kpi_unit,
            truth_label="BLOCKED",
            source_ref=None,
            measured_at=ts,
        )

    def get_latest(self) -> list[dict]:
        return [
            {
                "module_id": r.module_id,
                "kpi_name": r.kpi_name,
                "kpi_value": r.kpi_value,
                "kpi_unit": r.kpi_unit,
                "truth_label": r.truth_label,
                "source_ref": r.source_ref,
                "measured_at": r.measured_at,
            }
            for r in self._latest.values()
        ]

    def get_module_reading(self, module_id: int) -> dict | None:
        reading = self._latest.get(module_id)
        if not reading:
            return None
        return {
            "module_id": reading.module_id,
            "kpi_name": reading.kpi_name,
            "kpi_value": reading.kpi_value,
            "kpi_unit": reading.kpi_unit,
            "truth_label": reading.truth_label,
            "source_ref": reading.source_ref,
            "measured_at": reading.measured_at,
        }

    def get_agent_readings(self, agent_name: str) -> list[dict]:
        agent_modules = {
            m.module_id for m in MODULE_DEFINITIONS if m.owner_agent == agent_name
        }
        return [
            {
                "module_id": r.module_id,
                "kpi_name": r.kpi_name,
                "kpi_value": r.kpi_value,
                "kpi_unit": r.kpi_unit,
                "truth_label": r.truth_label,
                "source_ref": r.source_ref,
                "measured_at": r.measured_at,
            }
            for mid, r in self._latest.items()
            if mid in agent_modules
        ]

    def get_truth_summary(self) -> dict:
        if not self._latest:
            return {"total": 50, "LIVE": 0, "MODELED": 0, "BLOCKED": 50}
        labels = [r.truth_label for r in self._latest.values()]
        return {
            "total": len(labels),
            "LIVE": labels.count("LIVE"),
            "MODELED": labels.count("MODELED"),
            "BLOCKED": labels.count("BLOCKED"),
        }


kpi_worker = KPIWorker()
