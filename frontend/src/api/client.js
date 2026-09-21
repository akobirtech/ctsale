/**
 * API klienti.
 *
 * Token strategiyasi:
 *   access  — faqat XOTIRADA (localStorage emas: XSS bo'lsa o'qib olinadi)
 *   refresh — httpOnly cookie, JavaScript ko'ra olmaydi
 *
 * 401 kelganda bitta refresh so'rovi yuboriladi va shu payt kelgan
 * boshqa so'rovlar navbatda kutadi — aks holda bir nechta parallel
 * refresh rotation'ni buzib, foydalanuvchini tizimdan chiqarib
 * yuborardi.
 */

import axios from "axios";

const isServer = typeof window === "undefined";

// SSR paytida to'liq manzil kerak, brauzerda nisbiy yo'l yetarli.
const baseURL = isServer
  ? `${process.env.API_URL || "http://127.0.0.1:8000"}/api/v1`
  : "/api/v1";

export const api = axios.create({
  baseURL,
  withCredentials: true,
  timeout: 20000,
  headers: { Accept: "application/json" },
});

let accessToken = null;
let onUnauthorized = null;

export function setAccessToken(token) {
  accessToken = token || null;
}

export function getAccessToken() {
  return accessToken;
}

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Refresh navbati
let refreshPromise = null;

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${baseURL}/auth/refresh/`, {}, { withCredentials: true })
      .then((response) => {
        setAccessToken(response.data.access);
        return response.data.access;
      })
      .catch((error) => {
        setAccessToken(null);
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;

    // Tarmoq uzilgan yoki server javob bermagan
    if (!response) {
      return Promise.reject(
        normalizeError({ code: "network_error", message: "Internetga ulanishni tekshiring." })
      );
    }

    const isAuthEndpoint = config?.url?.includes("/auth/refresh") || config?.url?.includes("/auth/login");

    if (response.status === 401 && !config._retried && !isAuthEndpoint) {
      config._retried = true;
      try {
        await refreshAccessToken();
        return api(config);
      } catch {
        onUnauthorized?.();
        return Promise.reject(normalizeError(response.data?.error));
      }
    }

    return Promise.reject(normalizeError(response.data?.error, response.status));
  }
);

/**
 * Backend har doim {error: {code, message, details}} qaytaradi.
 * Shu shaklni bir joyda normallashtirib, UI'da faqat `message` va
 * `details` bilan ishlaymiz.
 */
function normalizeError(payload, status) {
  const error = new Error(payload?.message || "Xatolik yuz berdi");
  error.code = payload?.code || "error";
  error.details = payload?.details || {};
  error.status = status;
  return error;
}

/** Maydon darajasidagi xatoni formaga ulash uchun. */
export function fieldErrors(error) {
  const details = error?.details || {};
  const result = {};
  for (const [field, value] of Object.entries(details)) {
    if (field === "detail") continue;
    result[field] = Array.isArray(value) ? value[0] : String(value);
  }
  return result;
}

export { refreshAccessToken };
