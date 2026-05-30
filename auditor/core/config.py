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
    sonarqube_url: str = os.environ.get("SONARQUBE_URL", "")
    sonarqube_token: str = os.environ.get("SONARQUBE_TOKEN", "")
    sonarqube_organization: str = os.environ.get("SONARQUBE_ORGANIZATION", "")
    run_id: str = os.environ.get("EXPERIMENT_RUN_ID", "run_001")


settings = Settings()
