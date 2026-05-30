"""Data shapes for audit results. Pydantic = validated, serialisable, testable."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class MetricScore(BaseModel):
    name: str
    value: float
    unit: str = ""


CONDITIONS = Literal[
    "human_control",  # baseline
    "claude_code",    # Anthropic
    "cursor_agent",   # Cursor
    "antigravity",    # Google Gemini
    "replit_agent",   # Replit
]


class AuditResult(BaseModel):
    run_id: str
    condition: CONDITIONS  # type: ignore[valid-type]
    spec_name: str
    spec_version: str
    metrics: list[MetricScore]
    timestamp: datetime
