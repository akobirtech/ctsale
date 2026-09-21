import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, ChevronRight, LayoutGrid } from "lucide-react";

import { useI18n, useLocalePath } from "../../i18n";

/**
 * Kategoriya mega-menyusi.
 *
 * Nega oddiy ochiluvchi ro'yxat emas: bo'limlar ikki darajali va
 * ularning soni 30 dan oshadi. Bitta ustunli menyu ekranga sig'masdi,
 * foydalanuvchi esa "Noutbuklar" ichida nima borligini bosmasdan
 * ko'ra olishi kerak.
 *
 * Ochilganda chap ustunda asosiy bo'limlar, o'ngda tanlanganining
 * ichki bo'limlari turadi. Sichqoncha olib borilsa yetarli — bosish
 * kerak emas, lekin klaviatura bilan ham yurish mumkin.
 */
export default function CategoryMenu({ categories = [] }) {
  const { t } = useI18n();
  const localePath = useLocalePath();

  const [open, setOpen] = useState(false);
  const [activeSlug, setActiveSlug] = useState(null);
  const containerRef = useRef(null);

  const roots = categories.filter((category) => category.products_count > 0 || category.children?.length);
  const active = roots.find((category) => category.slug === activeSlug) || roots[0] || null;

  // Tashqariga bosilsa yoki Escape bosilsa menyu yopiladi.
  useEffect(() => {
    if (!open) return undefined;

    function handlePointer(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    function handleKey(event) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handlePointer);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handlePointer);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  if (roots.length === 0) return null;

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        className="btn btn-secondary btn-sm whitespace-nowrap"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="true"
      >
        <LayoutGrid size={16} />
        {t("nav.categories")}
        <ChevronDown
          size={14}
          style={{ transform: open ? "rotate(180deg)" : undefined, transition: "transform .15s" }}
        />
      </button>

      {open ? (
        <div
          className="surface absolute left-0 top-full z-50 mt-1 flex w-[min(46rem,calc(100vw-2rem))] overflow-hidden"
          style={{ boxShadow: "var(--shadow-lg)" }}
        >
          {/* Chap ustun — asosiy bo'limlar */}
          <ul
            className="max-h-[70vh] w-1/2 shrink-0 overflow-y-auto border-r py-1.5"
            style={{ background: "var(--bg-muted)" }}
          >
            {roots.map((category) => {
              const isActive = active?.slug === category.slug;
              return (
                <li key={category.slug}>
                  <Link
                    to={localePath(`/category/${category.slug}`)}
                    className="flex items-center justify-between gap-2 px-3 py-2 text-sm font-medium"
                    style={isActive ? { background: "var(--surface)", color: "var(--accent)" } : undefined}
                    onMouseEnter={() => setActiveSlug(category.slug)}
                    onFocus={() => setActiveSlug(category.slug)}
                    onClick={() => setOpen(false)}
                  >
                    <span className="truncate">{category.name}</span>
                    <span className="flex items-center gap-1 text-xs" style={{ color: "var(--text-subtle)" }}>
                      {category.products_count}
                      {category.children?.length ? <ChevronRight size={13} /> : null}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>

          {/* O'ng ustun — tanlangan bo'limning ichi */}
          <div className="max-h-[70vh] flex-1 overflow-y-auto p-4">
            {active ? (
              <>
                <Link
                  to={localePath(`/category/${active.slug}`)}
                  className="text-sm font-semibold hover:underline"
                  onClick={() => setOpen(false)}
                >
                  {active.name}
                </Link>
                {active.children?.length ? (
                  <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1">
                    {active.children.map((child) => (
                      <li key={child.slug}>
                        <Link
                          to={localePath(`/category/${child.slug}`)}
                          className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-[13px] hover:bg-[var(--bg-muted)]"
                          style={{ color: "var(--text-muted)" }}
                          onClick={() => setOpen(false)}
                        >
                          <span className="truncate">{child.name}</span>
                          <span className="text-[11px]" style={{ color: "var(--text-subtle)" }}>
                            {child.products_count}
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-[13px]" style={{ color: "var(--text-subtle)" }}>
                    {t("catalog.noSubcategories")}
                  </p>
                )}
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}

/**
 * Mobil variant: mega-menyu tor ekranga sig'maydi, shuning uchun
 * bir xil ma'lumot yig'iladigan ro'yxat sifatida ko'rsatiladi.
 */
export function CategoryAccordion({ categories = [], onNavigate }) {
  const localePath = useLocalePath();
  const [openSlug, setOpenSlug] = useState(null);

  return (
    <ul className="space-y-0.5">
      {categories.map((category) => {
        const isOpen = openSlug === category.slug;
        const hasChildren = Boolean(category.children?.length);

        return (
          <li key={category.slug}>
            <div className="flex items-center">
              <Link
                to={localePath(`/category/${category.slug}`)}
                className="flex flex-1 items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-[var(--bg-muted)]"
                onClick={onNavigate}
              >
                {category.name}
                <span className="text-xs" style={{ color: "var(--text-subtle)" }}>
                  {category.products_count}
                </span>
              </Link>
              {hasChildren ? (
                <button
                  type="button"
                  className="btn btn-ghost h-9 min-h-9 w-9 shrink-0 px-0"
                  onClick={() => setOpenSlug(isOpen ? null : category.slug)}
                  aria-expanded={isOpen}
                  aria-label={category.name}
                >
                  <ChevronDown
                    size={16}
                    style={{ transform: isOpen ? "rotate(180deg)" : undefined, transition: "transform .15s" }}
                  />
                </button>
              ) : null}
            </div>

            {isOpen && hasChildren ? (
              <ul className="mb-1 ml-3 border-l pl-3">
                {category.children.map((child) => (
                  <li key={child.slug}>
                    <Link
                      to={localePath(`/category/${child.slug}`)}
                      className="flex items-center justify-between rounded-lg px-3 py-2 text-[13px] hover:bg-[var(--bg-muted)]"
                      style={{ color: "var(--text-muted)" }}
                      onClick={onNavigate}
                    >
                      {child.name}
                      <span className="text-[11px]" style={{ color: "var(--text-subtle)" }}>
                        {child.products_count}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
