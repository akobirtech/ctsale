/**
 * Yengil i18n.
 *
 * Tashqi kutubxona olinmadi: bizga kerak bo'lgani — lug'at, `{param}`
 * o'rniga qiymat qo'yish va URL prefiksi. i18next SSR bilan qo'shimcha
 * sozlash talab qiladi va bundle'ga ~40KB qo'shadi.
 */

import { createContext, useCallback, useContext, useMemo } from "react";

import en from "./en.json";
import ru from "./ru.json";
import uz from "./uz.json";

export const DICTIONARIES = { uz, ru, en };
export const LANGUAGES = ["uz", "ru", "en"];
export const DEFAULT_LANGUAGE = "uz";

export const LANGUAGE_LABELS = {
  uz: { native: "O'zbekcha", short: "UZ" },
  ru: { native: "Русский", short: "RU" },
  en: { native: "English", short: "EN" },
};

const I18nContext = createContext({ lang: DEFAULT_LANGUAGE, t: (key) => key });

/** "a.b.c" yo'li bo'yicha qiymat oladi. */
function lookup(dictionary, key) {
  return key.split(".").reduce((node, part) => (node == null ? undefined : node[part]), dictionary);
}

export function isSupported(lang) {
  return LANGUAGES.includes(lang);
}

/** URL yo'lidan tilni ajratadi: "/ru/product/x" -> "ru" */
export function langFromPath(pathname) {
  const first = (pathname || "/").split("/").filter(Boolean)[0];
  return isSupported(first) ? first : null;
}

/** Yo'ldagi til prefiksini boshqasiga almashtiradi. */
export function switchLangInPath(pathname, nextLang) {
  const segments = (pathname || "/").split("/").filter(Boolean);
  if (isSupported(segments[0])) segments[0] = nextLang;
  else segments.unshift(nextLang);
  return "/" + segments.join("/");
}

export function I18nProvider({ lang, children }) {
  const active = isSupported(lang) ? lang : DEFAULT_LANGUAGE;

  const t = useCallback(
    (key, params) => {
      // Tarjima topilmasa standart tilga, u ham bo'lmasa kalitning
      // o'ziga qaytamiz — sahifa hech qachon bo'sh chiqmasin.
      let text = lookup(DICTIONARIES[active], key);
      if (text == null) text = lookup(DICTIONARIES[DEFAULT_LANGUAGE], key);
      if (text == null) return key;
      if (!params) return text;
      return Object.entries(params).reduce(
        (acc, [name, value]) => acc.replaceAll(`{${name}}`, String(value)),
        text
      );
    },
    [active]
  );

  const value = useMemo(() => ({ lang: active, t }), [active, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}

/** Til prefiksli havola yasaydi: link("/catalog") -> "/uz/catalog" */
export function useLocalePath() {
  const { lang } = useI18n();
  return useCallback(
    (path = "/") => {
      const clean = path.startsWith("/") ? path : `/${path}`;
      return clean === "/" ? `/${lang}` : `/${lang}${clean}`;
    },
    [lang]
  );
}
