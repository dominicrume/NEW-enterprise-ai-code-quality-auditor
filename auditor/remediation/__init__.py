"""Remediation — propose and verify fixes for findings the auditor reports.

Deliberately downstream of measurement. The analysers stay deterministic and
blind; nothing here can influence a score. A fix is only ever kept when
re-running the same analysers proves the finding is gone and no new finding
appeared in its place.
"""
from auditor.remediation.engine import FixOutcome, Remediation, remediate

__all__ = ["FixOutcome", "Remediation", "remediate"]
