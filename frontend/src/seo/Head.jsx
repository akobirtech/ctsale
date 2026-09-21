/**
 * `<head>` boshqaruvi — SSR va brauzer uchun bitta API.
 *
 * react-helmet-async olinmadi: bizga kerak bo'lgani juda sodda —
 * sahifa o'z meta ma'lumotini e'lon qiladi, server uni HTML'ga
 * qo'yadi, brauzer esa navigatsiyada yangilaydi.
 *
 * Muhim: backend `seo` obyektini tayyor holda beradi (canonical,
 * hreflang, OG, JSON-LD). Shunda sitemap, sahifa va Telegram posti
 * bitta manbadan foydalanadi va bir-biriga zid bo'lmaydi.
 */

import { createContext, useContext, useEffect } from "react";

const HeadContext = createContext(null);

export function HeadCollector({ store, children }) {
  return <HeadContext.Provider value={store}>{children}</HeadContext.Provider>;
}

function escapeAttr(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** JSON-LD ichida `</script>` bo'lsa HTML'ni buzadi — buni to'sib qo'yamiz. */
function safeJson(data) {
  return JSON.stringify(data).replace(/</g, "\\u003c");
}

export function renderHeadToString(store) {
  const parts = [];
  const { title, meta = [], link = [], jsonld = [] } = store;

  if (title) parts.push(`<title>${escapeAttr(title)}</title>`);

  for (const tag of meta) {
    const key = tag.property ? "property" : "name";
    const keyValue = tag.property || tag.name;
    if (!keyValue || tag.content == null) continue;
    parts.push(`<meta ${key}="${escapeAttr(keyValue)}" content="${escapeAttr(tag.content)}">`);
  }

  for (const tag of link) {
    const attrs = Object.entries(tag)
      .map(([name, value]) => `${name}="${escapeAttr(value)}"`)
      .join(" ");
    parts.push(`<link ${attrs}>`);
  }

  for (const data of jsonld) {
    parts.push(`<script type="application/ld+json">${safeJson(data)}</script>`);
  }

  return parts.join("\n    ");
}

/**
 * Sahifa meta ma'lumotini e'lon qiladi.
 *
 * @param {object} seo - backenddagi `seo` obyekti yoki qo'lda tuzilgan
 */
export function useHead(seo) {
  const store = useContext(HeadContext);

  // Server: to'plamga yozamiz (render paytida, effektsiz).
  if (store && typeof window === "undefined" && seo) {
    applyToStore(store, seo);
  }

  useEffect(() => {
    if (!seo || typeof document === "undefined") return;
    applyToDocument(seo);
  }, [seo]);
}

function buildTags(seo) {
  const meta = [];
  const link = [];

  if (seo.description) meta.push({ name: "description", content: seo.description });
  if (seo.keywords) meta.push({ name: "keywords", content: seo.keywords });
  if (seo.robots) meta.push({ name: "robots", content: seo.robots });

  const og = seo.og || {};
  if (og.title) meta.push({ property: "og:title", content: og.title });
  if (og.description) meta.push({ property: "og:description", content: og.description });
  if (og.type) meta.push({ property: "og:type", content: og.type });
  if (og.url) meta.push({ property: "og:url", content: og.url });
  if (og.image) meta.push({ property: "og:image", content: og.image });
  if (og.site_name) meta.push({ property: "og:site_name", content: og.site_name });
  if (og.locale) meta.push({ property: "og:locale", content: og.locale });

  const twitter = seo.twitter || {};
  if (twitter.card) meta.push({ name: "twitter:card", content: twitter.card });
  if (twitter.title) meta.push({ name: "twitter:title", content: twitter.title });
  if (twitter.description) meta.push({ name: "twitter:description", content: twitter.description });
  if (twitter.image) meta.push({ name: "twitter:image", content: twitter.image });

  for (const [name, content] of Object.entries(seo.verification || {})) {
    meta.push({ name, content });
  }

  if (seo.canonical) link.push({ rel: "canonical", href: seo.canonical });
  for (const alternate of seo.hreflang || []) {
    link.push({ rel: "alternate", hreflang: alternate.hreflang, href: alternate.href });
  }

  return { meta, link, jsonld: seo.jsonld || [] };
}

function applyToStore(store, seo) {
  const { meta, link, jsonld } = buildTags(seo);
  store.title = seo.title || store.title;
  store.meta = meta;
  store.link = link;
  store.jsonld = jsonld;
}

function applyToDocument(seo) {
  const { meta, link, jsonld } = buildTags(seo);

  if (seo.title) document.title = seo.title;

  // Oldingi sahifadan qolganlarini tozalaymiz, aks holda SPA
  // navigatsiyasida meta teglar to'planib ketadi.
  document.querySelectorAll("[data-head]").forEach((node) => node.remove());

  const fragment = document.createDocumentFragment();

  for (const tag of meta) {
    const element = document.createElement("meta");
    if (tag.property) element.setAttribute("property", tag.property);
    else element.setAttribute("name", tag.name);
    element.setAttribute("content", tag.content ?? "");
    element.setAttribute("data-head", "");
    fragment.appendChild(element);
  }

  for (const tag of link) {
    const element = document.createElement("link");
    for (const [name, value] of Object.entries(tag)) element.setAttribute(name, value);
    element.setAttribute("data-head", "");
    fragment.appendChild(element);
  }

  for (const data of jsonld) {
    const element = document.createElement("script");
    element.type = "application/ld+json";
    element.textContent = safeJson(data);
    element.setAttribute("data-head", "");
    fragment.appendChild(element);
  }

  document.head.appendChild(fragment);
}
