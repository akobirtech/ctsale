import { Link } from "react-router-dom";
import { Send } from "lucide-react";

import { useI18n, useLocalePath } from "../../i18n";

export default function Footer({ categories = [] }) {
  const { t } = useI18n();
  const localePath = useLocalePath();
  const year = new Date().getFullYear();

  return (
    <footer className="mt-16 border-t" style={{ background: "var(--bg-subtle)" }}>
      <div className="container-page py-10">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="flex items-center gap-2">
              <span
                className="flex h-9 w-9 items-center justify-center rounded-xl text-sm font-black"
                style={{ background: "var(--accent)", color: "var(--accent-text)" }}
                aria-hidden="true"
              >
                CT
              </span>
              <span className="text-base font-bold">{t("brand.name")}</span>
            </div>
            <p className="mt-3 text-sm" style={{ color: "var(--text-muted)" }}>
              {t("brand.tagline")}
            </p>
            <a
              href="https://t.me/notbuk_sot"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary btn-sm mt-4"
            >
              <Send size={15} aria-hidden="true" />
              Telegram kanal
            </a>
          </div>

          <nav aria-labelledby="footer-categories">
            <h2 id="footer-categories" className="mb-3 text-sm font-semibold">
              {t("nav.categories")}
            </h2>
            <ul className="space-y-2 text-sm" style={{ color: "var(--text-muted)" }}>
              {categories.slice(0, 6).map((category) => (
                <li key={category.slug}>
                  <Link className="hover:underline" to={localePath(`/category/${category.slug}`)}>
                    {category.name}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <nav aria-labelledby="footer-links">
            <h2 id="footer-links" className="mb-3 text-sm font-semibold">
              {t("catalog.title")}
            </h2>
            <ul className="space-y-2 text-sm" style={{ color: "var(--text-muted)" }}>
              <li>
                <Link className="hover:underline" to={localePath("/catalog")}>
                  {t("catalog.title")}
                </Link>
              </li>
              <li>
                <Link className="hover:underline" to={`${localePath("/catalog")}?is_new=true`}>
                  {t("condition.new")}
                </Link>
              </li>
              <li>
                <Link className="hover:underline" to={`${localePath("/catalog")}?is_new=false`}>
                  {t("home.used")}
                </Link>
              </li>
              <li>
                <Link className="hover:underline" to={localePath("/seller/products/new")}>
                  {t("nav.sell")}
                </Link>
              </li>
            </ul>
          </nav>

          <div>
            <h2 className="mb-3 text-sm font-semibold">{t("nav.profile")}</h2>
            <ul className="space-y-2 text-sm" style={{ color: "var(--text-muted)" }}>
              <li>
                <Link className="hover:underline" to={localePath("/login")}>
                  {t("nav.login")}
                </Link>
              </li>
              <li>
                <Link className="hover:underline" to={localePath("/register")}>
                  {t("nav.register")}
                </Link>
              </li>
              <li>
                <Link className="hover:underline" to={localePath("/favorites")}>
                  {t("nav.favorites")}
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div
          className="mt-8 flex flex-col gap-2 border-t pt-6 text-xs sm:flex-row sm:items-center sm:justify-between"
          style={{ color: "var(--text-subtle)" }}
        >
          <p>
            &copy; {year} {t("brand.name")}
          </p>
          <p>Toshkent, O&apos;zbekiston</p>
        </div>
      </div>
    </footer>
  );
}
