import { useState } from "react";
import { Link } from "react-router-dom";
import { Check, Clock, ExternalLink, Send, ShieldCheck, X } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { moderation as moderationApi } from "../../api/endpoints";
import RequireAuth from "../../components/auth/RequireAuth";
import Badge from "../../components/ui/Badge";
import EmptyState from "../../components/ui/EmptyState";
import ErrorState from "../../components/ui/ErrorState";
import Field from "../../components/ui/Field";
import { Skeleton } from "../../components/ui/Skeleton";
import { useToast } from "../../hooks/useToast";
import { useI18n, useLocalePath } from "../../i18n";
import { useHead } from "../../seo/Head";
import { formatRelativeDate } from "../../utils/format";

function RejectDialog({ task, reasons, onClose, onConfirm, busy }) {
  const { t } = useI18n();
  const [reasonCode, setReasonCode] = useState("");
  const [comment, setComment] = useState("");

  // "Boshqa sabab" tanlansa izohsiz sotuvchi nima qilishini bilmaydi.
  const commentRequired = reasonCode === "other";
  const canSubmit = reasonCode && (!commentRequired || comment.trim());

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <button type="button" className="absolute inset-0 bg-black/45" onClick={onClose} aria-label={t("common.close")} />
      <div className="surface relative w-full max-w-md p-5">
        <h2 className="text-base font-bold">E&apos;lonni rad etish</h2>
        <p className="mt-1 line-clamp-2 text-sm" style={{ color: "var(--text-muted)" }}>
          {task.product.title}
        </p>

        <div className="mt-4 space-y-3">
          <Field label={t("seller.rejectReason")} required>
            <select
              className="input"
              value={reasonCode}
              onChange={(event) => setReasonCode(event.target.value)}
            >
              <option value="">—</option>
              {reasons.map((reason) => (
                <option key={reason.value} value={reason.value}>
                  {reason.label}
                </option>
              ))}
            </select>
          </Field>

          <Field
            label={`Sotuvchiga izoh${commentRequired ? "" : " (ixtiyoriy)"}`}
            required={commentRequired}
          >
            <textarea
              className="input min-h-24 py-2.5"
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              maxLength={1000}
              placeholder="Nimani tuzatish kerakligini aniq yozing"
            />
          </Field>
        </div>

        <div className="mt-5 flex gap-2">
          <button type="button" className="btn btn-secondary flex-1" onClick={onClose}>
            {t("common.cancel")}
          </button>
          <button
            type="button"
            className="btn btn-danger flex-1"
            disabled={!canSubmit || busy}
            onClick={() => onConfirm({ reason_code: reasonCode, comment })}
          >
            {busy ? t("common.loading") : "Rad etish"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ModerationContent() {
  const { t, lang } = useI18n();
  const localePath = useLocalePath();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [rejecting, setRejecting] = useState(null);
  const [selected, setSelected] = useState([]);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["moderation-queue", lang],
    queryFn: () => moderationApi.queue({ lang }),
    refetchInterval: 30_000,
  });

  const { data: stats } = useQuery({
    queryKey: ["moderation-stats"],
    queryFn: moderationApi.stats,
  });

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["moderation-queue"] });
    queryClient.invalidateQueries({ queryKey: ["moderation-stats"] });
    queryClient.invalidateQueries({ queryKey: ["admin-stats"] });
    setSelected([]);
  }

  const approve = useMutation({
    mutationFn: (id) => moderationApi.approve(id),
    onSuccess: (result) => {
      toast.success(result.detail);
      refresh();
    },
    onError: (error) => toast.error(error.message),
  });

  const reject = useMutation({
    mutationFn: ({ id, payload }) => moderationApi.reject(id, payload),
    onSuccess: (result) => {
      toast.success(result.detail);
      setRejecting(null);
      refresh();
    },
    onError: (error) => toast.error(error.message),
  });

  const bulkApprove = useMutation({
    mutationFn: (ids) => moderationApi.bulkApprove(ids),
    onSuccess: (result) => {
      toast.success(result.detail);
      if (result.failed?.length) {
        toast.error(`${result.failed.length} ta e'londa xatolik bo'ldi`);
      }
      refresh();
    },
    onError: (error) => toast.error(error.message),
  });

  if (isError) return <ErrorState onRetry={refetch} />;

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-28 w-full" />
        ))}
      </div>
    );
  }

  const tasks = data?.results || [];

  if (!tasks.length) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title="Navbat bo'sh"
        description="Moderatsiya kutayotgan e'lon yo'q."
      />
    );
  }

  const toggleSelect = (id) =>
    setSelected((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    );

  return (
    <>
      {/* Ommaviy amallar */}
      {selected.length > 0 ? (
        <div
          className="surface sticky top-20 z-30 mb-3 flex flex-wrap items-center justify-between gap-2 p-3"
          style={{ background: "var(--accent-soft)" }}
        >
          <span className="text-sm font-semibold">{selected.length} ta tanlandi</span>
          <div className="flex gap-2">
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setSelected([])}>
              {t("common.cancel")}
            </button>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => bulkApprove.mutate(selected)}
              disabled={bulkApprove.isPending}
            >
              <Check size={15} aria-hidden="true" />
              Hammasini tasdiqlash
            </button>
          </div>
        </div>
      ) : null}

      <div className="space-y-3">
        {tasks.map((task) => {
          const product = task.product;
          return (
            <article key={task.id} className="surface flex gap-3 p-3">
              <label className="flex shrink-0 items-start pt-1">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-[var(--accent)]"
                  checked={selected.includes(task.id)}
                  onChange={() => toggleSelect(task.id)}
                  aria-label={`${product.title} tanlash`}
                />
              </label>

              <Link
                to={localePath(`/product/${product.slug}`)}
                target="_blank"
                rel="noreferrer"
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
                    target="_blank"
                    rel="noreferrer"
                    className="line-clamp-2 flex items-start gap-1 text-sm font-semibold hover:underline"
                  >
                    {product.title}
                    <ExternalLink size={13} className="mt-0.5 shrink-0" aria-hidden="true" />
                  </Link>
                  {task.is_resubmission ? <Badge tone="warning">Qayta yuborilgan</Badge> : null}
                </div>

                <p className="mt-1 text-sm font-bold" style={{ color: "var(--accent)" }}>
                  {product.price_display}
                </p>

                <div
                  className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11px]"
                  style={{ color: "var(--text-subtle)" }}
                >
                  <span>{task.seller_name}</span>
                  <span>{product.condition_display}</span>
                  <span>{product.region_name}</span>
                  <span className="flex items-center gap-1">
                    <Clock size={11} aria-hidden="true" />
                    {task.waiting_hours != null
                      ? `${task.waiting_hours} soat navbatda`
                      : formatRelativeDate(task.created_at, lang)}
                  </span>
                </div>

                {product.card_specs?.length ? (
                  <p className="mt-1 line-clamp-1 text-[11px]" style={{ color: "var(--text-subtle)" }}>
                    {product.card_specs.join(" · ")}
                  </p>
                ) : null}

                <div className="mt-2 flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={() => approve.mutate(task.id)}
                    disabled={approve.isPending}
                  >
                    <Check size={14} aria-hidden="true" />
                    Tasdiqlash
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setRejecting(task)}
                  >
                    <X size={14} aria-hidden="true" />
                    Rad etish
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>

      {rejecting ? (
        <RejectDialog
          task={rejecting}
          reasons={stats?.reject_reasons || []}
          busy={reject.isPending}
          onClose={() => setRejecting(null)}
          onConfirm={(payload) => reject.mutate({ id: rejecting.id, payload })}
        />
      ) : null}
    </>
  );
}

export default function ModerationPage() {
  const { t } = useI18n();
  const localePath = useLocalePath();

  useHead({
    title: `Moderatsiya — ${t("brand.name")}`,
    robots: "noindex, nofollow",
  });

  return (
    <div className="container-page py-6">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold sm:text-2xl">Moderatsiya navbati</h1>
        <Link to={localePath("/admin")} className="btn btn-ghost btn-sm">
          {t("nav.admin")}
        </Link>
      </div>
      <p className="mb-5 flex items-center gap-1.5 text-sm" style={{ color: "var(--text-muted)" }}>
        <Send size={14} aria-hidden="true" />
        Tasdiqlangan e&apos;lon avtomatik Telegram kanalga chiqadi.
      </p>

      <RequireAuth>
        <ModerationContent />
      </RequireAuth>
    </div>
  );
}
