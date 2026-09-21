import { useEffect, useRef } from "react";
import { X } from "lucide-react";

import { useI18n } from "../../i18n";

/**
 * Oddiy modal oyna.
 *
 * Nega alohida komponent: bir xil oyna uchta sahifada takrorlanayotgan
 * edi, ularning har birida Escape va fokus mantiqi qaytadan yozilardi.
 *
 * Ochilganda sahifa orqa fonda aylanmaydi va fokus oyna ichiga
 * ko'chadi — klaviatura bilan ishlaydiganlar uchun shart.
 */
export default function Modal({ open, onClose, title, description, children, footer, size = "md" }) {
  const { t } = useI18n();
  const panelRef = useRef(null);
  const bodyRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;

    function handleKey(event) {
      if (event.key === "Escape") onClose?.();
    }
    document.addEventListener("keydown", handleKey);

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    // Fokus mazmundagi birinchi maydonga o'tadi — aks holda
    // klaviatura orqa fonda qolib ketadi. Yopish tugmasi zaxira:
    // unga darhol tushish "oynani yoping" degandek ko'rinadi.
    const selector = "input, select, textarea, button, [href]";
    const target =
      bodyRef.current?.querySelector(selector) || panelRef.current?.querySelector(selector);
    target?.focus();

    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  const maxWidth = size === "lg" ? "max-w-2xl" : size === "sm" ? "max-w-sm" : "max-w-md";

  return (
    <div
      className="fixed inset-0 z-[70] flex items-end justify-center p-0 sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/45"
        onClick={onClose}
        aria-label={t("common.close")}
      />
      <div
        ref={panelRef}
        className={`surface relative max-h-[90vh] w-full overflow-y-auto rounded-b-none p-5 sm:rounded-2xl ${maxWidth}`}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-bold">{title}</h2>
            {description ? (
              <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
                {description}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            className="btn btn-ghost -mr-2 -mt-1 h-9 min-h-9 w-9 shrink-0 px-0"
            onClick={onClose}
            aria-label={t("common.close")}
          >
            <X size={18} />
          </button>
        </div>

        <div className="mt-4" ref={bodyRef}>
          {children}
        </div>

        {footer ? <div className="mt-5 flex gap-2">{footer}</div> : null}
      </div>
    </div>
  );
}
