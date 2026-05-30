# Setup

## You need
Python 3.11+. (Optional: SonarQube via Docker for the security analyzer.)

## Install
```bash
git clone <repo>
cd ai-code-quality-auditor
cp .env.example .env             # fill in keys you'll use
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q                         # confirm tests pass
auditor --help
```
