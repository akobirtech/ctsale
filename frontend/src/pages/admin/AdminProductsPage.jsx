import { useState } from "react";
import { Link } from "react-router-dom";
import { Archive, Package, RotateCcw, Star, Trash2 } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { admin as adminApi } from "../../api/endpoints";
import AdminNav from "../../components/admin/AdminNav";
import RequireAuth from "../../components/auth/RequireAuth";
import EmptyState from "../../components/ui/EmptyState";
import { Skeleton } from "../../components/ui/Skeleton";
import { useDebounce } from "../../hooks/useDebounce";
import { useToast } from "../../hooks/useToast";
import { useI18n, useLocalePath } from "../../i18n";
import { useHead } from "../../seo/Head";
import { formatCount } from "../../utils/format";

const STATUS_FILTERS = [
  { value: "", label: "common.all" },
  { value: "draft", label: "status.draft" },
  { value: "pending", label: "status.pending" },
  { value: "approved", label: "status.approved" },
  { value: "rejected", label: "status.rejected" },
  { value: "sold", label: "status.sold" },
  { value: "archived", label: "status.archived" },
];

function StatusBadge({ status }) {
  const { t } = useI18n();
  const tones = {
    approved: "var(--success)",
    pending: "var(--warning)",
    rejected: "var(--danger)",
    sold: "var(--accent)",
  };
  return (
    <span
      className="whitespace-nowrap rounded-md px-1.5 py-0.5 text-[11px] font-medium"
      style={{ background: "var(--bg-muted)", color: tones[status] || "var(--text-muted)" }}
    >
      {t(`status.${status}`)}
    </span>
  );
}

function ProductsTable() {
  const { t } = useI18n();
  const localePath = useLocalePath();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [deleted, setDeleted] = useState(false);
  const [selected, setSelected] = useState([]);

  const debouncedSearch = useDebounce(search, 350);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-products", status, debouncedSearch, deleted],
    queryFn: () =>
      adminApi.products({
        status: status || undefined,
        search: debouncedSearch || undefined,
        deleted: deleted ? "true" : undefined,
      }),
  });

  function refresh() {
    setSelected([]);
    queryClient.invalidateQueries({ queryKey: ["admin-products"] });
  }

  const bulk = useMutation({
    mutationFn: ({ action, ids }) => adminApi.bulkProducts(action, ids),
    onSuccess: (result) => {
      toast.success(t("admin.bulkDone", { count: result.affected }));
      refresh();
    },
    onError: (error) => toast.error(error.message),
  });

  const single = useMutation({
    mutationFn: ({ action, id }) => {
      if (action === "feature") return adminApi.featureProduct(id, 7);
      if (action === "restore") return adminApi.restoreProduct(id);
      return adminApi.deleteProduct(id);
    },
    onSuccess: refresh,
    onError: (error) => toast.error(error.message),
  });

  const rows = data?.results || [];
  const allSelected = rows.length > 0 && selected.length === rows.length;

  function toggleRow(id) {
    setSelected((current) =>
      current.includes(id) ? current.filter((value) => value !== id) : [...current, id]
    );
  }

  return (
    <>
      {/* Filtrlar */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <input
          type="search"
          className="input h-9 w-full sm:w-64"
          placeholder={t("admin.searchProducts")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />

        <select
          className="input h-9 w-auto"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          {STATUS_FILTERS.map((item) => (
            <option key={item.value} value={item.value}>
              {t(item.label)}
              {data?.status_counts?.[item.value] ? ` (${data.status_counts[item.value]})` : ""}
            </option>
          ))}
        </select>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={deleted}
            onChange={(event) => {
              setDeleted(event.target.checked);
              setSelected([]);
            }}
          />
          {t("admin.showDeleted")}
        </label>
      </div>

      {/* Ommaviy amallar — faqat tanlov bo'lganda */}
      {selected.length > 0 ? (
        <div
          className="mb-3 flex flex-wrap items-center gap-2 rounded-xl p-3"
          style={{ background: "var(--accent-soft)" }}
        >
          <span className="text-sm font-medium">
            {t("admin.selected", { count: selected.length })}
          </span>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => bulk.mutate({ action: "feature", ids: selected })}
            disabled={bulk.isPending}
          >
            <Star size={14} />
            VIP
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => bulk.mutate({ action: "archive", ids: selected })}
            disabled={bulk.isPending}
          >
            <Archive size={14} />
            {t("status.archived")}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ color: "var(--danger)" }}
            onClick={() => bulk.mutate({ action: "delete", ids: selected })}
            disabled={bulk.isPending}
          >
            <Trash2 size={14} />
            {t("seller.delete")}
          </button>
        </div>
      ) : null}

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-14" />
          ))}
        </div>
      ) : isError ? (
        <EmptyState title={t("error.generic")} />
      ) : rows.length === 0 ? (
        <EmptyState icon={Package} title={t("empty.products")} />
      ) : (
        <div className="surface overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ color: "var(--text-subtle)" }}>
                <th className="w-10 p-3">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={() => setSelected(allSelected ? [] : rows.map((row) => row.id))}
                    aria-label={t("common.all")}
                  />
                </th>
                <th className="p-3 text-left font-medium">{t("admin.product")}</th>
                <th className="p-3 text-left font-medium">{t("product.seller")}</th>
                <th className="p-3 text-left font-medium">{t("catalog.sortBy")}</th>
                <th className="p-3 text-right font-medium">{t("product.views")}</th>
                <th className="p-3" />
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t">
                  <td className="p-3">
                    <input
                      type="checkbox"
                      checked={selected.includes(row.id)}
                      onChange={() => toggleRow(row.id)}
                      aria-label={row.title}
                    />
                  </td>

                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      {row.cover ? (
                        <img
                          src={row.cover}
                          alt=""
                          className="h-9 w-9 shrink-0 rounded-lg object-cover"
                          loading="lazy"
                        />
                      ) : null}
                      <div className="min-w-0">
                        <Link
                          to={localePath(`/product/${row.slug}`)}
                          className="block max-w-[22rem] truncate font-medium hover:underline"
                        >
                          {row.title}
                        </Link>
                        <span className="text-xs" style={{ color: "var(--text-subtle)" }}>
                          {row.category_name}
                        </span>
                      </div>
                      {row.is_featured ? (
                        <Star size={14} style={{ color: "var(--warning)" }} aria-label="VIP" />
                      ) : null}
                    </div>
                  </td>

                  <td className="p-3">
                    <span className="whitespace-nowrap">{row.seller_name || row.seller_phone}</span>
                  </td>

                  <td className="p-3">
                    <StatusBadge status={row.status} />
                  </td>

                  <td className="p-3 text-right tabular-nums">{formatCount(row.views_count)}</td>

                  <td className="p-3">
                    <div className="flex justify-end gap-1">
                      {deleted ? (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => single.mutate({ action: "restore", id: row.id })}
                          title={t("admin.restore")}
                        >
                          <RotateCcw size={15} />
                        </button>
                      ) : (
                        <>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => single.mutate({ action: "feature", id: row.id })}
                            title="VIP"
                          >
                            <Star size={15} />
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            style={{ color: "var(--danger)" }}
                            onClick={() => single.mutate({ action: "delete", id: row.id })}
                            title={t("seller.delete")}
                          >
                            <Trash2 size={15} />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data?.count ? (
        <p className="mt-3 text-xs" style={{ color: "var(--text-subtle)" }}>
          {t("admin.totalFound", { count: data.count })}
        </p>
      ) : null}
    </>
  );
}

export default function AdminProductsPage() {
  const { t } = useI18n();
  useHead({ title: `${t("admin.products")} — ${t("nav.admin")}`, robots: "noindex, nofollow" });

  return (
    <div className="container-page py-6">
      <h1 className="mb-4 text-xl font-bold sm:text-2xl">{t("admin.products")}</h1>
      <AdminNav />
      <RequireAuth>
        <ProductsTable />
      </RequireAuth>
    </div>
  );
}
