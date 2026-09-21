import { useEffect, useState } from "react";

import { reports as reportsApi } from "../../api/endpoints";
import { useI18n } from "../../i18n";
import { useToast } from "../../hooks/useToast";
import Field from "../ui/Field";
import Modal from "../ui/Modal";

// Sabablar ro'yxati backenddan keladi: moderatorlar ko'radigan
// qiymatlar bilan bir xil bo'lishi kerak.
export default function ReportModal({ open, onClose, slug, productTitle }) {
  const { t } = useI18n();
  const toast = useToast();

  const [reasons, setReasons] = useState([]);
  const [reason, setReason] = useState("");
  const [comment, setComment] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open || reasons.length) return;
    reportsApi
      .reasons()
      .then((data) => {
        setReasons(data);
        setReason((current) => current || data[0]?.value || "");
      })
      .catch(() => setError(t("error.generic")));
  }, [open, reasons.length, t]);

  // Oyna yopilganda matn qolib ketmasin.
  useEffect(() => {
    if (!open) {
      setComment("");
      setError("");
    }
  }, [open]);

  const commentRequired = reason === "other";

  async function submit(event) {
    event.preventDefault();
    if (commentRequired && comment.trim().length < 10) {
      setError(t("product.reportCommentRequired"));
      return;
    }

    setSending(true);
    setError("");
    try {
      const data = await reportsApi.create({ slug, reason, comment: comment.trim() });
      toast.success(data.detail || t("product.reportSent"));
      onClose();
    } catch (requestError) {
      const body = requestError?.response?.data?.error;
      // 409 — allaqachon shikoyat qilingan; bu xato emas, holat.
      setError(body?.message || t("error.generic"));
    } finally {
      setSending(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={t("product.report")}
      description={productTitle}
      footer={
        <>
          <button type="button" className="btn btn-secondary flex-1" onClick={onClose}>
            {t("common.cancel")}
          </button>
          <button
            type="submit"
            form="report-form"
            className="btn btn-primary flex-1"
            disabled={sending || !reason}
          >
            {sending ? t("common.loading") : t("product.reportSubmit")}
          </button>
        </>
      }
    >
      <form id="report-form" onSubmit={submit} className="space-y-3">
        <Field label={t("product.reportReason")} required>
          <select
            className="input"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          >
            {reasons.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </Field>

        <Field
          label={t("product.reportComment")}
          required={commentRequired}
          hint={t("product.reportHint")}
        >
          <textarea
            className="input min-h-24"
            rows={4}
            maxLength={1000}
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder={t("product.reportPlaceholder")}
          />
        </Field>

        {error ? (
          <p className="text-sm" style={{ color: "var(--danger)" }} role="alert">
            {error}
          </p>
        ) : null}
      </form>
    </Modal>
  );
}
