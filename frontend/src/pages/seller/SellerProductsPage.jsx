import { useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  BarChart3,
  Eye,
  Heart,
  Pencil,
  Phone,
  Plus,
  RefreshCw,
  Send,
  Trash2,
} from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { products as productsApi } from "../../api/endpoints";
import RequireAuth from "../../components/auth/RequireAuth";
import Badge, { statusTone } from "../../components/ui/Badge";
import EmptyState from "../../components/ui/EmptyState";
import ErrorState from "../../components/ui/ErrorState";
import { ProductGridSkeleton } from "../../components/ui/Skeleton";
import { useToast } from "../../hooks/useToast";
import { useI18n, useLocalePath } from "../../i18n";
import { useHead } from "../../seo/Head";
import { formatCount, formatRelativeDate } from "../../utils/format";

const TABS = [
  { key: "", labelKey: "common.all" },
  { key: "approved", labelKey: "status.approved" },
  { key: "pending", labelKey: "status.pending" },
  { key: "draft", labelKey: "status.draft" },
  { key: "rejected", labelKey: "status.rejected" },
  { key: "sold", labelKey: "status.sold" },
];

function SellerProductRow({ product, onAction, busy }) {
  const { t, lang } = useI18n();
  const localePath = useLocalePath();

  const canSubmit = ["draft", "rejected", "expired"].includes(product.status);
  const canSell = ["approved", "reserved"].includes(product.status);
  const canRenew = ["approved", "expired"].includes(product.status);

  return (
    <article className="surface flex gap-3 p-3">
      <Link
        to={localePath(`/product/${product.slug}`)}
        className="h-20 w-24 shrink-0 overflow-hidden rounded-lg sm:h-24 sm:w-32"
        style={{ background: "var(--bg-muted)" }}
      >
        {product.primary_image?.url ? (
          <img
            src={product.primary_image.url}
            alt=""
            className="h-full w-full object-cover"
            loading="lazy"
          />
        ) : null}
      </Link>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <Link
            to={localePath(`/product/${product.slug}`)}
            className="line-clamp-2 text-sm font-semibold hover:underline"
          >
            {product.title}
          </Link>
          <Badge tone={statusTone(product.status)}>{t(`status.${product.status}`)}</Badge>
        </div>

        <p className="mt-1 text-sm font-bold" style={{ color: "var(--accent)" }}>
          {product.price_display}
        </p>

        <div
          className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11px]"
          style={{ color: "var(--text-subtle)" }}
        >
          <span className="flex items-center gap-1">
            <Eye size={12} aria-hidden="true" />
            {formatCount(product.views_count)}
          </span>
          <span className="flex items-center gap-1">
            <Heart size={12} aria-hidden="true" />
            {formatCount(product.favorites_count)}
          </span>
          <span className="flex items-center gap-1">
            <Phone size={12} aria-hidden="true" />
            {formatCount(product.phone_reveals_count ?? 0)}
          </span>
          <time dateTime={product.created_at}>
            {formatRelativeDate(product.published_at || product.created_at, lang)}
          </time>
        </div>

        <div className="mt-2 flex flex-wrap gap-1.5">
          <Link
            to={localePath(`/seller/products/${product.slug}/edit`)}
            className="btn btn-secondary btn-sm"
          >
            <Pencil size={14} aria-hidden="true" />
            {t("seller.edit")}
          </Link>

          {canSubmit ? (
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => onAction("submit", product)}
              disabled={busy}
            >
              <Send size={14} aria-hidden="true" />
              {t("seller.submit")}
            </button>
          ) : null}

          {canSell ? (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => onAction("markSold", product)}
              disabled={busy}
            >
              {t("seller.markSold")}
            </button>
          ) : null}

          {canRenew ? (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => onAction("renew", product)}
              disabled={busy}
            >
              <RefreshCw size={14} aria-hidden="true" />
              {t("seller.renew")}
            </button>
          ) : null}

          <button
            type="button"
            className="btn btn-ghost btn-sm"
            style={{ color: "var(--danger)" }}
            onClick={() => onAction("remove", product)}
            disabled={busy}
          >
            <Trash2 size={14} aria-hidden="true" />
            {t("seller.delete")}
          </button>
        </div>
      </div>
    </article>
  );
}

function SellerProductsContent() {
  const { t, lang } = useI18n();
  const localePath = useLocalePath();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [tab, setTab] = useState("");
  const [confirming, setConfirming] = useState(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["my-products", tab, lang],
    queryFn: () => productsApi.mine({ status: tab || undefined, lang }),
  });

  const action = useMutation({
    mutationFn: ({ type, product }) => {
      if (type === "submit") return productsApi.submit(product.slug);
      if (type === "markSold") return productsApi.markSold(product.slug);
      if (type === "renew") return productsApi.renew(product.slug);
      if (type === "remove") return productsApi.remove(product.slug);
      throw new Error("Noma'lum amal");
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["my-products"] });
      toast.success(result?.detail || t("common.save"));
      setConfirming(null);
    },
    onError: (error) => {
      toast.error(error.message);
      setConfirming(null);
    },
  });

  function handleAction(type, product) {
    // O'chirish qaytarib bo'lmaydigan amal — tasdiq so'raymiz.
    if (type === "remove") {
      setConfirming({ type, product });
      return;
    }
    action.mutate({ type, product });
  }

  if (isError) return <ErrorState onRetry={refetch} />;

  const products = data?.results || [];

  return (
    <>
      <div className="mb-4 flex gap-1.5 overflow-x-auto pb-1">
        {TABS.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => setTab(item.key)}
            className="btn btn-sm whitespace-nowrap"
            style={
              tab === item.key
                ? { background: "var(--accent)", color: "var(--accent-text)" }
                : { background: "var(--surface)", color: "var(--text-muted)" }
            }
            aria-pressed={tab === item.key}
          >
            {t(item.labelKey)}
          </button>
        ))}
      </div>

      {isLoading ? (
        <ProductGridSkeleton count={4} />
      ) : products.length === 0 ? (
        <EmptyState
          title={t("empty.myProducts")}
          description={t("home.ctaText")}
          action={
            <Link to={localePath("/seller/products/new")} className="btn btn-primary btn-sm">
              <Plus size={15} aria-hidden="true" />
              {t("seller.newProduct")}
            </Link>
          }
        />
      ) : (
        <div className="space-y-3">
          {products.map((product) => (
            <SellerProductRow
              key={product.id}
              product={product}
              onAction={handleAction}
              busy={action.isPending}
            />
          ))}
        </div>
      )}

      {/* O'chirishni tasdiqlash */}
      {confirming ? (
        <div className="fixed inset-0 z-[70] flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <button
            type="button"
            className="absolute inset-0 bg-black/45"
            onClick={() => setConfirming(null)}
            aria-label={t("common.close")}
          />
          <div className="surface relative w-full max-w-sm p-5">
            <div className="flex items-start gap-3">
              <div
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
                style={{ background: "var(--danger-soft)", color: "var(--danger)" }}
              >
                <AlertCircle size={20} aria-hidden="true" />
              </div>
              <div className="min-w-0">
                <h2 className="text-base font-bold">{t("seller.delete")}?</h2>
                <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
                  «{confirming.product.title}» o&apos;chiriladi. Bu amalni qaytarib bo&apos;lmaydi.
                </p>
              </div>
            </div>
            <div className="mt-5 flex gap-2">
              <button
                type="button"
                className="btn btn-secondary flex-1"
                onClick={() => setConfirming(null)}
              >
                {t("common.cancel")}
              </button>
              <button
                type="button"
                className="btn btn-danger flex-1"
                onClick={() => action.mutate(confirming)}
                disabled={action.isPending}
              >
                {action.isPending ? t("common.loading") : t("seller.delete")}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}

export default function SellerProductsPage() {
  const { t } = useI18n();
  const localePath = useLocalePath();

  useHead({
    title: `${t("seller.myProducts")} — ${t("brand.name")}`,
    robots: "noindex, nofollow",
  });

  return (
    <div className="container-page py-6">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold sm:text-2xl">{t("seller.myProducts")}</h1>
        <div className="flex gap-2">
          <Link to={localePath("/seller/statistics")} className="btn btn-secondary btn-sm">
            <BarChart3 size={16} aria-hidden="true" />
            {t("seller.statistics")}
          </Link>
          <Link to={localePath("/seller/products/new")} className="btn btn-primary btn-sm">
            <Plus size={16} aria-hidden="true" />
            {t("seller.newProduct")}
          </Link>
        </div>
      </div>

      <RequireAuth>
        <SellerProductsContent />
      </RequireAuth>
    </div>
  );
}
