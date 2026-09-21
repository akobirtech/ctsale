import Field from "../ui/Field";

/**
 * Kategoriyaga qarab dinamik yaratiladigan xususiyat maydonlari.
 *
 * Sxema backenddan keladi (`/categories/{slug}/attributes/`), shuning
 * uchun admin yangi xususiyat qo'shganda frontend kodini o'zgartirish
 * kerak bo'lmaydi.
 */
export default function SpecFields({ attributes = [], values = {}, errors = {}, onChange }) {
  if (!attributes.length) {
    return (
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
        Bu kategoriya uchun qo&apos;shimcha xususiyat talab qilinmaydi.
      </p>
    );
  }

  const set = (code, value) => onChange({ ...values, [code]: value });

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {attributes.map((attribute) => {
        const value = values[attribute.code];
        const error = errors[attribute.code];
        const label = attribute.unit
          ? `${attribute.label}, ${attribute.unit}`
          : attribute.label;

        if (attribute.data_type === "boolean") {
          return (
            <Field key={attribute.code} label={label} error={error}>
              <label className="flex cursor-pointer items-center gap-2 py-2 text-sm">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-[var(--accent)]"
                  checked={Boolean(value)}
                  onChange={(event) => set(attribute.code, event.target.checked)}
                />
                Ha
              </label>
            </Field>
          );
        }

        if (attribute.data_type === "select") {
          return (
            <Field
              key={attribute.code}
              label={label}
              error={error}
              required={attribute.is_required}
            >
              <select
                className="input"
                value={value ?? ""}
                onChange={(event) => set(attribute.code, event.target.value || undefined)}
                aria-invalid={error ? "true" : undefined}
              >
                <option value="">—</option>
                {attribute.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
          );
        }

        if (attribute.data_type === "multiselect") {
          const selected = Array.isArray(value) ? value : [];
          return (
            <Field key={attribute.code} label={label} error={error}>
              <div className="flex flex-wrap gap-1.5 py-1">
                {attribute.options.map((option) => {
                  const active = selected.includes(option.value);
                  return (
                    <button
                      key={option.value}
                      type="button"
                      className="btn btn-sm"
                      style={
                        active
                          ? { background: "var(--accent)", color: "var(--accent-text)" }
                          : { background: "var(--bg-muted)", color: "var(--text-muted)" }
                      }
                      aria-pressed={active}
                      onClick={() =>
                        set(
                          attribute.code,
                          active
                            ? selected.filter((item) => item !== option.value)
                            : [...selected, option.value]
                        )
                      }
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </Field>
          );
        }

        const numeric = ["integer", "decimal"].includes(attribute.data_type);
        return (
          <Field
            key={attribute.code}
            label={label}
            error={error}
            required={attribute.is_required}
            type={numeric ? "number" : "text"}
            inputMode={numeric ? "decimal" : undefined}
            step={attribute.data_type === "decimal" ? "any" : undefined}
            placeholder={attribute.placeholder || undefined}
            value={value ?? ""}
            onChange={(event) => {
              const raw = event.target.value;
              if (raw === "") {
                set(attribute.code, undefined);
              } else {
                set(attribute.code, numeric ? Number(raw) : raw);
              }
            }}
          />
        );
      })}
    </div>
  );
}
