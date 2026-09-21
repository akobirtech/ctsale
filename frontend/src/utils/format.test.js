/** Formatlash yordamchilari — narx, sana, telefon, sonlar. */

import { describe, expect, it, vi } from "vitest";

import { formatCount, formatDate, formatPhone, formatPrice, formatRelativeDate } from "./format";

describe("formatPrice", () => {
  it("uzun raqamni bo'sh joy bilan ajratadi", () => {
    // 12500000 o'qib bo'lmaydigan raqam; 12 500 000 esa bir qarashda tushunarli.
    expect(formatPrice(12500000)).toBe("12 500 000 so'm");
  });

  it("valyutaga qarab qo'shimchani almashtiradi", () => {
    expect(formatPrice(1000, "UZS", "ru")).toBe("1 000 сум");
    expect(formatPrice(1000, "UZS", "en")).toBe("1 000 UZS");
  });

  it("dollarni belgi bilan ko'rsatadi", () => {
    expect(formatPrice(750, "USD")).toBe("$750");
  });

  it("narx yo'q bo'lsa null qaytaradi", () => {
    // Sahifa "Kelishiladi" deb yozishi uchun null kerak, "0" emas.
    expect(formatPrice(null)).toBeNull();
    expect(formatPrice(undefined)).toBeNull();
    expect(formatPrice("kelishiladi")).toBeNull();
  });

  it("nolni narx deb qabul qiladi", () => {
    expect(formatPrice(0)).toBe("0 so'm");
  });

  it("kasrni yaxlitlaydi", () => {
    expect(formatPrice("1999.6")).toBe("2 000 so'm");
  });
});

describe("formatRelativeDate", () => {
  const now = new Date("2026-09-21T12:00:00Z");

  function at(iso) {
    vi.setSystemTime(now);
    return formatRelativeDate(iso);
  }

  it.each([
    ["2026-09-21T11:59:30Z", "hozirgina"],
    ["2026-09-21T11:30:00Z", "30 daqiqa oldin"],
    ["2026-09-21T09:00:00Z", "3 soat oldin"],
    ["2026-09-18T12:00:00Z", "3 kun oldin"],
    ["2026-07-21T12:00:00Z", "2 oy oldin"],
    ["2024-09-21T12:00:00Z", "2 yil oldin"],
  ])("%s -> %s", (iso, expected) => {
    expect(at(iso)).toBe(expected);
    vi.useRealTimers();
  });

  it("bo'sh qiymatda bo'sh satr", () => {
    expect(formatRelativeDate(null)).toBe("");
  });

  it("ruscha uchun Intl ishlatadi", () => {
    vi.setSystemTime(now);
    expect(formatRelativeDate("2026-09-20T12:00:00Z", "ru")).toMatch(/вчера|дн/i);
    vi.useRealTimers();
  });
});

describe("formatPhone", () => {
  it("o'zbek raqamini bo'laklarga ajratadi", () => {
    expect(formatPhone("+998901234567")).toBe("+998 90 123 45 67");
  });

  it("noto'g'ri uzunlikda tegmaydi", () => {
    // Formatlash o'rniga buzib ko'rsatgandan ko'ra asl holida qoldirgan afzal.
    expect(formatPhone("+99890")).toBe("+99890");
    expect(formatPhone(null)).toBe("");
  });
});

describe("formatCount", () => {
  it.each([
    [0, "0"],
    [999, "999"],
    [1000, "1.0k"],
    [9999, "10.0k"],
    [12000, "12k"],
    [1500000, "1.5M"],
  ])("%s -> %s", (value, expected) => {
    expect(formatCount(value)).toBe(expected);
  });

  it("son bo'lmagan qiymatda yiqilmaydi", () => {
    expect(formatCount(undefined)).toBe("0");
    expect(formatCount("abc")).toBe("0");
  });
});

describe("formatDate", () => {
  it("tilga qarab formatlaydi", () => {
    expect(formatDate("2026-03-15T00:00:00Z", "en")).toContain("2026");
    expect(formatDate("")).toBe("");
  });
});
