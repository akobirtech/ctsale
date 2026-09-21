/** Yorug'/quyuq mavzu. Tanlov localStorage'da — bu maxfiy ma'lumot emas. */

import { create } from "zustand";

const STORAGE_KEY = "ctsale-theme";

function readStored() {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "dark" || value === "light" ? value : "system";
  } catch {
    // Private rejimda localStorage istisno otishi mumkin.
    return "system";
  }
}

export const useThemeStore = create((set, get) => ({
  theme: "system",

  init() {
    if (typeof window === "undefined") return;
    const theme = readStored();
    set({ theme });
    get().apply(theme);
  },

  apply(theme) {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
  },

  set(theme) {
    set({ theme });
    get().apply(theme);
    try {
      if (theme === "system") localStorage.removeItem(STORAGE_KEY);
      else localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Saqlab bo'lmasa ham mavzu joriy sessiyada ishlaydi.
    }
  },

  toggle() {
    const current = get().theme;
    const resolved =
      current === "system"
        ? window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"
        : current;
    get().set(resolved === "dark" ? "light" : "dark");
  },
}));
