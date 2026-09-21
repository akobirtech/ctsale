import { useState } from "react";
import { ChevronDown } from "lucide-react";

import { useI18n } from "../../i18n";

function Group({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b py-3 last:border-b-0">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-2 text-left text-sm font-semibold"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        {title}
        <ChevronDown
          size={16}
          className="shrink-0 transition-transform"
          style={{ transform: open ? "rotate(180deg)" : "none", color: "var(--text-subtle)" }}
          aria-hidden="true"
        />
      </button>
      {open ? <div className="mt-3 space-y-2">{children}</div> : null}
    </div>
  );
}

function CheckOption({ label, count, checked, onChange }) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 shrink-0 accent-[var(--accent)]"
      />
      <span className="min-w-0 flex-1 truncate">{label}</span>
      {count != null ? (
        <span className="shrink-0 text-xs" style={{ color: "var(--text-subtle)" }}>
          {count}
        </span>
      ) : null}
    </label>
  );
}

/**
 * Filtrlar paneli.
 *
 * Barcha holat URL'da yashaydi (`params`), shuning uchun filtrlangan
 * sahifani havola sifatida yuborish va orqaga tugmasi to'g'ri ishlaydi.
 */
export default function FilterPanel({ facets = {}, params = {}, onChange, onClear }) {
  const { t } = useI18n();

  const setParam = (key, value) => onChange({ ...params, [key]: value || undefined, page: undefined });

  const toggleInList = (key, value) => {
    const current = (params[key] || "").split(",").filter(Boolean);
    const next = current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value];
    setParam(key, next.join(","));
  };

  const activeCount = Object.entries(params).filter(
    ([key, value]) => value && !["page", "sort", "q", "lang", "facets"].includes(key)
  ).length;

  return (
    <div>
      <div className="flex items-center justify-between gap-2 pb-2">
        <h2 className="text-sm font-bold">{t("catalog.filters")}</h2>
        {activeCount > 0 ? (
          <button
            type="button"
            onClick={onClear}
            className="text-xs font-semibold"
            style={{ color: "var(--accent)" }}
          >
            {t("catalog.clear")} ({activeCount})
          </button>
        ) : null}
      </div>

      {/* Narx */}
      <Group title={t("catalog.price")}>
        <div className="flex items-center gap-2">
          <input
            type="number"
            inputMode="numeric"
            className="input"
            placeholder={facets.price?.min ? String(Math.round(facets.price.min)) : t("catalog.from")}
            value={params.price_min || ""}
            onChange={(event) => setParam("price_min", event.target.value)}
            aria-label={t("catalog.from")}
          />
          <span style={{ color: "var(--text-subtle)" }}>—</span>
          <input
            type="number"
            inputMode="numeric"
            className="input"
            placeholder={facets.price?.max ? String(Math.round(facets.price.max)) : t("catalog.to")}
            value={params.price_max || ""}
            onChange={(event) => setParam("price_max", event.target.value)}
            aria-label={t("catalog.to")}
          />
        </div>
      </Group>

      {/* Holat */}
      {facets.condition?.length ? (
        <Group title={t("catalog.condition")}>
          {facets.condition.map((option) => (
            <CheckOption
              key={option.value}
              label={option.label}
              count={option.count}
              checked={(params.condition || "").split(",").includes(option.value)}
              onChange={() => toggleInList("condition", option.value)}
            />
          ))}
        </Group>
      ) : null}

      {/* Brend */}
      {facets.brand?.length ? (
        <Group title={t("catalog.brand")}>
          <ScrollableOptions
            options={facets.brand}
            selected={(params.brand || "").split(",").filter(Boolean)}
            onToggle={(value) => toggleInList("brand", value)}
          />
        </Group>
      ) : null}

      {/* Viloyat */}
      {facets.region?.length ? (
        <Group title={t("catalog.region")} defaultOpen={false}>
          <ScrollableOptions
            options={facets.region}
            selected={params.region ? [params.region] : []}
            onToggle={(value) => setParam("region", params.region === value ? "" : value)}
          />
        </Group>
      ) : null}

      {/* Kategoriyaga bog'liq dinamik xususiyatlar */}
      {(facets.specs || []).map((spec) =>
        spec.type === "range" ? (
          <Group key={spec.code} title={`${spec.label}${spec.unit ? `, ${spec.unit}` : ""}`} defaultOpen={false}>
            <div className="flex items-center gap-2">
              <input
                type="number"
                inputMode="numeric"
                className="input"
                placeholder={String(spec.min)}
                value={params[`spec_${spec.code}_min`] || ""}
                onChange={(event) => setParam(`spec_${spec.code}_min`, event.target.value)}
                aria-label={`${spec.label} ${t("catalog.from")}`}
              />
              <span style={{ color: "var(--text-subtle)" }}>—</span>
              <input
                type="number"
                inputMode="numeric"
                className="input"
                placeholder={String(spec.max)}
                value={params[`spec_${spec.code}_max`] || ""}
                onChange={(event) => setParam(`spec_${spec.code}_max`, event.target.value)}
                aria-label={`${spec.label} ${t("catalog.to")}`}
              />
            </div>
          </Group>
        ) : (
          <Group key={spec.code} title={spec.label} defaultOpen={false}>
            <ScrollableOptions
              options={spec.options}
              selected={(params[`spec_${spec.code}`] || "").split(",").filter(Boolean)}
              onToggle={(value) => toggleInList(`spec_${spec.code}`, value)}
            />
          </Group>
        )
      )}

      {/* Qo'shimcha bayroqlar */}
      <Group title={t("common.all")} defaultOpen={false}>
        <CheckOption
          label={t("catalog.warranty")}
          checked={params.has_warranty === "true"}
          onChange={(checked) => setParam("has_warranty", checked ? "true" : "")}
        />
        <CheckOption
          label={t("catalog.exchange")}
          checked={params.is_exchange_possible === "true"}
          onChange={(checked) => setParam("is_exchange_possible", checked ? "true" : "")}
        />
        <CheckOption
          label={t("catalog.negotiable")}
          checked={params.is_negotiable === "true"}
          onChange={(checked) => setParam("is_negotiable", checked ? "true" : "")}
        />
        <CheckOption
          label={t("catalog.onlyWithVideo")}
          checked={params.with_video === "true"}
          onChange={(checked) => setParam("with_video", checked ? "true" : "")}
        />
      </Group>
    </div>
  );
}

/** Uzun ro'yxatlar uchun: avval 6 ta, keyin "ko'proq". */
function ScrollableOptions({ options = [], selected = [], onToggle }) {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? options : options.slice(0, 6);

  return (
    <>
      {visible.map((option) => (
        <CheckOption
          key={option.value}
          label={option.label}
          count={option.count}
          checked={selected.includes(option.value)}
          onChange={() => onToggle(option.value)}
        />
      ))}
      {options.length > 6 ? (
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="text-xs font-semibold"
          style={{ color: "var(--accent)" }}
        >
          {expanded ? t("catalog.showLess") : `${t("catalog.showMore")} (${options.length - 6})`}
        </button>
      ) : null}
    </>
  );
}
