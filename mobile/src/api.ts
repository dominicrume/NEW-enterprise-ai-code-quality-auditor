/**
 * Client for the auditor dashboard's JSON API.
 *
 * The evaluation engine itself (Bandit, radon, the manifest deriver) runs
 * server-side or on a developer machine — it shells out to static analysers
 * and cannot run inside a mobile sandbox. This app is the reporting client
 * for evaluations the engine has already produced.
 */
import Constants from "expo-constants";

const FALLBACK_BASE = "https://auditor-dashboard-rume.fly.dev";

export const API_BASE: string =
  (Constants.expoConfig?.extra as { apiBaseUrl?: string } | undefined)
    ?.apiBaseUrl ?? FALLBACK_BASE;

/** One row of the reports index. */
export interface ReportSummary {
  run_id: string;
  csv: string;
  kind: string;
  spec: string | null;
  generated_at: string | null;
  is_pilot: boolean;
  is_dissertation_result: boolean;
}

/** Per-metric roll-up across every condition in a run. */
export interface MetricSummary {
  metric: string;
  unit: string;
  blurb: string;
  best_condition: string;
  best_value: number;
  worst_condition: string;
  worst_value: number;
  values: Record<string, number>;
}

export interface LeaderboardRow {
  condition: string;
  overall_rank: number;
  avg_rank: number;
  rank_sum: number;
  wins: number;
}

export interface Report {
  run_id: string;
  conditions: string[];
  metrics: string[];
  units: Record<string, string>;
  summary: MetricSummary[];
  leaderboard: LeaderboardRow[];
  pivot: Record<string, Record<string, number>>;
  banner_kind: string | null;
  banner_text: string | null;
  reps_per_condition: number | null;
  provenance: Record<string, unknown> | null;
  metric_guidance?: Record<string, { axis?: string; adoption?: string }>;
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    signal,
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(
      res.status === 404
        ? "That evaluation could not be found on the server."
        : `The server returned ${res.status}. Try again in a moment.`,
    );
  }
  return (await res.json()) as T;
}

export const fetchReports = (signal?: AbortSignal) =>
  getJson<ReportSummary[]>("/api/reports", signal);

export const fetchReport = (runId: string, signal?: AbortSignal) =>
  getJson<Report>(`/api/report/${encodeURIComponent(runId)}`, signal);

/**
 * Decision bands, mirroring METRIC_CALIBRATION in auditor/dashboard/app.py.
 * Kept in sync deliberately: the bands are interpretation policy, and the
 * app must not invent its own thresholds.
 */
const CALIBRATION: Record<string, { warning: number; critical: number }> = {
  security_density: { warning: 50, critical: 100 },
  complexity_mean: { warning: 3, critical: 6 },
  duplication_pct: { warning: 5, critical: 10 },
  hallucinations: { warning: 1, critical: 3 },
  correction_freq: { warning: 10, critical: 25 },
};

export type Band = "good" | "warn" | "critical";

export function bandFor(metric: string, value: number): Band {
  const c = CALIBRATION[metric];
  if (!c) return "good";
  if (value >= c.critical) return "critical";
  if (value >= c.warning) return "warn";
  return "good";
}

/** "security_density" -> "Security density" */
export const prettyMetric = (m: string) =>
  m.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

/** "claude_code" -> "Claude Code" */
export const prettyCondition = (c: string) =>
  c
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

export const formatValue = (v: number) =>
  Number.isFinite(v) ? (Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(2)) : "—";
