"""
KPI Snapshot Worker

Runs on interval (default 5-15 min) to query source tables and update
kpi_snapshot. Never overwrites audit history — appends new measurements.

Until source tables are wired, modules stay at BLOCKED with null values.
When a source is connected, the worker flips the truth_label to LIVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.config.module_registry import MODULE_DEFINITIONS, ModuleDef


@dataclass
class KPIReading:
    module_id: int
    kpi_name: str
    kpi_value: float | None
    kpi_unit: str
    truth_label: str
    source_ref: str | None
    measured_at: str


CONNECTED_SOURCES: dict[str, bool] = {}


class KPIWorker:
    """Collects KPI readings from source tables and builds snapshots."""

    def __init__(self):
        self._snapshots: list[KPIReading] = []
        self._latest: dict[int, KPIReading] = {}

    async def collect_all(self) -> list[KPIReading]:
        readings = []
        now = datetime.now(timezone.utc).isoformat()

        for module in MODULE_DEFINITIONS:
            reading = await self._collect_module(module, now)
            readings.append(reading)
            self._latest[module.module_id] = reading

        self._snapshots.extend(readings)
        return readings

    async def _collect_module(self, module: ModuleDef, ts: str) -> KPIReading:
        if module.source_table and module.source_table in CONNECTED_SOURCES:
            value = await self._query_source(module.source_table, module.kpi_unit)
            return KPIReading(
                module_id=module.module_id,
                kpi_name=module.kpi_name,
                kpi_value=value,
                kpi_unit=module.kpi_unit,
                truth_label="LIVE",
                source_ref=f"postgres.{module.source_table}",
                measured_at=ts,
            )

        return KPIReading(
            module_id=module.module_id,
            kpi_name=module.kpi_name,
            kpi_value=None,
            kpi_unit=module.kpi_unit,
            truth_label="BLOCKED",
            source_ref=None,
            measured_at=ts,
        )

    async def _query_source(self, table: str, unit: str) -> float | None:
        return None

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
