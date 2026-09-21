/**
 * Autentifikatsiya holati.
 *
 * Access token XOTIRADA (zustand ichida) saqlanadi — localStorage'ga
 * yozilmaydi, chunki XSS bo'lganda u darhol o'g'irlanadi. Sahifa
 * yangilanganda sessiya httpOnly refresh cookie orqali tiklanadi.
 */

import { create } from "zustand";

import { auth as authApi } from "../api/endpoints";
import { setAccessToken, setUnauthorizedHandler } from "../api/client";

export const useAuthStore = create((set, get) => ({
  user: null,
  status: "idle", // idle | loading | authenticated | anonymous
  permissions: new Set(),

  isAuthenticated: () => get().status === "authenticated",

  can(code) {
    const { user, permissions } = get();
    if (!user) return false;
    if (user.is_superuser) return true;
    return permissions.has(code);
  },

  setSession(payload) {
    if (payload?.access) setAccessToken(payload.access);
    const user = payload?.user ?? null;
    set({
      user,
      status: user ? "authenticated" : "anonymous",
      permissions: new Set(user?.permissions || []),
    });
  },

  /** Sahifa ochilganda sessiyani tiklaydi. */
  async restore() {
    if (get().status === "loading") return;
    set({ status: "loading" });
    try {
      const { access } = await authApi.refresh();
      setAccessToken(access);
      const user = await authApi.me();
      set({ user, status: "authenticated", permissions: new Set(user.permissions || []) });
    } catch {
      setAccessToken(null);
      set({ user: null, status: "anonymous", permissions: new Set() });
    }
  },

  async login(credentials) {
    const payload = await authApi.login(credentials);
    get().setSession(payload);
    return payload.user;
  },

  async logout() {
    try {
      await authApi.logout();
    } finally {
      setAccessToken(null);
      set({ user: null, status: "anonymous", permissions: new Set() });
    }
  },

  updateUser(patch) {
    set((state) => ({ user: state.user ? { ...state.user, ...patch } : null }));
  },
}));

// Refresh ham muvaffaqiyatsiz bo'lsa holatni tozalaymiz.
if (typeof window !== "undefined") {
  setUnauthorizedHandler(() => {
    setAccessToken(null);
    useAuthStore.setState({ user: null, status: "anonymous", permissions: new Set() });
  });
}
