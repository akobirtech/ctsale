import { useState } from "react";
import { Link } from "react-router-dom";
import { Eye, Heart, Package, Phone } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { products as productsApi } from "../../api/endpoints";
import RequireAuth from "../../components/auth/RequireAuth";
import EmptyState from "../../components/ui/EmptyState";
import PageLoader from "../../components/ui/PageLoader";
import { useI18n, useLocalePath } from "../../i18n";
import { useHead } from "../../seo/Head";
import { formatCount } from "../../utils/format";

const RANGES = [7, 30, 90];

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="surface p-4">
      <div className="flex items-center gap-2 text-xs font-medium" style={{ color: "var(--text-muted)" }}>
        <Icon size={15} aria-hidden="true" />
        {label}
      </div>
      <p className="mt-1.5 text-2xl font-bold">{formatCount(value)}</p>
    </div>
  );
}

/**
 * Ko'rishlar grafigi.
 *
 * Diagramma kutubxonasi qo'shilmadi: bitta ustunli grafik uchun
 * 40 KB JS yuklash mantiqsiz. CSS balandliklari ham xuddi shu
 * ma'lumotni beradi va SSR'da ham ko'rinadi.
 */
function ViewsChart({ points, days }) {
  const { t } = useI18n();
  if (!points.length) {
    return (
      <p className="py-8 text-center text-sm" style={{ color: "var(--text-subtle)" }}>
        {t("seller.statsNoViews")}
      </p>
    );
  }

  const max = Math.max(...points.map((point) => point.count), 1);

  return (
    <div>
      <div className="flex h-40 items-end gap-1" role="img" aria-label={t("seller.statsChartLabel", { days })}>
        {points.map((point) => (
          <div
            key={point.date}
            className="flex-1 rounded-t"
            style={{
              height: `${Math.max((point.count / max) * 100, 3)}%`,
              background: "var(--accent)",
              minWidth: 3,
            }}
            title={`${point.date}: ${point.count}`}
          />
        ))}
      </div>
      <div className="mt-2 flex justify-between text-xs" style={{ color: "var(--text-subtle)" }}>
        <span>{points[0].date}</span>
        <span>{points[points.length - 1].date}</span>
      </div>
    </div>
  );
}

function StatsContent() {
  const { t } = useI18n();
  const localePath = useLocalePath();
  const [days, setDays] = useState(30);

  useHead({ title: t("seller.statistics"), robots: "noindex, nofollow" });

  const { data, isLoading, isError } = useQuery({
    queryKey: ["seller-stats", days],
    queryFn: () => productsApi.myStats({ days }),
  });

  if (isLoading) return <PageLoader />;
  if (isError) return <EmptyState title={t("error.generic")} />;

  const totals = data.totals;

  return (
    <div className="container-page py-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold">{t("seller.statistics")}</h1>
        <div className="flex gap-1">
          {RANGES.map((range) => (
            <button
              key={range}
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setDays(range)}
              style={
                range === days
                  ? { background: "var(--accent)", color: "var(--accent-text)", borderColor: "transparent" }
                  : undefined
              }
            >
              {t("seller.statsDays", { days: range })}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Package} label={t("nav.myProducts")} value={totals.total} />
        <StatCard icon={Eye} label={t("product.views")} value={totals.views} />
        <StatCard icon={Heart} label={t("product.favorites")} value={totals.favorites} />
        <StatCard icon={Phone} label={t("seller.statsPhoneReveals")} value={totals.phone_reveals} />
      </div>

      <div className="surface mt-4 p-5">
        <h2 className="mb-4 text-sm font-bold">{t("seller.statsViewsChart")}</h2>
        <ViewsChart points={data.views_daily} days={days} />
      </div>

      {data.top_products.length > 0 ? (
        <div className="surface mt-4 p-5">
          <h2 className="mb-3 text-sm font-bold">{t("seller.statsTop")}</h2>
          <ul className="space-y-1">
            {data.top_products.map((product) => (
              <li key={product.slug}>
                <Link
                  to={localePath(`/product/${product.slug}`)}
                  className="flex items-center justify-between gap-3 rounded-lg px-2 py-2 text-sm hover:bg-[var(--bg-muted)]"
                >
                  <span className="min-w-0 flex-1 truncate font-medium">{product.title}</span>
                  <span
                    className="flex shrink-0 items-center gap-3 text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    <span className="flex items-center gap-1">
                      <Eye size={13} aria-hidden="true" />
                      {formatCount(product.views_count)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Phone size={13} aria-hidden="true" />
                      {formatCount(product.phone_reveals_count)}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export default function SellerStatsPage() {
  return (
    <RequireAuth>
      <StatsContent />
    </RequireAuth>
  );
}
