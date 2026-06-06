"""
NoblePort OS — Business Domains

Each domain is a coherent business capability with its own models,
services, API routes, and ownership boundaries. Domains compose
into the full NoblePort operating system.

  intake          — first-touch, inbound qualification, routing
  leads           — lead pipeline, scoring, nurture
  jobs            — job execution, scheduling, profitability
  workflows       — workflow templates and the automation engine
  marketing       — campaigns, content, channels, attribution
  follow_ups      — automated follow-up sequences and reminders
  contacts        — CRM contact directory and communication log
  permits         — permit applications, AHJ tracking, inspections
  subcontractors  — sub directory, bids, insurance, payments
  construction    — field operations, daily logs, crew management

Domains use the existing models in backend/models/ where they overlap
and add their own models for net-new entities.
"""

from __future__ import annotations

DOMAIN_REGISTRY = {
    "intake": "First-touch, inbound qualification, routing",
    "leads": "Lead pipeline, scoring, nurture",
    "jobs": "Job execution, scheduling, profitability",
    "workflows": "Workflow templates and the automation engine",
    "marketing": "Campaigns, content, channels, attribution",
    "follow_ups": "Automated follow-up sequences and reminders",
    "contacts": "CRM contact directory and communication log",
    "permits": "Permit applications, AHJ tracking, inspections",
    "subcontractors": "Sub directory, bids, insurance, payments",
    "construction": "Field operations, daily logs, crew management",
}

__all__ = ["DOMAIN_REGISTRY"]
