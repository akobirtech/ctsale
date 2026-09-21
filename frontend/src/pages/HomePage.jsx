import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Search, Send, ShieldCheck, Zap } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { products as productsApi } from "../api/endpoints";
import ProductGrid from "../components/product/ProductGrid";
import { useI18n, useLocalePath } from "../i18n";
import { useHead } from "../seo/Head";
import { useRouteData } from "../store/routeData";

function Section({ title, viewAllTo, children }) {
  const { t } = useI18n();
  return (
    <section className="mt-10">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-lg font-bold sm:text-xl">{title}</h2>
        {viewAllTo ? (
          <Link
            to={viewAllTo}
            className="flex shrink-0 items-center gap-1 text-sm font-semibold"
            style={{ color: "var(--accent)" }}
          >
            {t("home.viewAll")}
            <ArrowRight size={15} aria-hidden="true" />
          </Link>
        ) : null}
      </div>
      {children}
    </section>
  );
}

export default function HomePage() {
  const { t, lang } = useI18n();
  const localePath = useLocalePath();
  const navigate = useNavigate();
  const preloaded = useRouteData("home");

  const [query, setQuery] = useState("");

  const { data: blocks, isLoading } = useQuery({
    queryKey: ["home-blocks", lang],
    queryFn: () => productsApi.featured({ limit: 8, lang }),
    initialData: preloaded?.blocks,
    staleTime: 5 * 60_000,
  });

  const categories = preloaded?.categories || [];
  const featuredCategories = categories.filter((category) => category.is_featured).slice(0, 8);

  useHead({
    title: `${t("brand.name")} — ${t("brand.tagline")}`,
    description: t("home.heroSubtitle"),
    robots: "index, follow",
    canonical: undefined,
    og: {
      type: "website",
      title: `${t("brand.name")} — ${t("brand.tagline")}`,
      description: t("home.heroSubtitle"),
      site_name: t("brand.name"),
    },
  });

  function submitSearch(event) {
    event.preventDefault();
    const value = query.trim();
    if (value.length < 2) return;
    navigate(`${localePath("/search")}?q=${encodeURIComponent(value)}`);
  }

  return (
    <>
      {/* Hero */}
      <section
        className="border-b"
        style={{
          background:
            "linear-gradient(180deg, var(--accent-soft) 0%, var(--bg) 100%)",
        }}
      >
        <div className="container-page py-10 text-center sm:py-14">
          <h1 className="mx-auto max-w-2xl text-[26px] font-extrabold leading-tight sm:text-4xl">
            {t("home.heroTitle")}
          </h1>
          <p
            className="mx-auto mt-3 max-w-xl text-sm sm:text-base"
            style={{ color: "var(--text-muted)" }}
          >
            {t("home.heroSubtitle")}
          </p>

          <form onSubmit={submitSearch} className="mx-auto mt-6 flex max-w-xl gap-2" role="search">
            <label htmlFor="hero-search" className="sr-only">
              {t("nav.search")}
            </label>
            <div className="relative flex-1">
              <Search
                size={18}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2"
                style={{ color: "var(--text-subtle)" }}
                aria-hidden="true"
              />
              <input
                id="hero-search"
                type="search"
                className="input pl-10"
                placeholder={t("home.searchPlaceholder")}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-primary">
              {t("nav.search")}
            </button>
          </form>

          <ul
            className="mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            <li className="flex items-center gap-1.5">
              <ShieldCheck size={15} aria-hidden="true" />
              Har bir e&apos;lon moderatsiyadan o&apos;tadi
            </li>
            <li className="flex items-center gap-1.5">
              <Send size={15} aria-hidden="true" />
              Telegram kanalda avtomatik e&apos;lon
            </li>
            <li className="flex items-center gap-1.5">
              <Zap size={15} aria-hidden="true" />
              E&apos;lon joylash bepul
            </li>
          </ul>
        </div>
      </section>

      <div className="container-page pb-4">
        {/* Kategoriyalar */}
        {featuredCategories.length > 0 ? (
          <Section title={t("home.popularCategories")} viewAllTo={localePath("/catalog")}>
            <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4 lg:grid-cols-8">
              {featuredCategories.map((category) => (
                <Link
                  key={category.slug}
                  to={localePath(`/category/${category.slug}`)}
                  className="surface flex flex-col items-center gap-1.5 px-2 py-4 text-center transition-colors hover:bg-[var(--surface-hover)]"
                >
                  <span className="line-clamp-2 text-xs font-semibold leading-tight">
                    {category.name}
                  </span>
                  <span className="text-[11px]" style={{ color: "var(--text-subtle)" }}>
                    {category.products_count}
                  </span>
                </Link>
              ))}
            </div>
          </Section>
        ) : null}

        {blocks?.featured?.length ? (
          <Section title={t("home.featured")} viewAllTo={`${localePath("/catalog")}?is_featured=true`}>
            <ProductGrid products={blocks.featured} loading={isLoading} skeletonCount={4} />
          </Section>
        ) : null}

        <Section title={t("home.newest")} viewAllTo={`${localePath("/catalog")}?sort=newest`}>
          <ProductGrid products={blocks?.newest || []} loading={isLoading} />
        </Section>

        <Section title={t("home.popular")} viewAllTo={`${localePath("/catalog")}?sort=most_viewed`}>
          <ProductGrid products={blocks?.popular || []} loading={isLoading} />
        </Section>

        <Section title={t("home.used")} viewAllTo={`${localePath("/catalog")}?is_new=false`}>
          <ProductGrid products={blocks?.used || []} loading={isLoading} />
        </Section>

        {/* CTA */}
        <section
          className="mt-12 rounded-2xl px-6 py-10 text-center"
          style={{ background: "var(--accent-soft)" }}
        >
          <h2 className="text-xl font-bold sm:text-2xl">{t("home.ctaTitle")}</h2>
          <p
            className="mx-auto mt-2 max-w-md text-sm"
            style={{ color: "var(--text-muted)" }}
          >
            {t("home.ctaText")}
          </p>
          <Link to={localePath("/seller/products/new")} className="btn btn-primary mt-5">
            {t("home.ctaButton")}
          </Link>
        </section>
      </div>
    </>
  );
}
