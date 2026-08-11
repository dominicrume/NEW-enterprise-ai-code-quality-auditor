import React from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Colors, space, type } from "./theme";

export function Eyebrow({ children, c }: { children: string; c: Colors }) {
  return (
    <Text style={[type.eyebrow, { color: c.accentInk }]}>{children}</Text>
  );
}

export function Banner({
  kind,
  text,
  c,
}: {
  kind: string | null;
  text: string | null;
  c: Colors;
}) {
  if (!text) return null;
  const tint = kind === "pilot" ? c.warn : c.accent;
  return (
    <View
      style={[
        styles.banner,
        { borderColor: tint, backgroundColor: c.surface },
      ]}
    >
      <View style={[styles.bannerRail, { backgroundColor: tint }]} />
      <Text style={[type.small, { color: c.ink, flex: 1 }]}>{text}</Text>
    </View>
  );
}

/** Horizontal bar, drawn with plain views — no native chart dependency. */
export function Bar({
  value,
  max,
  color,
  track,
}: {
  value: number;
  max: number;
  color: string;
  track: string;
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <View style={[styles.track, { backgroundColor: track }]}>
      <View
        style={[
          styles.fill,
          { width: `${Math.max(pct, value > 0 ? 2 : 0)}%`, backgroundColor: color },
        ]}
      />
    </View>
  );
}

export function Card({
  children,
  c,
}: {
  children: React.ReactNode;
  c: Colors;
}) {
  return (
    <View
      style={[styles.card, { backgroundColor: c.surface, borderColor: c.line }]}
    >
      {children}
    </View>
  );
}

export function Loading({ c, label }: { c: Colors; label: string }) {
  return (
    <View style={styles.center}>
      <ActivityIndicator color={c.accent} />
      <Text style={[type.small, { color: c.muted, marginTop: space.md }]}>
        {label}
      </Text>
    </View>
  );
}

export function ErrorState({
  c,
  message,
  onRetry,
}: {
  c: Colors;
  message: string;
  onRetry: () => void;
}) {
  return (
    <View style={styles.center}>
      <Text style={[type.title, { color: c.ink, textAlign: "center" }]}>
        Couldn't load
      </Text>
      <Text
        style={[
          type.small,
          { color: c.muted, textAlign: "center", marginTop: space.sm },
        ]}
      >
        {message}
      </Text>
      <Pressable
        onPress={onRetry}
        accessibilityRole="button"
        style={({ pressed }) => [
          styles.retry,
          { borderColor: c.accent, opacity: pressed ? 0.6 : 1 },
        ]}
      >
        <Text style={[type.small, { color: c.accentInk, fontWeight: "700" }]}>
          Try again
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.md,
    borderWidth: 1,
    borderRadius: 8,
    padding: space.md,
    overflow: "hidden",
  },
  bannerRail: { width: 3, alignSelf: "stretch", borderRadius: 2 },
  track: { height: 8, borderRadius: 4, overflow: "hidden", width: "100%" },
  fill: { height: 8, borderRadius: 4 },
  card: { borderWidth: 1, borderRadius: 10, padding: space.lg, gap: space.md },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: space.xl },
  retry: {
    marginTop: space.lg,
    borderWidth: 1,
    borderRadius: 999,
    paddingVertical: space.sm,
    paddingHorizontal: space.lg,
  },
});
