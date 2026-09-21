/**
 * Marshrutlar va ularning ma'lumot yuklovchilari.
 *
 * Har bir marshrut ixtiyoriy `loader` ga ega: SSR paytida u render'dan
 * OLDIN chaqiriladi va natija `window.__INITIAL_DATA__` orqali brauzerga
 * uzatiladi. Shu sababli crawler to'liq HTML ko'radi va brauzer
 * hydrate paytida qayta so'rov yubormaydi.
 */

import { lazy } from "react";

import { catalog, products } from "./api/endpoints";

// Bosh, katalog va mahsulot sahifalari SSR uchun darhol kerak —
// ularni lazy qilmaymiz, aks holda birinchi render kechikadi.
import CatalogPage from "./pages/CatalogPage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";
import ProductPage from "./pages/ProductPage";

// Qolganlari faqat kerak bo'lganda yuklanadi.
const LoginPage = lazy(() => import("./pages/LoginPage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));
const PasswordResetPage = lazy(() => import("./pages/PasswordResetPage"));
const FavoritesPage = lazy(() => import("./pages/FavoritesPage"));
const ProfilePage = lazy(() => import("./pages/ProfilePage"));
const SellerProductsPage = lazy(() => import("./pages/seller/SellerProductsPage"));
const ProductFormPage = lazy(() => import("./pages/seller/ProductFormPage"));
const AdminDashboardPage = lazy(() => import("./pages/admin/AdminDashboardPage"));
const ModerationPage = lazy(() => import("./pages/admin/ModerationPage"));

export const routes = [
  {
    id: "home",
    path: "",
    Component: HomePage,
    loader: async ({ lang }) => ({
      blocks: await products.featured({ limit: 8, lang }),
      categories: await catalog.tree(lang),
    }),
  },
  {
    id: "catalog",
    path: "catalog",
    Component: CatalogPage,
    loader: async ({ lang, query }) => ({
      page: await products.list({ ...query, lang, facets: "true" }),
      categories: await catalog.tree(lang),
    }),
  },
  {
    id: "category",
    path: "category/:slug",
    Component: CatalogPage,
    loader: async ({ lang, params, query }) => ({
      page: await products.list({ ...query, category: params.slug, lang, facets: "true" }),
      categories: await catalog.tree(lang),
      category: await catalog.category(params.slug, lang).catch(() => null),
    }),
  },
  {
    id: "search",
    path: "search",
    Component: CatalogPage,
    loader: async ({ lang, query }) => {
      if (!query.q || query.q.length < 2) {
        return { page: { count: 0, results: [] }, categories: await catalog.tree(lang) };
      }
      return {
        page: await products.search({ ...query, lang }).catch(() => ({ count: 0, results: [] })),
        categories: await catalog.tree(lang),
      };
    },
  },
  {
    id: "product",
    path: "product/:slug",
    Component: ProductPage,
    loader: async ({ lang, params }) => {
      const product = await products.detail(params.slug, lang);
      // O'xshash mahsulotlar sahifani bloklamasin — xato bo'lsa bo'sh.
      const similar = await products.similar(params.slug, lang).catch(() => []);
      return { product, similar };
    },
    // Slug o'zgargan bo'lsa backend eski slug bo'yicha ham javob beradi.
    // Ikki manzilda bir xil kontent turmasligi uchun eskisidan 301 qilamiz.
    canonicalPath: (data, { lang }) =>
      data?.product?.slug ? `/${lang}/product/${data.product.slug}` : null,
  },
  { id: "login", path: "login", Component: LoginPage },
  { id: "register", path: "register", Component: RegisterPage },
  { id: "password-reset", path: "password-reset", Component: PasswordResetPage },
  { id: "favorites", path: "favorites", Component: FavoritesPage, private: true },
  { id: "profile", path: "profile", Component: ProfilePage, private: true },
  { id: "seller-products", path: "seller/products", Component: SellerProductsPage, private: true },
  { id: "seller-new", path: "seller/products/new", Component: ProductFormPage, private: true },
  { id: "seller-edit", path: "seller/products/:slug/edit", Component: ProductFormPage, private: true },
  { id: "admin", path: "admin", Component: AdminDashboardPage, private: true, staff: true },
  { id: "admin-moderation", path: "admin/moderation", Component: ModerationPage, private: true, staff: true },
  { id: "not-found", path: "*", Component: NotFoundPage },
];

/** SSR uchun: URL yo'liga mos marshrutni topadi. */
export function matchRoute(pathname, lang) {
  const prefix = `/${lang}`;
  let rest = pathname.startsWith(prefix) ? pathname.slice(prefix.length) : pathname;
  rest = rest.replace(/^\/+/, "").replace(/\/+$/, "");

  for (const route of routes) {
    if (route.path === "*") continue;
    const params = matchPattern(route.path, rest);
    if (params) return { route, params };
  }
  return { route: routes.find((r) => r.path === "*"), params: {} };
}

function matchPattern(pattern, pathname) {
  const patternParts = pattern === "" ? [] : pattern.split("/");
  const pathParts = pathname === "" ? [] : pathname.split("/");
  if (patternParts.length !== pathParts.length) return null;

  const params = {};
  for (let i = 0; i < patternParts.length; i += 1) {
    const expected = patternParts[i];
    const actual = pathParts[i];
    if (expected.startsWith(":")) {
      if (!actual) return null;
      params[expected.slice(1)] = decodeURIComponent(actual);
    } else if (expected !== actual) {
      return null;
    }
  }
  return params;
}
