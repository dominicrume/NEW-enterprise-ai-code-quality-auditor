import { StatusBar } from "expo-status-bar";
import React, { useState } from "react";
import { SafeAreaView, StyleSheet, useColorScheme, View } from "react-native";
import { ReportDetailScreen } from "./src/ReportDetailScreen";
import { ReportsScreen } from "./src/ReportsScreen";
import { palette } from "./src/theme";

export default function App() {
  const scheme = useColorScheme() === "dark" ? "dark" : "light";
  const c = palette[scheme];
  const [openRunId, setOpenRunId] = useState<string | null>(null);

  return (
    <SafeAreaView style={[styles.root, { backgroundColor: c.paper }]}>
      <StatusBar style={scheme === "dark" ? "light" : "dark"} />
      <View style={styles.body}>
        {openRunId ? (
          <ReportDetailScreen
            c={c}
            runId={openRunId}
            onBack={() => setOpenRunId(null)}
          />
        ) : (
          <ReportsScreen c={c} onOpen={setOpenRunId} />
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  body: { flex: 1, paddingHorizontal: 2 },
});
