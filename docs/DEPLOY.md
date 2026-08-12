# Deploy guide — getting the auditor in front of users

Four artefacts ship from this repo. The first three are commands you run
once each; the fourth happens automatically.

## 1. PyPI — `pipx install ai-code-quality-auditor`

The package is built and twine-validated under `dist/`. To publish:

```bash
# One-time: get a PyPI API token from https://pypi.org/manage/account/token/
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEI…           # paste your token

# Upload (sdist + wheel are already built)
twine upload dist/*
```

Verify with `pipx install ai-code-quality-auditor && auditor --help`.

To cut a new release later: bump `version =` in `pyproject.toml`, then
`rm -rf dist build && python -m build && twine upload dist/*`.

## 2. GitHub Action — `dominicrume/NEW-enterprise-ai-code-quality-auditor@v1`

The repo root already contains `action.yml`, so the repo itself is the
action. After the next `git push`:

```bash
# Tag it so consumers pin to a stable ref
git tag -a v1 -m "First public release"
git push origin v1

# Make it discoverable on the GitHub Actions marketplace:
# https://github.com/marketplace/actions  →  "Publish this Action"
# (one-click in the GitHub UI on the release page)
```

A third party then drops these six lines into their own workflow:

```yaml
- uses: dominicrume/NEW-enterprise-ai-code-quality-auditor@v1
  with:
    run-id: ${{ github.run_id }}
    spec: specs/agent_education_system.yaml
    conditions: claude_code,cursor_agent
    fail-on-hallucination: "true"
```

See `.github/workflows/example-usage.yml` for the full template.

## 3. Hosted dashboard — `https://auditor-dashboard-rume.fly.dev`

Fly.io free tier handles this. One-time setup:

```bash
# Install fly CLI
brew install flyctl

# Sign in (opens browser)
fly auth signup        # or `fly auth login` if you have an account

# Provision app (uses the fly.toml in this repo)
fly launch --no-deploy --copy-config --name auditor-dashboard

# Deploy
fly deploy
```

After deploy: `fly status` shows the public URL. Update the badge in
`README.md` and the LinkedIn post.

To re-deploy on every push, add this job to `.github/workflows/ci.yml`:

```yaml
deploy-dashboard:
  needs: tests
  if: github.ref == 'refs/heads/main'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: superfly/flyctl-actions/setup-flyctl@master
    - run: flyctl deploy --remote-only
      env:
        FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

Set `FLY_API_TOKEN` from `fly auth token` into the repo secrets.

## 4. LinkedIn / dissertation linkage — automatic once #3 is live

Once the Fly URL exists, the existing screenshots at
`docs/screenshots/dashboard_report.png` and the README badge both already
reference the hosted dashboard URL. No further edits needed — every link
in your LinkedIn post, dissertation appendix, and PhD application
artefacts goes to the same place.

---

## Summary of what each gives you

| Artefact | Who uses it | Their effort |
|---|---|---|
| `pipx install ai-code-quality-auditor` | Devs evaluating AI tools locally | 1 command |
| GitHub Action | Engineering managers wiring into CI | 6 lines of YAML |
| Hosted dashboard URL | Non-technical viewers (Alex, supervisors, partners) | 1 click |
| Live commit on `main` | Anyone reading the LinkedIn post | scroll |
