import { useState } from "react";
import { Link } from "react-router-dom";
import { Check, Flag, X } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { reports as reportsApi } from "../../api/endpoints";
import AdminNav from "../../components/admin/AdminNav";
import RequireAuth from "../../components/auth/RequireAuth";
import EmptyState from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import { useToast } from "../../hooks/useToast";
import { useI18n, useLocalePath } from "../../i18n";
import { useHead } from "../../seo/Head";
import { formatRelativeDate } from "../../utils/format";

const TABS = [
  { value: "new", label: "Yangi" },
  { value: "reviewing", label: "Ko'rilmoqda" },
  { value: "resolved", label: "Hal qilingan" },
  { value: "dismissed", label: "Rad etilgan" },
];

function ReportsList() {
  const { t } = useI18n();
  const localePath = useLocalePath();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [status, setStatus] = useState("new");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-reports", status],
    queryFn: () => reportsApi.list({ status }),
  });

  const resolve = useMutation({
    mutationFn: ({ id, nextStatus }) => reportsApi.resolve(id, { status: nextStatus }),
    onSuccess: () => {
      toast.success(t("common.save"));
      queryClient.invalidateQueries({ queryKey: ["admin-reports"] });
    },
    onError: (error) => toast.error(error.message),
  });

  const rows = data?.results || [];

  return (
    <>
      <div className="mb-3 flex gap-1 overflow-x-auto pb-1">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            type="button"
            className="btn btn-secondary btn-sm shrink-0"
            onClick={() => setStatus(tab.value)}
            style={
              tab.value === status
                ? { background: "var(--accent)", color: "var(--accent-text)", borderColor: "transparent" }
                : undefined
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-24" />
          ))}
        </div>
      ) : isError ? (
        <EmptyState title={t("error.generic")} />
      ) : rows.length === 0 ? (
        <EmptyState icon={Flag} title={t("admin.reportsEmpty")} />
      ) : (
        <div className="space-y-2">
          {rows.map((report) => (
            <article key={report.id} className="surface p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                    {t("admin.reportOn")}
                  </p>
                  <Link
                    to={localePath(`/product/${report.product_slug}`)}
                    className="font-medium hover:underline"
                  >
                    {report.product_title}
                  </Link>

                  <p className="mt-2 text-sm">
                    <span style={{ color: "var(--text-subtle)" }}>{t("admin.reason")}: </span>
                    <span className="font-medium">{report.reason_display || report.reason}</span>
                  </p>

                  {report.comment ? (
                    <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
                      {report.comment}
                    </p>
                  ) : null}

                  <p className="mt-2 text-xs" style={{ color: "var(--text-subtle)" }}>
                    {t("admin.reporter")}: {report.reporter_name || "—"} ·{" "}
                    {formatRelativeDate(report.created_at)}
                  </p>
                </div>

                {status === "new" || status === "reviewing" ? (
                  <div className="flex shrink-0 gap-2">
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={() => resolve.mutate({ id: report.id, nextStatus: "resolved" })}
                      disabled={resolve.isPending}
                    >
                      <Check size={15} />
                      {t("admin.resolve")}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => resolve.mutate({ id: report.id, nextStatus: "dismissed" })}
                      disabled={resolve.isPending}
                    >
                      <X size={15} />
                      {t("admin.dismiss")}
                    </button>
                  </div>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </>
  );
}

export default function AdminReportsPage() {
  const { t } = useI18n();
  useHead({ title: `${t("admin.reports")} — ${t("nav.admin")}`, robots: "noindex, nofollow" });

  return (
    <div className="container-page py-6">
      <h1 className="mb-4 text-xl font-bold sm:text-2xl">{t("admin.reports")}</h1>
      <AdminNav />
      <RequireAuth>
        <ReportsList />
      </RequireAuth>
    </div>
  );
}
