/** Formatlash yordamchilari — barcha joyda bir xil ko'rinish uchun. */

export function formatPrice(value, currency = "UZS", lang = "uz") {
  if (value === null || value === undefined) return null;
  const number = Number(value);
  if (Number.isNaN(number)) return null;

  // Uzun raqamlar bo'sh joy bilan ajratilsa o'qish osonroq: 12 500 000
  const grouped = Math.round(number).toLocaleString("ru-RU").replace(/\u00a0/g, " ");
  if (currency === "USD") return `$${grouped}`;
  const suffix = { uz: "so'm", ru: "сум", en: "UZS" }[lang] || "so'm";
  return `${grouped} ${suffix}`;
}

const RELATIVE_UNITS = [
  { limit: 60, divisor: 1, unit: "second" },
  { limit: 3600, divisor: 60, unit: "minute" },
  { limit: 86400, divisor: 3600, unit: "hour" },
  { limit: 2592000, divisor: 86400, unit: "day" },
  { limit: 31536000, divisor: 2592000, unit: "month" },
];

export function formatRelativeDate(value, lang = "uz") {
  if (!value) return "";
  const date = new Date(value);
  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  const absolute = Math.abs(seconds);

  // Intl.RelativeTimeFormat o'zbek tilini to'liq qo'llab-quvvatlamaydi,
  // shuning uchun uz uchun qo'lda yozamiz.
  if (lang === "uz") return formatRelativeUz(absolute);

  const formatter = new Intl.RelativeTimeFormat(lang, { numeric: "auto" });
  for (const { limit, divisor, unit } of RELATIVE_UNITS) {
    if (absolute < limit) return formatter.format(Math.round(seconds / divisor), unit);
  }
  return formatter.format(Math.round(seconds / 31536000), "year");
}

function formatRelativeUz(seconds) {
  if (seconds < 60) return "hozirgina";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} daqiqa oldin`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} soat oldin`;
  if (seconds < 2592000) return `${Math.floor(seconds / 86400)} kun oldin`;
  if (seconds < 31536000) return `${Math.floor(seconds / 2592000)} oy oldin`;
  return `${Math.floor(seconds / 31536000)} yil oldin`;
}

export function formatDate(value, lang = "uz") {
  if (!value) return "";
  const locale = { uz: "uz-UZ", ru: "ru-RU", en: "en-US" }[lang] || "uz-UZ";
  return new Date(value).toLocaleDateString(locale, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function formatPhone(phone) {
  // +998901234567 -> +998 90 123 45 67
  if (!phone || phone.length !== 13) return phone || "";
  return `${phone.slice(0, 4)} ${phone.slice(4, 6)} ${phone.slice(6, 9)} ${phone.slice(9, 11)} ${phone.slice(11)}`;
}

export function formatCount(value) {
  const number = Number(value) || 0;
  if (number < 1000) return String(number);
  if (number < 1_000_000) return `${(number / 1000).toFixed(number < 10_000 ? 1 : 0)}k`;
  return `${(number / 1_000_000).toFixed(1)}M`;
}
