import { useCallback, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ChevronRight, SlidersHorizontal, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { products as productsApi } from "../api/endpoints";
import FilterPanel from "../components/filters/FilterPanel";
import ProductGrid from "../components/product/ProductGrid";
import ErrorState from "../components/ui/ErrorState";
import { useI18n, useLocalePath } from "../i18n";
import { useHead } from "../seo/Head";
import { useRouteData } from "../store/routeData";

const SORT_KEYS = ["newest", "price_asc", "price_desc", "popular", "most_viewed", "oldest"];

export default function CatalogPage() {
  const { t, lang } = useI18n();
  const localePath = useLocalePath();
  const navigate = useNavigate();
  const location = useLocation();
  const { slug } = useParams();
  const [searchParams] = useSearchParams();

  const [drawerOpen, setDrawerOpen] = useState(false);

  const isSearch = location.pathname.endsWith("/search");
  const routeId = isSearch ? "search" : slug ? "category" : "catalog";
  const preloaded = useRouteData(routeId);

  // URL — yagona haqiqat manbasi. Filtr holati alohida saqlanmaydi,
  // shuning uchun orqaga tugmasi va havola ulashish to'g'ri ishlaydi.
  const params = useMemo(() => Object.fromEntries(searchParams.entries()), [searchParams]);

  const queryParams = useMemo(
    () => ({ ...params, lang, facets: "true", ...(slug ? { category: slug } : {}) }),
    [params, lang, slug]
  );

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["catalog", routeId, slug, params, lang],
    queryFn: () =>
      isSearch ? productsApi.search(queryParams) : productsApi.list(queryParams),
    initialData: preloaded?.page,
    placeholderData: (previous) => previous,
    enabled: !isSearch || (params.q || "").length >= 2,
  });

  const category = preloaded?.category;
  const results = data?.results || [];
  const facets = data?.facets || {};

  const title = isSearch
    ? `${t("nav.search")}: ${params.q || ""}`
    : category?.name || t("catalog.title");

  useHead({
    title: `${title} — ${t("brand.name")}`,
    description: category?.meta_description || t("home.heroSubtitle"),
    // Filtrlangan va sahifalangan ko'rinishlar indekslanmaydi —
    // aks holda minglab deyarli bir xil sahifa hosil bo'ladi.
    robots:
      isSearch || Object.keys(params).some((key) => key !== "sort")
        ? "noindex, follow"
        : "index, follow",
  });

  const updateParams = useCallback(
    (next) => {
      const search = new URLSearchParams();
      for (const [key, value] of Object.entries(next)) {
        if (value !== undefined && value !== null && value !== "") search.set(key, value);
      }
      navigate(`${location.pathname}?${search.toString()}`, { replace: false });
    },
    [navigate, location.pathname]
  );

  const clearFilters = useCallback(() => {
    const keep = new URLSearchParams();
    if (params.q) keep.set("q", params.q);
    if (params.sort) keep.set("sort", params.sort);
    navigate(`${location.pathname}?${keep.toString()}`);
  }, [navigate, location.pathname, params.q, params.sort]);

  const goToPage = (page) => updateParams({ ...params, page: page > 1 ? page : undefined });

  if (isError) {
    return (
      <div className="container-page py-10">
        <ErrorState
          title={t("error.generic")}
          description={error?.message}
          onRetry={refetch}
        />
      </div>
    );
  }

  return (
    <div className="container-page py-5">
      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="mb-3">
        <ol className="flex flex-wrap items-center gap-1 text-xs" style={{ color: "var(--text-muted)" }}>
          <li>
            <Link to={localePath("/")} className="hover:underline">
              {t("nav.home")}
            </Link>
          </li>
          {(category?.breadcrumbs || []).map((crumb) => (
            <li key={crumb.slug} className="flex items-center gap-1">
              <ChevronRight size={12} aria-hidden="true" />
              <Link to={localePath(`/category/${crumb.slug}`)} className="hover:underline">
                {crumb.name}
              </Link>
            </li>
          ))}
        </ol>
      </nav>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl font-bold sm:text-2xl">{title}</h1>
          <p className="mt-0.5 text-sm" style={{ color: "var(--text-muted)" }}>
            {t("catalog.results", { count: data?.count ?? 0 })}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn btn-secondary btn-sm lg:hidden"
            onClick={() => setDrawerOpen(true)}
          >
            <SlidersHorizontal size={15} aria-hidden="true" />
            {t("catalog.filters")}
          </button>

          <label htmlFor="sort" className="sr-only">
            {t("catalog.sort")}
          </label>
          <select
            id="sort"
            className="input h-9 min-h-9 w-auto py-0 text-sm"
            value={params.sort || "newest"}
            onChange={(event) => updateParams({ ...params, sort: event.target.value, page: undefined })}
          >
            {SORT_KEYS.map((key) => (
              <option key={key} value={key}>
                {t(`sort.${key}`)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Natija yo'q bo'lsa takliflar */}
      {isSearch && data?.suggestions?.length ? (
        <div className="surface mb-4 p-3 text-sm">
          <span style={{ color: "var(--text-muted)" }}>{t("empty.searchHint")}: </span>
          {data.suggestions.map((suggestion, index) => (
            <span key={suggestion}>
              {index > 0 ? ", " : ""}
              <Link
                to={`${localePath("/search")}?q=${encodeURIComponent(suggestion)}`}
                className="font-semibold hover:underline"
                style={{ color: "var(--accent)" }}
              >
                {suggestion}
              </Link>
            </span>
          ))}
        </div>
      ) : null}

      <div className="flex gap-6">
        {/* Desktop filtr paneli */}
        <aside className="hidden w-64 shrink-0 lg:block">
          <div className="surface sticky top-36 max-h-[calc(100vh-10rem)] overflow-y-auto p-4">
            <FilterPanel
              facets={facets}
              params={params}
              onChange={updateParams}
              onClear={clearFilters}
            />
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <ProductGrid
            products={results}
            loading={isLoading && !results.length}
            isSearch={isSearch}
            emptyAction={
              <Link to={localePath("/catalog")} className="btn btn-secondary btn-sm">
                {t("catalog.title")}
              </Link>
            }
          />

          {/* Sahifalash */}
          {data && data.pages > 1 ? (
            <nav className="mt-8 flex items-center justify-center gap-1.5" aria-label="Pagination">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                disabled={!data.previous}
                onClick={() => goToPage((data.page || 1) - 1)}
              >
                {t("seller.back")}
              </button>
              <span className="px-3 text-sm" style={{ color: "var(--text-muted)" }}>
                {data.page} {t("common.of")} {data.pages}
              </span>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                disabled={!data.next}
                onClick={() => goToPage((data.page || 1) + 1)}
              >
                {t("seller.next")}
              </button>
            </nav>
          ) : null}
        </div>
      </div>

      {/* Mobil filtr drawer */}
      {drawerOpen ? (
        <div className="fixed inset-0 z-[60] lg:hidden" role="dialog" aria-modal="true">
          <button
            type="button"
            className="absolute inset-0 bg-black/45"
            onClick={() => setDrawerOpen(false)}
            aria-label={t("common.close")}
          />
          <div
            className="absolute inset-x-0 bottom-0 max-h-[85vh] overflow-y-auto rounded-t-2xl p-4"
            style={{ background: "var(--surface)" }}
          >
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-base font-bold">{t("catalog.filters")}</h2>
              <button
                type="button"
                className="btn btn-ghost h-9 min-h-9 w-9 px-0"
                onClick={() => setDrawerOpen(false)}
                aria-label={t("common.close")}
              >
                <X size={18} />
              </button>
            </div>

            <FilterPanel
              facets={facets}
              params={params}
              onChange={updateParams}
              onClear={clearFilters}
            />

            <button
              type="button"
              className="btn btn-primary mt-4 w-full"
              onClick={() => setDrawerOpen(false)}
            >
              {t("catalog.apply")} ({data?.count ?? 0})
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
