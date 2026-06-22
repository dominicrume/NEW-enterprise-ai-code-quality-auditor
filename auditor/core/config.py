"""Reads environment / .env. Never hard-code secrets."""
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Settings:
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    # NB: security scanning uses local Bandit (see security_analyzer.py); the
    # original SonarCloud settings were retired during the pilot (Deviation 002).
    run_id: str = os.environ.get("EXPERIMENT_RUN_ID", "run_001")


settings = Settings()
