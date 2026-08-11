import React, { useCallback, useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import {
  bandFor,
  fetchReport,
  formatValue,
  prettyCondition,
  prettyMetric,
  Report,
} from "./api";
import { Banner, Bar, Card, ErrorState, Eyebrow, Loading } from "./components";
import { Colors, space, type } from "./theme";

export function ReportDetailScreen({
  c,
  runId,
  onBack,
}: {
  c: Colors;
  runId: string;
  onBack: () => void;
}) {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      try {
        setError(null);
        setReport(await fetchReport(runId, signal));
      } catch (e) {
        if ((e as Error).name !== "AbortError") setError((e as Error).message);
      }
    },
    [runId],
  );

  useEffect(() => {
    const ctrl = new AbortController();
    load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  const back = (
    <Pressable
      onPress={onBack}
      accessibilityRole="button"
      accessibilityLabel="Back to evaluations"
      style={({ pressed }) => [styles.back, { opacity: pressed ? 0.6 : 1 }]}
    >
      <Text style={[type.body, { color: c.accentInk }]}>‹ Evaluations</Text>
    </Pressable>
  );

  if (error && !report) {
    return (
      <View style={{ flex: 1 }}>
        {back}
        <ErrorState c={c} message={error} onRetry={() => load()} />
      </View>
    );
  }
  if (!report) {
    return (
      <View style={{ flex: 1 }}>
        {back}
        <Loading c={c} label="Loading report…" />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.body}>
      {back}
      <View style={styles.header}>
        <Eyebrow c={c}>Assurance report</Eyebrow>
        <Text style={[type.display, { color: c.ink }]}>{report.run_id}</Text>
        <Text style={[type.small, { color: c.muted }]}>
          {report.metrics.length} metrics · {report.conditions.length} conditions
          {report.reps_per_condition
            ? ` · ${report.reps_per_condition} runs each`
            : ""}
        </Text>
      </View>

      <Banner kind={report.banner_kind} text={report.banner_text} c={c} />

      {report.summary.map((s) => {
        const max = Math.max(...Object.values(s.values), 0);
        return (
          <Card c={c} key={s.metric}>
            <View>
              <Text style={[type.title, { color: c.ink }]}>
                {prettyMetric(s.metric)}
              </Text>
              <Text style={[type.small, { color: c.muted, marginTop: 2 }]}>
                {s.blurb}
              </Text>
            </View>

            <View style={styles.bestRow}>
              <View style={{ flex: 1 }}>
                <Text style={[type.eyebrow, { color: c.muted, fontSize: 10 }]}>
                  Best
                </Text>
                <Text style={[type.body, { color: c.ink, fontWeight: "700" }]}>
                  {prettyCondition(s.best_condition)}
                </Text>
              </View>
              <View style={{ alignItems: "flex-end" }}>
                <Text style={[type.metric, { color: c.accentInk }]}>
                  {formatValue(s.best_value)}
                </Text>
                <Text style={[type.small, { color: c.muted }]}>{s.unit}</Text>
              </View>
            </View>

            <View style={{ gap: space.sm }}>
              {report.conditions.map((cond) => {
                const v = s.values[cond];
                if (v === undefined) return null;
                const tint =
                  bandFor(s.metric, v) === "critical"
                    ? c.critical
                    : bandFor(s.metric, v) === "warn"
                      ? c.warn
                      : c.good;
                return (
                  <View key={cond} style={{ gap: 3 }}>
                    <View style={styles.barLabel}>
                      <Text style={[type.small, { color: c.ink, flex: 1 }]}>
                        {prettyCondition(cond)}
                      </Text>
                      <Text
                        style={[
                          type.small,
                          { color: c.muted, fontVariant: ["tabular-nums"] },
                        ]}
                      >
                        {formatValue(v)}
                      </Text>
                    </View>
                    <Bar value={v} max={max} color={tint} track={c.track} />
                  </View>
                );
              })}
            </View>
          </Card>
        );
      })}

      {report.leaderboard.length > 0 && (
        <Card c={c}>
          <Text style={[type.title, { color: c.ink }]}>Overall ranking</Text>
          <Text style={[type.small, { color: c.muted }]}>
            Illustrative rank-sum across metrics — not a weighted procurement
            score. Read it alongside the per-metric detail above.
          </Text>
          {report.leaderboard.map((row) => (
            <View key={row.condition} style={styles.lbRow}>
              <Text style={[type.body, { color: c.accentInk, width: 26 }]}>
                {row.overall_rank}
              </Text>
              <Text style={[type.body, { color: c.ink, flex: 1 }]}>
                {prettyCondition(row.condition)}
              </Text>
              <Text style={[type.small, { color: c.muted }]}>
                {row.wins} best-in-metric
              </Text>
            </View>
          ))}
        </Card>
      )}

      <Text style={[type.small, { color: c.muted, textAlign: "center" }]}>
        Evaluations are produced by the auditor engine and published to the
        dashboard. This app reads them; it does not run the analysers.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  body: { padding: space.lg, gap: space.md, paddingBottom: space.xxl },
  back: { paddingVertical: space.sm },
  header: { gap: space.xs },
  bestRow: { flexDirection: "row", alignItems: "flex-end", gap: space.md },
  barLabel: { flexDirection: "row", alignItems: "center", gap: space.sm },
  lbRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
});
