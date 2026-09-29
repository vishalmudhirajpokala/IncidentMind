"use client";

import { MoonIcon, SunIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

const STORAGE_KEY = "incidentmind-theme";

export type ThemeChoice = "light" | "dark";

/**
 * Resolve the theme, preferring an explicit choice.
 *
 * Light is the default and the OS setting is deliberately *not* consulted. The
 * interface is built as white and light gray -- a paper console -- and following
 * `prefers-color-scheme` meant that anyone whose OS was set to dark landed on the
 * inverted palette instead, which is not what this design is. The dark palette
 * still exists and is still one click away for a dark room.
 *
 * Kept in sync with the inline script in `app/layout.tsx`, which applies the
 * class before first paint. If the two ever disagree the page flashes, so both
 * read the same key and apply the same rule.
 */
export function resolveStoredTheme(): ThemeChoice | null {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    // Private browsing, or storage disabled. Fall back to the default.
  }
  return null;
}

export function preferredTheme(): ThemeChoice {
  return resolveStoredTheme() ?? "light";
}

export function applyTheme(theme: ThemeChoice): void {
  document.documentElement.classList.toggle("dark", theme === "dark");
}

/**
 * Light/dark switch.
 *
 * Not decoration: a demo room's projector and a judge's laptop are frequently
 * set to opposite schemes, and an incident console that renders badly in the
 * one being projected loses the argument. Light is the default (see
 * `preferredTheme`); dark stays available for a dark room. The button reports
 * the scheme it will switch *to*, not the current one, so its label is never
 * ambiguous.
 */
export function ThemeToggle() {
  // "light" as the initial value, not `preferredTheme()`: it is only ever seen
  // for the frame or two before the effect below runs, and it has to agree with
  // what the pre-paint script already did.
  const [theme, setTheme] = useState<ThemeChoice>("light");
  const [ready, setReady] = useState(false);

  // Read the real theme after mount. Rendering the icon from localStorage
  // during SSR would guess, and a guess that disagrees with the pre-paint
  // script shows the wrong icon for a frame.
  useEffect(() => {
    setTheme(preferredTheme());
    setReady(true);
  }, []);

  function toggle() {
    const next: ThemeChoice = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Choice is still applied for this session; it just will not persist.
    }
  }

  const label = theme === "dark" ? "Light theme" : "Dark theme";

  /*
    `title` rather than a tooltip: the block's sidebar tooltip is keyboard-bound
    and this button already carries an explicit accessible name, so a tooltip
    would add a second, redundant announcement of the same thing. The native
    tooltip is the right tool for hover-only redundancy.
  */
  return (
    <Button
      variant="ghost"
      size="icon"
      className="size-8 shrink-0"
      onClick={toggle}
      title={`Switch to ${label.toLowerCase()}`}
      aria-label={ready ? `Switch to ${label.toLowerCase()}` : "Switch theme"}
    >
      {theme === "dark" ? (
        <SunIcon className="size-4" aria-hidden />
      ) : (
        <MoonIcon className="size-4" aria-hidden />
      )}
    </Button>
  );
}

/**
 * Applies the stored theme before the browser paints.
 *
 * Injected as a raw string rather than a component because a component effect
 * runs after paint, which shows as a white flash on a dark theme. Deliberately
 * tiny and dependency-free.
 *
 * Must stay rule-for-rule identical to `preferredTheme` above, which resolves to
 * "light" when nothing is stored. It does not read `prefers-color-scheme`; the
 * console is a white-and-light-gray design and does not follow the OS into its
 * inverted palette on a first visit.
 */
export const themeBootstrapScript = `(function(){try{var s=localStorage.getItem(${JSON.stringify(
  STORAGE_KEY,
)});var t=(s==="light"||s==="dark")?s:"light";document.documentElement.classList.toggle("dark",t==="dark");}catch(e){}})();`;
