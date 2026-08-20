# AI Code Auditor — mobile app

A native iOS and Android client for the AI Code Quality Auditor. It reads
published evaluations from the dashboard API and presents them as an executive
assurance report: five metrics per run, colour-banded against the same decision
thresholds the web dashboard uses, with an overall ranking.

Built with Expo (React Native), TypeScript, and zero native chart dependencies —
bars are drawn with plain views, which keeps the build reproducible and the
store review surface small.

## The architectural boundary (read this first)

**The app is a reporting client, not the evaluation engine.** The five analysers
shell out to static-analysis tools (Bandit), walk a filesystem, and parse
captured agent sessions. Neither iOS nor Android permits that inside an app
sandbox, so the engine stays where it is — the CLI and the server — and the app
consumes what the engine publishes:

```
auditor CLI / server            this app
──────────────────              ────────
spec → adapter → capture
   → 5 analysers → CSV
   → Flask dashboard  ── JSON API ──►  native iOS / Android client
```

If a future version needs on-device evaluation, the honest path is a hosted
`POST /api/evaluate` endpoint that the app calls — the analysis still runs on a
server, the phone just triggers it.

## Test it on your phone in about two minutes

```bash
cd mobile
npm install
npx expo start
```

Install **Expo Go** (App Store / Play Store), scan the QR code from the
terminal with your camera, and the app opens on your phone against the live
API. Edit a file and it reloads instantly. No developer account, no build, no
store review — this is the fastest way to demo it.

For a standalone build you can install without Expo Go, see *Store builds*
below.

## Configuration

The API base URL lives in `app.json` under `expo.extra.apiBaseUrl` and defaults
to the live dashboard. Point it at a local server for development:

```bash
# terminal 1 — the dashboard
PYTHONPATH=. python -m auditor.dashboard.app     # http://127.0.0.1:5050

# then set expo.extra.apiBaseUrl to http://<your-LAN-ip>:5050
# (localhost won't resolve from a physical phone — use the machine's LAN IP)
```

## Project layout

| File | Purpose |
|---|---|
| `App.tsx` | Root; theme selection and screen switching |
| `src/api.ts` | Typed API client, decision bands, formatting |
| `src/theme.ts` | Palette shared with the web dashboard, light + dark |
| `src/components.tsx` | Card, bar, banner, loading and error states |
| `src/ReportsScreen.tsx` | List of published evaluations, pull to refresh |
| `src/ReportDetailScreen.tsx` | Per-metric detail and overall ranking |

## Store builds

Builds run on Expo's servers (EAS) — you do **not** need a Mac to build for iOS.

```bash
npm install -g eas-cli
eas login                       # free Expo account
eas build:configure
eas build --platform ios        # or android, or all
eas submit --platform ios       # uploads to App Store Connect
eas submit --platform android   # uploads to Play Console
```

### What you need before submitting

| Requirement | Apple | Google |
|---|---|---|
| Developer account | Apple Developer Program, **$99/year** | Play Console, **$25 one-time** |
| Identity verification | Yes — can take several days | Yes; individual accounts also need 12 testers for 14 days before production |
| Bundle / package ID | `dev.rume.aicodeauditor` (set in `app.json`) | same |
| Privacy policy URL | Required | Required |
| Screenshots | 6.7" iPhone required | Phone required |
| Review time | Typically 1–3 days | Typically hours to 3 days |

Change `dev.rume.aicodeauditor` in `app.json` to a domain you control before
first submission — the identifier is permanent once published.

### Data-collection declarations

Both stores require a data-safety declaration. As written, this app **collects
nothing**: no accounts, no analytics, no advertising identifiers, no personal
data. It makes anonymous read-only HTTPS requests to the dashboard API. Declare
exactly that; if you later add analytics or sign-in, both declarations must be
updated before the next release.

`ITSAppUsesNonExemptEncryption` is already set to `false` in `app.json`, which
is correct for an app whose only cryptography is standard HTTPS.

### Likely review friction, stated honestly

An app that only displays reports from one server can attract Apple's
*Guideline 4.2 — Minimum Functionality* ("this could be a website"). Two things
reduce that risk, and both are worth doing before submitting: give the app at
least one capability the web page lacks (offline caching of the last-viewed
report, or push notification when a new evaluation is published), and provide
reviewer notes explaining that it is the client for a research instrument, with
a link to the dashboard and the PyPI package. If the target audience is a
handful of partners and clients rather than the public, **TestFlight and Play
internal testing are the better distribution route** — no public review, and
you can share an install link the same day.

## Dependency advisories

Dependabot reports advisories against two transitive npm packages. Both come
from Expo's build tooling; neither is code that ships inside the app.

**`uuid` — fixed.** Pinned to 14.x through an `overrides` entry in
`package.json`, replacing the 7.0.3 that `xcode` pulls in. The bundle was
rebuilt and verified after the change.

**`image-size` — no fix exists.** The advisory's affected range is `*`: every
published version is covered, so there is no version to upgrade to. npm's only
proposed remedy is downgrading Expo from 57 to 53, which trades one advisory
for four major versions of missing security work. Pinned to the newest release
(2.0.2) and left flagged rather than pretending otherwise.

Assessment for the `image-size` advisories: they are denial-of-service loops in
the ICNS, JXL and HEIF parsers. Metro calls `image-size` at **build time** to
read the dimensions of assets in this repository. Triggering it would require a
malicious image to already be committed here — that is, write access to the
repository, at which point the parser is not the exposure that matters. Nothing
reaches an end user, because the parser does not ship in the app bundle.

Re-check with:

```bash
npm audit
npx expo export --platform android    # confirm the build still works
```
