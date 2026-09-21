import { AlertTriangle, RefreshCw } from "lucide-react";

import { useI18n } from "../../i18n";

export default function ErrorState({ title, description, onRetry, status }) {
  const { t } = useI18n();

  return (
    <div className="flex flex-col items-center justify-center px-4 py-16 text-center" role="alert">
      <div
        className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl"
        style={{ background: "var(--danger-soft)", color: "var(--danger)" }}
      >
        <AlertTriangle size={28} strokeWidth={1.75} aria-hidden="true" />
      </div>
      {status ? (
        <span className="mb-1 text-xs font-bold tracking-widest" style={{ color: "var(--text-subtle)" }}>
          {status}
        </span>
      ) : null}
      <h3 className="text-base font-semibold" style={{ color: "var(--text)" }}>
        {title || t("error.generic")}
      </h3>
      {description ? (
        <p className="mt-1.5 max-w-md text-sm" style={{ color: "var(--text-muted)" }}>
          {description}
        </p>
      ) : null}
      {onRetry ? (
        <button type="button" className="btn btn-secondary btn-sm mt-5" onClick={onRetry}>
          <RefreshCw size={15} aria-hidden="true" />
          {t("error.tryAgain")}
        </button>
      ) : null}
    </div>
  );
}
