import { useId } from "react";

/**
 * Forma maydoni: yorliq + kiritish + xato.
 *
 * Xato `aria-describedby` orqali bog'lanadi va `aria-invalid`
 * qo'yiladi — ekran o'quvchi nima noto'g'ri ekanini aytadi.
 */
export default function Field({
  label,
  error,
  hint,
  required,
  children,
  id: providedId,
  ...inputProps
}) {
  const generatedId = useId();
  const id = providedId || generatedId;
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;

  const describedBy = [error ? errorId : null, hint ? hintId : null]
    .filter(Boolean)
    .join(" ");

  return (
    <div>
      {label ? (
        <label htmlFor={id} className="label">
          {label}
          {required ? (
            <span style={{ color: "var(--danger)" }} aria-hidden="true">
              {" "}
              *
            </span>
          ) : null}
        </label>
      ) : null}

      {children ?? (
        <input
          id={id}
          className="input"
          aria-invalid={error ? "true" : undefined}
          aria-describedby={describedBy || undefined}
          required={required}
          {...inputProps}
        />
      )}

      {hint && !error ? (
        <p id={hintId} className="mt-1 text-xs" style={{ color: "var(--text-subtle)" }}>
          {hint}
        </p>
      ) : null}

      {error ? (
        <p id={errorId} className="mt-1 text-xs font-medium" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      ) : null}
    </div>
  );
}

/** Telefon maydoni — O'zbekiston formatida, avtomatik niqob bilan. */
export function PhoneField({ value, onChange, error, label, required, ...rest }) {
  function handleChange(event) {
    // Foydalanuvchi qanday yozsa ham +998XXXXXXXXX ga keltiramiz:
    // nusxa-ko'chirishda qavs va tirelar tushib qolsin.
    const digits = event.target.value.replace(/\D/g, "");
    const local = digits.startsWith("998") ? digits.slice(3) : digits;
    onChange(`+998${local.slice(0, 9)}`);
  }

  const local = (value || "").replace("+998", "");
  const display = [
    local.slice(0, 2),
    local.slice(2, 5),
    local.slice(5, 7),
    local.slice(7, 9),
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <Field label={label} error={error} required={required}>
      <div className="relative">
        <span
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm font-medium"
          style={{ color: "var(--text-muted)" }}
        >
          +998
        </span>
        <input
          type="tel"
          inputMode="numeric"
          autoComplete="tel"
          className="input pl-14"
          placeholder="90 123 45 67"
          value={display}
          onChange={handleChange}
          aria-invalid={error ? "true" : undefined}
          required={required}
          {...rest}
        />
      </div>
    </Field>
  );
}
