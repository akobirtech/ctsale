import { useState } from "react";
import { Ban, BadgeCheck, ShieldCheck, Undo2, Users } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { admin as adminApi } from "../../api/endpoints";
import AdminNav from "../../components/admin/AdminNav";
import RequireAuth from "../../components/auth/RequireAuth";
import EmptyState from "../../components/ui/EmptyState";
import Field from "../../components/ui/Field";
import Modal from "../../components/ui/Modal";
import { Skeleton } from "../../components/ui/Skeleton";
import { useDebounce } from "../../hooks/useDebounce";
import { useToast } from "../../hooks/useToast";
import { useI18n } from "../../i18n";
import { useHead } from "../../seo/Head";
import { formatPhone, formatRelativeDate } from "../../utils/format";

function BanDialog({ user, onClose, onSubmit, pending }) {
  const { t } = useI18n();
  const [reason, setReason] = useState("");
  const [days, setDays] = useState("");

  return (
    <Modal
      open={Boolean(user)}
      onClose={onClose}
      title={t("admin.banUser")}
      description={user ? formatPhone(user.phone) : ""}
      footer={
        <>
          <button type="button" className="btn btn-secondary flex-1" onClick={onClose}>
            {t("common.cancel")}
          </button>
          <button
            type="submit"
            form="ban-form"
            className="btn btn-primary flex-1"
            disabled={pending || reason.trim().length < 3}
          >
            {t("admin.ban")}
          </button>
        </>
      }
    >
      <form
        id="ban-form"
        className="space-y-3"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit({ reason: reason.trim(), days: days || undefined });
        }}
      >
        {/* Sabab majburiy: backend ham talab qiladi va u audit
            jurnaliga tushadi. */}
        <Field label={t("admin.banReason")} required>
          <textarea
            className="input min-h-20"
            rows={3}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </Field>

        <Field
          label={t("admin.banDays")}
          type="number"
          min="1"
          max="3650"
          placeholder={t("admin.banForever")}
          value={days}
          onChange={(event) => setDays(event.target.value)}
        />
      </form>
    </Modal>
  );
}

function UsersTable() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState("");
  const [onlyBanned, setOnlyBanned] = useState(false);
  const [banning, setBanning] = useState(null);

  const debouncedSearch = useDebounce(search, 350);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-users", debouncedSearch, onlyBanned],
    queryFn: () =>
      adminApi.users({
        search: debouncedSearch || undefined,
        banned: onlyBanned ? "true" : undefined,
      }),
  });

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["admin-users"] });
  }

  const act = useMutation({
    mutationFn: ({ action, id, payload }) => {
      if (action === "ban") return adminApi.banUser(id, payload);
      if (action === "unban") return adminApi.unbanUser(id);
      return adminApi.verifySeller(id);
    },
    onSuccess: (result) => {
      toast.success(result.detail || t("common.save"));
      setBanning(null);
      refresh();
    },
    onError: (error) => toast.error(error.message),
  });

  const rows = data?.results || [];

  return (
    <>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <input
          type="search"
          className="input h-9 w-full sm:w-64"
          placeholder={t("admin.searchUsers")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={onlyBanned}
            onChange={(event) => setOnlyBanned(event.target.checked)}
          />
          {t("admin.onlyBanned")}
        </label>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-14" />
          ))}
        </div>
      ) : isError ? (
        <EmptyState title={t("error.generic")} />
      ) : rows.length === 0 ? (
        <EmptyState icon={Users} title={t("admin.users")} />
      ) : (
        <div className="surface overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ color: "var(--text-subtle)" }}>
                <th className="p-3 text-left font-medium">{t("auth.phone")}</th>
                <th className="p-3 text-left font-medium">{t("admin.roles")}</th>
                <th className="p-3 text-right font-medium">{t("nav.myProducts")}</th>
                <th className="p-3 text-left font-medium">{t("product.memberSince")}</th>
                <th className="p-3" />
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t">
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <div className="min-w-0">
                        <p className="font-medium">{row.full_name || formatPhone(row.phone)}</p>
                        <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                          {formatPhone(row.phone)}
                        </p>
                      </div>
                      {row.is_verified_seller ? (
                        <BadgeCheck
                          size={15}
                          style={{ color: "var(--success)" }}
                          aria-label={t("product.verifiedSeller")}
                        />
                      ) : null}
                      {row.ban_is_active ? (
                        <span
                          className="rounded-md px-1.5 py-0.5 text-[11px] font-medium"
                          style={{ background: "var(--danger-soft)", color: "var(--danger)" }}
                        >
                          {t("admin.banned")}
                        </span>
                      ) : null}
                    </div>
                  </td>

                  <td className="p-3">
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                      {(row.roles || []).join(", ") || "—"}
                    </span>
                  </td>

                  <td className="p-3 text-right tabular-nums">{row.products_total ?? 0}</td>

                  <td className="p-3 text-xs" style={{ color: "var(--text-subtle)" }}>
                    {formatRelativeDate(row.created_at)}
                  </td>

                  <td className="p-3">
                    <div className="flex justify-end gap-1">
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => act.mutate({ action: "verify", id: row.id })}
                        title={t("product.verifiedSeller")}
                      >
                        <ShieldCheck size={15} />
                      </button>

                      {row.ban_is_active ? (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => act.mutate({ action: "unban", id: row.id })}
                          title={t("admin.unban")}
                        >
                          <Undo2 size={15} />
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          style={{ color: "var(--danger)" }}
                          onClick={() => setBanning(row)}
                          title={t("admin.ban")}
                        >
                          <Ban size={15} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <BanDialog
        user={banning}
        pending={act.isPending}
        onClose={() => setBanning(null)}
        onSubmit={(payload) => act.mutate({ action: "ban", id: banning.id, payload })}
      />
    </>
  );
}

export default function AdminUsersPage() {
  const { t } = useI18n();
  useHead({ title: `${t("admin.users")} — ${t("nav.admin")}`, robots: "noindex, nofollow" });

  return (
    <div className="container-page py-6">
      <h1 className="mb-4 text-xl font-bold sm:text-2xl">{t("admin.users")}</h1>
      <AdminNav />
      <RequireAuth>
        <UsersTable />
      </RequireAuth>
    </div>
  );
}
