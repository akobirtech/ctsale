import { Link } from "react-router-dom";
import {
  AlertTriangle,
  Eye,
  Flag,
  Heart,
  Package,
  Phone,
  Send,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { admin as adminApi } from "../../api/endpoints";
import RequireAuth from "../../components/auth/RequireAuth";
import ErrorState from "../../components/ui/ErrorState";
import { Skeleton } from "../../components/ui/Skeleton";
import { useI18n, useLocalePath } from "../../i18n";
import { useHead } from "../../seo/Head";
import { formatCount } from "../../utils/format";

function StatCard({ icon: Icon, label, value, hint, tone = "neutral", to }) {
  const tones = {
    neutral: { background: "var(--bg-muted)", color: "var(--text-muted)" },
    brand: { background: "var(--accent-soft)", color: "var(--accent)" },
    warning: { background: "var(--warning-soft)", color: "var(--warning)" },
    danger: { background: "var(--danger-soft)", color: "var(--danger)" },
    success: { background: "var(--success-soft)", color: "var(--success)" },
  };

  const content = (
    <div className="surface flex items-start gap-3 p-4 transition-shadow hover:shadow-[var(--shadow-md)]">
      <span
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
        style={tones[tone]}
      >
        <Icon size={19} aria-hidden="true" />
      </span>
      <div className="min-w-0">
        <p className="text-xl font-extrabold leading-tight">{value}</p>
        <p className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
          {label}
        </p>
        {hint ? (
          <p className="mt-0.5 text-[11px]" style={{ color: "var(--text-subtle)" }}>
            {hint}
          </p>
        ) : null}
      </div>
    </div>
  );

  return to ? <Link to={to}>{content}</Link> : content;
}

/**
 * Oddiy ustunli grafik.
 *
 * Chart kutubxonasi olinmadi: bitta grafik uchun ~60KB bundle
 * qo'shish oqlanmaydi. Kerak bo'lganda almashtirish oson.
 */
function MiniChart({ series = [] }) {
  const max = Math.max(1, ...series.map((point) => Math.max(point.products, point.users)));

  return (
    <div className="surface p-4">
      <h2 className="mb-3 text-sm font-bold">Oxirgi 30 kun</h2>
      <div className="flex h-32 items-end gap-[2px]" role="img" aria-label="Kunlik dinamika">
        {series.map((point) => (
          <div key={point.date} className="group relative flex flex-1 flex-col justify-end gap-[2px]">
            <div
              className="rounded-t-sm"
              style={{
                height: `${(point.products / max) * 100}%`,
                background: "var(--accent)",
                minHeight: point.products ? "2px" : "0",
              }}
            />
            <div
              className="rounded-t-sm"
              style={{
                height: `${(point.users / max) * 60}%`,
                background: "var(--success)",
                minHeight: point.users ? "2px" : "0",
              }}
            />
            <span
              className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 hidden -translate-x-1/2 whitespace-nowrap rounded px-1.5 py-0.5 text-[10px] group-hover:block"
              style={{ background: "var(--text)", color: "var(--bg)" }}
            >
              {point.date}: {point.products} e&apos;lon, {point.users} user
            </span>
          </div>
        ))}
      </div>
      <div className="mt-2 flex gap-4 text-[11px]" style={{ color: "var(--text-muted)" }}>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-sm" style={{ background: "var(--accent)" }} />
          E&apos;lonlar
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-sm" style={{ background: "var(--success)" }} />
          Foydalanuvchilar
        </span>
      </div>
    </div>
  );
}

function DashboardContent() {
  const { t } = useI18n();
  const localePath = useLocalePath();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: adminApi.stats,
    refetchInterval: 60_000,
  });

  const { data: chart } = useQuery({
    queryKey: ["admin-chart"],
    queryFn: () => adminApi.chart(30),
  });

  if (isError) return <ErrorState onRetry={refetch} />;

  if (isLoading || !data) {
    return (
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {Array.from({ length: 8 }).map((_, index) => (
          <Skeleton key={index} className="h-20 w-full" />
        ))}
      </div>
    );
  }

  const { products, users, moderation, telegram, reports } = data;

  return (
    <div className="space-y-5">
      {/* Diqqat talab qiladigan narsalar birinchi */}
      {moderation.pending > 0 || telegram.failed > 0 || reports.new > 0 ? (
        <div className="grid gap-3 sm:grid-cols-3">
          {moderation.pending > 0 ? (
            <StatCard
              icon={ShieldCheck}
              tone="warning"
              value={moderation.pending}
              label="Moderatsiya kutmoqda"
              hint="Ko'rib chiqish kerak"
              to={localePath("/admin/moderation")}
            />
          ) : null}
          {telegram.failed > 0 ? (
            <StatCard
              icon={AlertTriangle}
              tone="danger"
              value={telegram.failed}
              label="Telegram xatosi"
              hint="Qayta yuborish kerak"
            />
          ) : null}
          {reports.new > 0 ? (
            <StatCard icon={Flag} tone="danger" value={reports.new} label="Yangi shikoyat" />
          ) : null}
        </div>
      ) : null}

      <div>
        <h2 className="mb-3 text-sm font-bold">E&apos;lonlar</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatCard icon={Package} tone="brand" value={products.total} label="Jami" hint={`+${products.new_week} shu hafta`} />
          <StatCard icon={Package} tone="success" value={products.approved} label={t("status.approved")} />
          <StatCard icon={Package} value={products.sold} label={t("status.sold")} />
          <StatCard icon={Package} tone="danger" value={products.rejected} label={t("status.rejected")} />
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-bold">Faollik</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatCard icon={Eye} value={formatCount(products.views)} label={t("product.views")} />
          <StatCard icon={Heart} value={formatCount(products.favorites)} label={t("nav.favorites")} />
          <StatCard icon={Phone} value={formatCount(products.phone_reveals)} label="Telefon ochildi" />
          <StatCard icon={Send} tone="brand" value={telegram.published} label="Telegram post" />
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-bold">Foydalanuvchilar</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatCard icon={Users} tone="brand" value={users.total} label="Jami" hint={`+${users.new_week} shu hafta`} />
          <StatCard icon={Users} value={users.sellers} label="Sotuvchilar" />
          <StatCard icon={ShieldCheck} tone="success" value={users.verified_sellers} label={t("product.verifiedSeller")} />
          <StatCard icon={Users} tone={users.banned ? "danger" : "neutral"} value={users.banned} label="Bloklangan" />
        </div>
      </div>

      {chart?.series?.length ? <MiniChart series={chart.series} /> : null}
    </div>
  );
}

export default function AdminDashboardPage() {
  const { t } = useI18n();
  const localePath = useLocalePath();

  useHead({
    title: `${t("nav.admin")} — ${t("brand.name")}`,
    robots: "noindex, nofollow",
  });

  return (
    <div className="container-page py-6">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold sm:text-2xl">{t("nav.admin")}</h1>
        <Link to={localePath("/admin/moderation")} className="btn btn-primary btn-sm">
          <ShieldCheck size={16} aria-hidden="true" />
          Moderatsiya
        </Link>
      </div>

      <RequireAuth>
        <DashboardContent />
      </RequireAuth>
    </div>
  );
}
