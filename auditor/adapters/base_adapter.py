"""Base contract every AI workflow adapter implements."""
from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    name: str

    @abstractmethod
    def generate(self, spec: dict) -> tuple[dict, list[dict]]:
        """Return (codebase, interaction_log).

        codebase: {"files": {path: content}, "manifest": [feature_ids...]}
        interaction_log: list of events with at minimum a "type" key.
        """
