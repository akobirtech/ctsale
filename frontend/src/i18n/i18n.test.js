/** Til aniqlash, almashtirish va lug'at to'liqligi. */

import { describe, expect, it } from "vitest";

import { DICTIONARIES, LANGUAGES, isSupported, langFromPath, switchLangInPath } from "./index";

describe("langFromPath", () => {
  it.each([
    ["/uz/product/x", "uz"],
    ["/ru", "ru"],
    ["/en/catalog?q=1", "en"],
  ])("%s -> %s", (path, expected) => {
    expect(langFromPath(path)).toBe(expected);
  });

  it("prefiks bo'lmasa null qaytaradi", () => {
    // SSR shu holatda standart tilga yo'naltiradi.
    expect(langFromPath("/catalog")).toBeNull();
    expect(langFromPath("/")).toBeNull();
  });

  it("o'xshash, lekin noto'g'ri prefiksni qabul qilmaydi", () => {
    expect(langFromPath("/uzbek/catalog")).toBeNull();
  });
});

describe("switchLangInPath", () => {
  it("mavjud prefiksni almashtiradi", () => {
    expect(switchLangInPath("/uz/product/asus", "ru")).toBe("/ru/product/asus");
  });

  it("prefiks bo'lmasa qo'shadi", () => {
    expect(switchLangInPath("/catalog", "en")).toBe("/en/catalog");
  });

  it("ildizni ham ishlaydi", () => {
    expect(switchLangInPath("/", "ru")).toBe("/ru");
  });
});

describe("lug'atlar", () => {
  /** "a.b.c" ko'rinishidagi barcha kalitlarni yig'adi. */
  function keysOf(node, prefix = "") {
    return Object.entries(node).flatMap(([key, value]) =>
      typeof value === "object" && value !== null
        ? keysOf(value, `${prefix}${key}.`)
        : [`${prefix}${key}`]
    );
  }

  const reference = keysOf(DICTIONARIES.uz);

  it.each(LANGUAGES.filter((lang) => lang !== "uz"))(
    "%s tilida yetishmayotgan kalit yo'q",
    (lang) => {
      const missing = reference.filter((key) => !keysOf(DICTIONARIES[lang]).includes(key));

      // Bitta yetishmagan kalit sahifada o'zbekcha matn chiqishiga
      // olib keladi — buni ko'z bilan payqash qiyin.
      expect(missing).toEqual([]);
    }
  );

  it("bo'sh tarjima yo'q", () => {
    const empty = LANGUAGES.flatMap((lang) =>
      keysOf(DICTIONARIES[lang])
        .filter((key) => {
          const value = key.split(".").reduce((node, part) => node?.[part], DICTIONARIES[lang]);
          return typeof value === "string" && value.trim() === "";
        })
        .map((key) => `${lang}:${key}`)
    );

    expect(empty).toEqual([]);
  });

  it("{param} o'rnini almashtiruvchilar barcha tillarda bir xil", () => {
    const placeholders = (text) => (text.match(/\{[a-z]+\}/gi) || []).sort().join(",");

    const mismatched = reference.filter((key) => {
      const get = (lang) => key.split(".").reduce((node, part) => node?.[part], DICTIONARIES[lang]);
      const base = get("uz");
      if (typeof base !== "string") return false;
      return LANGUAGES.some((lang) => {
        const value = get(lang);
        return typeof value === "string" && placeholders(value) !== placeholders(base);
      });
    });

    // Ruscha matnda {count} unutilsa, son umuman ko'rinmaydi.
    expect(mismatched).toEqual([]);
  });
});

describe("isSupported", () => {
  it("faqat ro'yxatdagi tillarni tan oladi", () => {
    expect(isSupported("uz")).toBe(true);
    expect(isSupported("de")).toBe(false);
    expect(isSupported(undefined)).toBe(false);
  });
});
