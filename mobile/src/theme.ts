/**
 * Palette shared with the web dashboard and the briefing pack, so the
 * mobile app reads as the same product rather than a separate one.
 */
export type Scheme = "light" | "dark";

/** Every surface and ink the UI is allowed to paint with. */
export interface Colors {
  paper: string;
  surface: string;
  ink: string;
  muted: string;
  line: string;
  accent: string;
  accentInk: string;
  good: string;
  warn: string;
  critical: string;
  track: string;
}

export const palette: Record<Scheme, Colors> = {
  light: {
    paper: "#F7F8F5",
    surface: "#FFFFFF",
    ink: "#20272B",
    muted: "#5C6660",
    line: "#DCE1DB",
    accent: "#0F766E",
    accentInk: "#0B5D57",
    good: "#0F766E",
    warn: "#A2733B",
    critical: "#A2473B",
    track: "#EDEFEA",
  },
  dark: {
    paper: "#131715",
    surface: "#1A201D",
    ink: "#E8ECE8",
    muted: "#98A29B",
    line: "#2A322E",
    accent: "#35B8A6",
    accentInk: "#5ECDBE",
    good: "#35B8A6",
    warn: "#D6A75F",
    critical: "#D9705E",
    track: "#232B27",
  },
};

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 };

export const type = {
  display: { fontSize: 26, fontWeight: "700" as const, letterSpacing: -0.4 },
  title: { fontSize: 19, fontWeight: "700" as const, letterSpacing: -0.2 },
  body: { fontSize: 15, fontWeight: "400" as const },
  small: { fontSize: 13, fontWeight: "400" as const },
  eyebrow: {
    fontSize: 11,
    fontWeight: "700" as const,
    letterSpacing: 1.1,
    textTransform: "uppercase" as const,
  },
  metric: { fontSize: 30, fontWeight: "700" as const, letterSpacing: -0.8 },
};
