import { createContext, useContext, useEffect, useState } from "react";

export const THEMES = ["archive", "carbon", "slate", "sepia"];
export const THEME_LABELS = {
  archive: "Archive",
  carbon: "Carbon",
  slate: "Slate",
  sepia: "Sepia",
};

const STORAGE_KEY = "sentinelrag_theme";
const ThemeContext = createContext(null);

function readStoredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return THEMES.includes(stored) ? stored : "archive";
  } catch {
    // Private browsing / blocked storage -- fall back to the default
    // theme rather than let the app fail to render.
    return "archive";
  }
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(readStoredTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Nothing to do -- the theme still applies for this session, it
      // just won't be remembered on reload.
    }
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used inside a ThemeProvider");
  }
  return ctx;
}
