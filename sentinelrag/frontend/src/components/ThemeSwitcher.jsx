import { THEMES, THEME_LABELS, useTheme } from "../theme";

/**
 * Four labeled swatches, not a dropdown, so a theme change is a single
 * click -- reachable both inside the app (Sidebar) and on the public
 * landing page, before anyone has logged in.
 */
export default function ThemeSwitcher({ className = "" }) {
  const { theme, setTheme } = useTheme();

  return (
    <div className={`theme-switcher ${className}`} role="group" aria-label="Color theme">
      {THEMES.map((t) => (
        <button
          key={t}
          type="button"
          className={`theme-swatch theme-swatch-${t} ${theme === t ? "active" : ""}`}
          onClick={() => setTheme(t)}
          aria-pressed={theme === t}
          title={THEME_LABELS[t]}
        >
          <span className="sr-only">{THEME_LABELS[t]}</span>
        </button>
      ))}
    </div>
  );
}
