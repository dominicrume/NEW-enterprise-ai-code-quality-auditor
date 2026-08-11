import React, { useCallback, useEffect, useState } from "react";
import {
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { fetchReports, ReportSummary } from "./api";
import { Card, ErrorState, Eyebrow, Loading } from "./components";
import { Colors, space, type } from "./theme";

export function ReportsScreen({
  c,
  onOpen,
}: {
  c: Colors;
  onOpen: (runId: string) => void;
}) {
  const [reports, setReports] = useState<ReportSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      setError(null);
      setReports(await fetchReports(signal));
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        setError((e as Error).message);
      }
    }
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  if (error && !reports) {
    return <ErrorState c={c} message={error} onRetry={() => load()} />;
  }
  if (!reports) return <Loading c={c} label="Loading evaluations…" />;

  return (
    <FlatList
      data={reports}
      keyExtractor={(r) => r.run_id}
      contentContainerStyle={styles.list}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor={c.accent}
        />
      }
      ListHeaderComponent={
        <View style={styles.header}>
          <Eyebrow c={c}>AI Code Quality Auditor</Eyebrow>
          <Text style={[type.display, { color: c.ink }]}>Evaluations</Text>
          <Text style={[type.small, { color: c.muted }]}>
            Five-metric comparisons of AI coding tools against one fixed
            specification.
          </Text>
        </View>
      }
      ListEmptyComponent={
        <Text style={[type.small, { color: c.muted, padding: space.lg }]}>
          No evaluations published yet.
        </Text>
      }
      renderItem={({ item }) => (
        <Pressable
          onPress={() => onOpen(item.run_id)}
          accessibilityRole="button"
          accessibilityLabel={`Open evaluation ${item.run_id}`}
          style={({ pressed }) => ({ opacity: pressed ? 0.65 : 1 })}
        >
          <Card c={c}>
            <View style={styles.row}>
              <Text style={[type.title, { color: c.ink, flex: 1 }]}>
                {item.run_id}
              </Text>
              <Chip
                label={item.is_pilot ? "Pilot" : "Main study"}
                tint={item.is_pilot ? c.warn : c.accent}
                c={c}
              />
            </View>
            {item.spec ? (
              <Text style={[type.small, { color: c.muted }]}>
                Spec: {item.spec}
              </Text>
            ) : null}
            <Text style={[type.small, { color: c.accentInk }]}>
              View report →
            </Text>
          </Card>
        </Pressable>
      )}
    />
  );
}

function Chip({
  label,
  tint,
  c,
}: {
  label: string;
  tint: string;
  c: Colors;
}) {
  return (
    <View style={[styles.chip, { borderColor: tint, backgroundColor: c.paper }]}>
      <Text style={[type.eyebrow, { color: tint, fontSize: 10 }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  list: { padding: space.lg, gap: space.md, paddingBottom: space.xxl },
  header: { gap: space.xs, marginBottom: space.md },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm },
  chip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: space.md,
    paddingVertical: 3,
  },
});
