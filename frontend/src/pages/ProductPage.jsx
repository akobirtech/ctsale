import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  BadgeCheck,
  ChevronRight,
  Eye,
  Flag,
  Heart,
  MapPin,
  Package,
  Phone,
  RefreshCw,
  Send,
  Share2,
  ShieldCheck,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { products as productsApi } from "../api/endpoints";
import ProductGallery from "../components/product/ProductGallery";
import ProductGrid from "../components/product/ProductGrid";
import ReportModal from "../components/product/ReportModal";
import ErrorState from "../components/ui/ErrorState";
import Badge, { conditionTone } from "../components/ui/Badge";
import { useToast } from "../hooks/useToast";
import { useI18n, useLocalePath } from "../i18n";
import { useHead } from "../seo/Head";
import { useAuthStore } from "../store/auth";
import { useRouteData } from "../store/routeData";
import { formatCount, formatDate, formatPhone, formatRelativeDate } from "../utils/format";

export default function ProductPage() {
  const { t, lang } = useI18n();
  const localePath = useLocalePath();
  const { slug } = useParams();
  const toast = useToast();
  const preloaded = useRouteData("product");

  const [contact, setContact] = useState(null);
  const [revealing, setRevealing] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);

  const user = useAuthStore((state) => state.user);
  const navigate = useNavigate();

  function openReport() {
    // Shikoyat autentifikatsiya talab qiladi — kirishga yuboramiz,
    // qaytib kelish uchun joriy manzilni saqlab.
    if (!user) {
      navigate(`${localePath("/login")}?next=${encodeURIComponent(window.location.pathname)}`);
      return;
    }
    setReportOpen(true);
  }

  const { data: product, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["product", slug, lang],
    queryFn: () => productsApi.detail(slug, lang),
    initialData: preloaded?.product,
  });

  const { data: similar = [] } = useQuery({
    queryKey: ["product-similar", slug, lang],
    queryFn: () => productsApi.similar(slug, lang),
    initialData: preloaded?.similar,
    enabled: Boolean(product),
  });

  // SEO ma'lumotini backend tayyorlaydi — sahifa, sitemap va Telegram
  // posti bir xil manbadan foydalansin.
  useHead(product?.seo);

  if (isError) {
    const status = error?.status;
    return (
      <div className="container-page py-10">
        <ErrorState
          status={status === 410 ? "410" : status === 404 ? "404" : undefined}
          title={status === 410 ? t("product.soldOut") : t("error.notFound")}
          description={t("error.notFoundText")}
          onRetry={status >= 500 ? refetch : undefined}
        />
        <div className="text-center">
          <Link to={localePath("/catalog")} className="btn btn-primary">
            {t("catalog.title")}
          </Link>
        </div>
      </div>
    );
  }

  if (isLoading || !product) {
    return (
      <div className="container-page py-6">
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="skeleton aspect-[4/3] w-full" />
          <div className="space-y-3">
            <div className="skeleton h-7 w-3/4" />
            <div className="skeleton h-9 w-1/2" />
            <div className="skeleton h-24 w-full" />
          </div>
        </div>
      </div>
    );
  }

  const isSold = product.status === "sold";

  async function revealPhone() {
    setRevealing(true);
    try {
      const data = await productsApi.revealPhone(product.slug);
      setContact(data);
    } catch (revealError) {
      toast.error(revealError.message || t("error.generic"));
    } finally {
      setRevealing(false);
    }
  }

  async function share() {
    const url = window.location.href;
    try {
      if (navigator.share) {
        await navigator.share({ title: product.title, url });
      } else {
        await navigator.clipboard.writeText(url);
        toast.success(t("product.copied"));
      }
    } catch {
      // Foydalanuvchi bekor qilgan bo'lishi mumkin — xato ko'rsatmaymiz.
    }
  }

  const usedDetails = [
    [t("product.usagePeriod"), product.usage_period],
    [t("product.accessories"), product.accessories],
    [t("product.defects"), product.defects],
    [t("product.repairHistory"), product.repair_history],
  ].filter(([, value]) => value);

  return (
    <div className="container-page py-5">
      {/* Breadcrumbs — JSON-LD dagi BreadcrumbList bilan mos */}
      <nav aria-label="Breadcrumb" className="mb-3">
        <ol className="flex flex-wrap items-center gap-1 text-xs" style={{ color: "var(--text-muted)" }}>
          <li>
            <Link to={localePath("/")} className="hover:underline">
              {t("nav.home")}
            </Link>
          </li>
          {(product.breadcrumbs || []).map((crumb) => (
            <li key={crumb.slug} className="flex items-center gap-1">
              <ChevronRight size={12} aria-hidden="true" />
              <Link to={localePath(`/category/${crumb.slug}`)} className="hover:underline">
                {crumb.name}
              </Link>
            </li>
          ))}
        </ol>
      </nav>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="min-w-0">
          <ProductGallery
            images={product.images}
            videos={product.videos}
            title={product.title}
          />

          {/* Tavsif */}
          <section className="surface mt-5 p-4 sm:p-5">
            <h2 className="mb-2 text-base font-bold">{t("product.description")}</h2>
            <p className="whitespace-pre-line text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
              {product.description}
            </p>

            {usedDetails.length ? (
              <dl className="mt-4 grid gap-2 border-t pt-4 text-sm sm:grid-cols-2">
                {usedDetails.map(([label, value]) => (
                  <div key={label}>
                    <dt className="text-xs font-semibold" style={{ color: "var(--text-subtle)" }}>
                      {label}
                    </dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
            ) : null}
          </section>

          {/* Xususiyatlar */}
          {product.spec_rows?.length ? (
            <section className="surface mt-5 p-4 sm:p-5">
              <h2 className="mb-3 text-base font-bold">{t("product.specs")}</h2>
              <dl className="divide-y text-sm">
                {product.spec_rows.map((row) => (
                  <div key={row.code} className="flex items-start justify-between gap-4 py-2">
                    <dt style={{ color: "var(--text-muted)" }}>{row.label}</dt>
                    <dd className="text-right font-medium">
                      {row.value}
                      {row.unit ? ` ${row.unit}` : ""}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>
          ) : null}
        </div>

        {/* O'ng ustun — yopishqoq */}
        <div className="lg:sticky lg:top-36 lg:self-start">
          <div className="surface p-4 sm:p-5">
            <div className="mb-2 flex flex-wrap gap-1.5">
              <Badge tone={conditionTone(product.condition)}>{product.condition_display}</Badge>
              {product.is_featured ? <Badge tone="brand">VIP</Badge> : null}
              {product.is_exchange_possible ? (
                <Badge tone="neutral" icon={RefreshCw}>
                  {t("product.exchangePossible")}
                </Badge>
              ) : null}
              {product.has_warranty ? (
                <Badge tone="success" icon={ShieldCheck}>
                  {t("catalog.warranty")}
                </Badge>
              ) : null}
              {product.has_original_box ? (
                <Badge tone="neutral" icon={Package}>
                  {t("product.originalBox")}
                </Badge>
              ) : null}
            </div>

            <h1 className="text-lg font-bold leading-snug sm:text-xl">{product.title}</h1>

            <p className="mt-3 text-2xl font-extrabold" style={{ color: "var(--accent)" }}>
              {product.price_display}
            </p>

            {isSold ? (
              <div
                className="mt-3 rounded-lg px-3 py-2 text-sm font-semibold"
                style={{ background: "var(--bg-muted)", color: "var(--text-muted)" }}
              >
                {t("product.soldOut")}
              </div>
            ) : null}

            <div
              className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs"
              style={{ color: "var(--text-subtle)" }}
            >
              <span className="flex items-center gap-1">
                <MapPin size={13} aria-hidden="true" />
                {product.region_name}
                {product.district_name ? `, ${product.district_name}` : ""}
              </span>
              <span className="flex items-center gap-1">
                <Eye size={13} aria-hidden="true" />
                {formatCount(product.views_count)} {t("product.views")}
              </span>
              <span className="flex items-center gap-1">
                <Heart size={13} aria-hidden="true" />
                {formatCount(product.favorites_count)}
              </span>
            </div>

            <time
              className="mt-1 block text-xs"
              style={{ color: "var(--text-subtle)" }}
              dateTime={product.published_at}
            >
              {t("product.published")}: {formatRelativeDate(product.published_at, lang)}
            </time>

            {/* Aloqa */}
            {!isSold ? (
              <div className="mt-4 space-y-2">
                {contact ? (
                  <>
                    <a href={`tel:${contact.phone}`} className="btn btn-primary w-full">
                      <Phone size={17} aria-hidden="true" />
                      {formatPhone(contact.phone)}
                    </a>
                    {contact.telegram ? (
                      <a
                        href={`https://t.me/${contact.telegram.replace("@", "")}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-secondary w-full"
                      >
                        <Send size={16} aria-hidden="true" />
                        {t("product.writeTelegram")}
                      </a>
                    ) : null}
                  </>
                ) : (
                  <button
                    type="button"
                    className="btn btn-primary w-full"
                    onClick={revealPhone}
                    disabled={revealing}
                  >
                    <Phone size={17} aria-hidden="true" />
                    {revealing ? t("common.loading") : t("product.showPhone")}
                  </button>
                )}

                <div className="flex gap-2">
                  <button type="button" className="btn btn-secondary btn-sm flex-1" onClick={share}>
                    <Share2 size={15} aria-hidden="true" />
                    {t("product.share")}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm flex-1"
                    onClick={openReport}
                  >
                    <Flag size={15} aria-hidden="true" />
                    {t("product.report")}
                  </button>
                </div>
              </div>
            ) : null}
          </div>

          {/* Sotuvchi */}
          {product.seller ? (
            <div className="surface mt-4 p-4 sm:p-5">
              <h2 className="mb-3 text-sm font-bold">{t("product.seller")}</h2>
              <div className="flex items-center gap-3">
                <div
                  className="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-full text-sm font-bold"
                  style={{ background: "var(--accent-soft)", color: "var(--accent)" }}
                >
                  {product.seller.avatar ? (
                    <img
                      src={product.seller.avatar}
                      alt=""
                      className="h-full w-full object-cover"
                      loading="lazy"
                    />
                  ) : (
                    (product.seller.full_name || "?").charAt(0).toUpperCase()
                  )}
                </div>
                <div className="min-w-0">
                  <p className="flex items-center gap-1 truncate text-sm font-semibold">
                    {product.seller.shop?.name || product.seller.full_name || t("product.seller")}
                    {product.seller.is_verified_seller ? (
                      <BadgeCheck
                        size={15}
                        style={{ color: "var(--accent)" }}
                        aria-label={t("product.verifiedSeller")}
                      />
                    ) : null}
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                    {t("product.memberSince")} {formatDate(product.seller.created_at, lang)}
                  </p>
                </div>
              </div>

              {product.seller.shop?.working_hours ? (
                <p className="mt-3 text-xs" style={{ color: "var(--text-muted)" }}>
                  {product.seller.shop.working_hours}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      {similar.length > 0 ? (
        <section className="mt-10">
          <h2 className="mb-4 text-lg font-bold">{t("product.similar")}</h2>
          <ProductGrid products={similar.slice(0, 8)} />
        </section>
      ) : null}

      <ReportModal
        open={reportOpen}
        onClose={() => setReportOpen(false)}
        slug={product.slug}
        productTitle={product.title}
      />
    </div>
  );
}
