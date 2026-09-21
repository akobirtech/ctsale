/** Barcha API chaqiruvlari shu yerda — URL'lar komponentlarga tarqalmasin. */

import { api } from "./client";

export const auth = {
  register: (data) => api.post("/auth/register/", data).then((r) => r.data),
  verify: (data) => api.post("/auth/verify/", data).then((r) => r.data),
  resendOtp: (data) => api.post("/auth/resend-otp/", data).then((r) => r.data),
  login: (data) => api.post("/auth/login/", data).then((r) => r.data),
  refresh: () => api.post("/auth/refresh/").then((r) => r.data),
  logout: () => api.post("/auth/logout/").then((r) => r.data),
  me: () => api.get("/auth/me/").then((r) => r.data),
  updateMe: (data) => api.patch("/auth/me/", data).then((r) => r.data),
  changePassword: (data) => api.post("/auth/password/change/", data).then((r) => r.data),
  resetRequest: (data) => api.post("/auth/password/reset/", data).then((r) => r.data),
  resetConfirm: (data) => api.post("/auth/password/reset/confirm/", data).then((r) => r.data),
};

export const catalog = {
  tree: (lang) => api.get("/categories/tree/", { params: { lang } }).then((r) => r.data),
  category: (slug, lang) => api.get(`/categories/${slug}/`, { params: { lang } }).then((r) => r.data),
  attributes: (slug, lang) =>
    api.get(`/categories/${slug}/attributes/`, { params: { lang } }).then((r) => r.data),
  brands: (params) => api.get("/brands/", { params }).then((r) => r.data),
  popularBrands: () => api.get("/brands/popular/").then((r) => r.data),
  regions: (withDistricts) =>
    api.get("/regions/", { params: { with_districts: withDistricts } }).then((r) => r.data),
};

export const products = {
  list: (params) => api.get("/products/", { params }).then((r) => r.data),
  detail: (slug, lang) => api.get(`/products/${slug}/`, { params: { lang } }).then((r) => r.data),
  search: (params) => api.get("/products/search/", { params }).then((r) => r.data),
  autocomplete: (q) => api.get("/products/autocomplete/", { params: { q } }).then((r) => r.data),
  similar: (slug, lang) => api.get(`/products/${slug}/similar/`, { params: { lang } }).then((r) => r.data),
  featured: (params) => api.get("/products/featured/", { params }).then((r) => r.data),
  revealPhone: (slug) => api.post(`/products/${slug}/reveal-phone/`).then((r) => r.data),

  mine: (params) => api.get("/products/my/", { params }).then((r) => r.data),
  create: (data) => api.post("/products/", data).then((r) => r.data),
  update: (slug, data) => api.patch(`/products/${slug}/`, data).then((r) => r.data),
  remove: (slug) => api.delete(`/products/${slug}/`).then((r) => r.data),
  submit: (slug) => api.post(`/products/${slug}/submit/`).then((r) => r.data),
  markSold: (slug) => api.post(`/products/${slug}/mark-sold/`).then((r) => r.data),
  renew: (slug) => api.post(`/products/${slug}/renew/`).then((r) => r.data),
  setStatus: (slug, status) => api.post(`/products/${slug}/status/`, { status }).then((r) => r.data),
};

export const media = {
  uploadImages: (slug, files, onProgress) => {
    const form = new FormData();
    for (const file of files) form.append("images", file);
    return api
      .post(`/products/${slug}/images/`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (event) => {
          if (onProgress && event.total) {
            onProgress(Math.round((event.loaded * 100) / event.total));
          }
        },
      })
      .then((r) => r.data);
  },
  deleteImage: (slug, id) => api.delete(`/products/${slug}/images/${id}/`).then((r) => r.data),
  setPrimary: (slug, id) => api.post(`/products/${slug}/images/${id}/set-primary/`).then((r) => r.data),
  reorder: (slug, items) => api.post(`/products/${slug}/images/reorder/`, { items }).then((r) => r.data),
  uploadVideo: (slug, file, title) => {
    const form = new FormData();
    form.append("video", file);
    if (title) form.append("title", title);
    return api
      .post(`/products/${slug}/videos/`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
  deleteVideo: (slug, id) => api.delete(`/products/${slug}/videos/${id}/`).then((r) => r.data),
};

export const moderation = {
  queue: (params) => api.get("/moderation/queue/", { params }).then((r) => r.data),
  stats: () => api.get("/moderation/stats/").then((r) => r.data),
  preview: (id) => api.get(`/moderation/${id}/preview/`).then((r) => r.data),
  claim: (id) => api.post(`/moderation/${id}/claim/`).then((r) => r.data),
  approve: (id, note) => api.post(`/moderation/${id}/approve/`, { note }).then((r) => r.data),
  reject: (id, data) => api.post(`/moderation/${id}/reject/`, data).then((r) => r.data),
  bulkApprove: (ids) => api.post("/moderation/bulk-approve/", { task_ids: ids }).then((r) => r.data),
};

export const favorites = {
  list: (params) => api.get("/favorites/", { params }).then((r) => r.data),
  toggle: (slug) => api.post("/favorites/toggle/", { slug }).then((r) => r.data),
  ids: () => api.get("/favorites/ids/").then((r) => r.data),
};

export const reports = {
  reasons: () => api.get("/reports/reasons/").then((r) => r.data),
  create: (data) => api.post("/reports/", data).then((r) => r.data),
  list: (params) => api.get("/reports/", { params }).then((r) => r.data),
  resolve: (id, data) => api.post(`/reports/${id}/resolve/`, data).then((r) => r.data),
};

export const notifications = {
  list: (params) => api.get("/notifications/", { params }).then((r) => r.data),
  unreadCount: () => api.get("/notifications/unread-count/").then((r) => r.data),
  markRead: (id) => api.post(`/notifications/${id}/read/`).then((r) => r.data),
  markAllRead: () => api.post("/notifications/read-all/").then((r) => r.data),
  preferences: () => api.get("/notifications/preferences/").then((r) => r.data),
  updatePreferences: (data) =>
    api.patch("/notifications/preferences/", data).then((r) => r.data),
};

export const compare = {
  items: (slugs, lang) =>
    api.get("/compare/items/", { params: { slugs: slugs.join(","), lang } }).then((r) => r.data),
};
