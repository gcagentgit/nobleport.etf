"""
Voice Stack Maturity Labels

Every voice/avatar capability carries a visible maturity level.
Contractors will tolerate ugly UI. They will NOT tolerate broken audio,
laggy intake, or missed information.

Operational reliability matters more than avatar realism.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VoiceMaturity(str, Enum):
    PRODUCTION = "PRODUCTION"
    STAGED = "STAGED"
    R_AND_D = "R&D"
    MODELED = "MODELED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class VoiceCapability:
    name: str
    status: VoiceMaturity
    p95_latency_ms: int | None
    blockers: tuple[str, ...]
    dependencies: tuple[str, ...]


VOICE_CAPABILITIES: tuple[VoiceCapability, ...] = (
    VoiceCapability(
        name="Voice Intake (Inbound)",
        status=VoiceMaturity.STAGED,
        p95_latency_ms=312,
        blockers=(),
        dependencies=("LiveKit", "ElevenLabs", "Deepgram nova-3"),
    ),
    VoiceCapability(
        name="Voice Intake (Outbound)",
        status=VoiceMaturity.STAGED,
        p95_latency_ms=420,
        blockers=("SIP trunk routing not verified in production",),
        dependencies=("LiveKit", "ElevenLabs", "3CX/SIP"),
    ),
    VoiceCapability(
        name="Real-Time Avatar",
        status=VoiceMaturity.R_AND_D,
        p95_latency_ms=None,
        blockers=(
            "GPU render latency exceeds acceptable threshold",
            "Lip-sync drift under sustained conversation",
            "No production load testing performed",
        ),
        dependencies=("WebRTC", "GPU cluster", "Custom renderer"),
    ),
    VoiceCapability(
        name="Streaming UI (Transcript)",
        status=VoiceMaturity.STAGED,
        p95_latency_ms=180,
        blockers=("WebSocket reconnection reliability under load",),
        dependencies=("LiveKit Data Channel", "Next.js"),
    ),
    VoiceCapability(
        name="Multilingual Voice",
        status=VoiceMaturity.MODELED,
        p95_latency_ms=None,
        blockers=(
            "ElevenLabs multilingual model latency not benchmarked",
            "ASR accuracy for construction terminology in Spanish untested",
            "No production corpus for MA Portuguese contractors",
        ),
        dependencies=("ElevenLabs Multilingual v2", "Deepgram"),
    ),
    VoiceCapability(
        name="Voice-to-CRM Routing",
        status=VoiceMaturity.STAGED,
        p95_latency_ms=None,
        blockers=("HubSpot webhook delivery guarantees unverified",),
        dependencies=("Stephanie.ai", "HubSpot", "FastAPI"),
    ),
    VoiceCapability(
        name="Emotion/Sentiment Scoring",
        status=VoiceMaturity.MODELED,
        p95_latency_ms=None,
        blockers=(
            "No validated model for construction intake conversations",
            "Privacy review required for emotion data retention",
        ),
        dependencies=("Custom ML model",),
    ),
    VoiceCapability(
        name="Call Recording & Playback",
        status=VoiceMaturity.STAGED,
        p95_latency_ms=None,
        blockers=("MA two-party consent compliance verification pending",),
        dependencies=("LiveKit Egress", "S3/R2"),
    ),
    VoiceCapability(
        name="Barge-In / Operator Override",
        status=VoiceMaturity.STAGED,
        p95_latency_ms=95,
        blockers=(),
        dependencies=("LiveKit", "WebSocket"),
    ),
    VoiceCapability(
        name="Moderation / Content Filtering",
        status=VoiceMaturity.MODELED,
        p95_latency_ms=None,
        blockers=(
            "Edge cases for construction profanity vs. legitimate terms",
            "No real-world adversarial testing performed",
        ),
        dependencies=("Custom filter", "Anthropic API"),
    ),
)


def get_production_ready() -> list[VoiceCapability]:
    return [c for c in VOICE_CAPABILITIES if c.status == VoiceMaturity.PRODUCTION]


def get_blocked() -> list[VoiceCapability]:
    return [c for c in VOICE_CAPABILITIES if c.status == VoiceMaturity.BLOCKED]


def get_all_blockers() -> list[tuple[str, str]]:
    """Returns (capability_name, blocker) pairs for all unresolved blockers."""
    return [
        (cap.name, blocker)
        for cap in VOICE_CAPABILITIES
        for blocker in cap.blockers
    ]


def get_maturity_summary() -> dict[str, int]:
    counts: dict[str, int] = {}
    for cap in VOICE_CAPABILITIES:
        key = cap.status.value
        counts[key] = counts.get(key, 0) + 1
    return counts
