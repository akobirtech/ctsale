import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  ChevronDown,
  Heart,
  LogOut,
  Menu,
  Moon,
  Plus,
  Search,
  Sun,
  User,
  X,
} from "lucide-react";

import { products as productsApi } from "../../api/endpoints";
import { useDebounce } from "../../hooks/useDebounce";
import {
  LANGUAGES,
  LANGUAGE_LABELS,
  switchLangInPath,
  useI18n,
  useLocalePath,
} from "../../i18n";
import { useAuthStore } from "../../store/auth";
import { useThemeStore } from "../../store/theme";

export default function Navbar({ categories = [] }) {
  const { t, lang } = useI18n();
  const localePath = useLocalePath();
  const navigate = useNavigate();
  const location = useLocation();

  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const theme = useThemeStore((state) => state.theme);
  const toggleTheme = useThemeStore((state) => state.toggle);

  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);

  const debouncedQuery = useDebounce(query, 300);
  const searchRef = useRef(null);

  // Sahifa almashganda ochiq menyular yopilsin.
  useEffect(() => {
    setMenuOpen(false);
    setUserMenuOpen(false);
    setLangMenuOpen(false);
    setSuggestions(null);
  }, [location.pathname]);

  useEffect(() => {
    if (debouncedQuery.trim().length < 2) {
      setSuggestions(null);
      return;
    }
    let cancelled = false;
    productsApi
      .autocomplete(debouncedQuery.trim())
      .then((data) => {
        if (!cancelled) setSuggestions(data);
      })
      .catch(() => {
        // Avtoto'ldirish ixtiyoriy qulaylik — xato bo'lsa jim o'tamiz.
        if (!cancelled) setSuggestions(null);
      });
    return () => {
      cancelled = true;
    };
  }, [debouncedQuery]);

  // Tashqariga bosilganda takliflar yopilsin.
  useEffect(() => {
    function handleClick(event) {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setSuggestions(null);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function submitSearch(event) {
    event.preventDefault();
    const value = query.trim();
    if (value.length < 2) return;
    setSuggestions(null);
    navigate(`${localePath("/search")}?q=${encodeURIComponent(value)}`);
  }

  const featuredCategories = categories.filter((category) => category.is_featured).slice(0, 8);

  return (
    <header
      className="sticky top-0 z-50 border-b backdrop-blur"
      style={{ background: "color-mix(in srgb, var(--bg) 88%, transparent)" }}
    >
      <div className="container-page">
        <div className="flex h-16 items-center gap-3">
          {/* Mobil menyu */}
          <button
            type="button"
            className="btn btn-ghost -ml-2 h-10 min-h-10 w-10 px-0 lg:hidden"
            onClick={() => setMenuOpen((open) => !open)}
            aria-label={t("nav.menu")}
            aria-expanded={menuOpen}
          >
            {menuOpen ? <Menu size={20} /> : <Menu size={20} />}
          </button>

          <Link to={localePath("/")} className="flex shrink-0 items-center gap-2">
            <span
              className="flex h-9 w-9 items-center justify-center rounded-xl text-sm font-black"
              style={{ background: "var(--accent)", color: "var(--accent-text)" }}
              aria-hidden="true"
            >
              CT
            </span>
            <span className="hidden text-base font-bold sm:block">{t("brand.name")}</span>
          </Link>

          {/* Qidiruv */}
          <div ref={searchRef} className="relative min-w-0 flex-1">
            <form onSubmit={submitSearch} role="search">
              <label htmlFor="navbar-search" className="sr-only">
                {t("nav.search")}
              </label>
              <div className="relative">
                <Search
                  size={17}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2"
                  style={{ color: "var(--text-subtle)" }}
                  aria-hidden="true"
                />
                <input
                  id="navbar-search"
                  type="search"
                  className="input pl-9"
                  placeholder={t("home.searchPlaceholder")}
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  autoComplete="off"
                />
              </div>
            </form>

            {suggestions &&
            (suggestions.products?.length > 0 || suggestions.categories?.length > 0) ? (
              <div
                className="surface absolute left-0 right-0 top-full z-50 mt-1.5 overflow-hidden py-1"
                style={{ boxShadow: "var(--shadow-lg)" }}
              >
                {suggestions.categories?.map((item) => (
                  <Link
                    key={`c-${item.slug}`}
                    to={localePath(`/category/${item.slug}`)}
                    className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--surface-hover)]"
                  >
                    <span
                      className="rounded px-1.5 py-0.5 text-[10px] font-bold"
                      style={{ background: "var(--accent-soft)", color: "var(--accent)" }}
                    >
                      {t("catalog.category")}
                    </span>
                    {item.title}
                  </Link>
                ))}
                {suggestions.products?.map((item) => (
                  <Link
                    key={`p-${item.slug}`}
                    to={localePath(`/product/${item.slug}`)}
                    className="block truncate px-3 py-2 text-sm hover:bg-[var(--surface-hover)]"
                  >
                    {item.title}
                  </Link>
                ))}
              </div>
            ) : null}
          </div>

          {/* Desktop amallar */}
          <nav className="hidden items-center gap-1 lg:flex" aria-label="Asosiy">
            <Link to={localePath("/catalog")} className="btn btn-ghost btn-sm">
              {t("nav.catalog")}
            </Link>

            <button
              type="button"
              className="btn btn-ghost h-10 min-h-10 w-10 px-0"
              onClick={toggleTheme}
              aria-label={t("nav.theme")}
              title={t("nav.theme")}
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <div className="relative">
              <button
                type="button"
                className="btn btn-ghost btn-sm gap-1"
                onClick={() => setLangMenuOpen((open) => !open)}
                aria-expanded={langMenuOpen}
                aria-label={t("nav.language")}
              >
                {LANGUAGE_LABELS[lang].short}
                <ChevronDown size={14} aria-hidden="true" />
              </button>
              {langMenuOpen ? (
                <div
                  className="surface absolute right-0 top-full z-50 mt-1 w-36 overflow-hidden py-1"
                  style={{ boxShadow: "var(--shadow-lg)" }}
                >
                  {LANGUAGES.map((code) => (
                    <Link
                      key={code}
                      to={switchLangInPath(location.pathname, code) + location.search}
                      className="block px-3 py-2 text-sm hover:bg-[var(--surface-hover)]"
                      style={code === lang ? { color: "var(--accent)", fontWeight: 600 } : undefined}
                      reloadDocument
                    >
                      {LANGUAGE_LABELS[code].native}
                    </Link>
                  ))}
                </div>
              ) : null}
            </div>

            {user ? (
              <>
                <Link
                  to={localePath("/favorites")}
                  className="btn btn-ghost h-10 min-h-10 w-10 px-0"
                  aria-label={t("nav.favorites")}
                >
                  <Heart size={18} />
                </Link>
                <div className="relative">
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm gap-1.5"
                    onClick={() => setUserMenuOpen((open) => !open)}
                    aria-expanded={userMenuOpen}
                  >
                    <User size={17} />
                    <span className="max-w-24 truncate">{user.first_name || t("nav.profile")}</span>
                  </button>
                  {userMenuOpen ? (
                    <div
                      className="surface absolute right-0 top-full z-50 mt-1 w-52 overflow-hidden py-1"
                      style={{ boxShadow: "var(--shadow-lg)" }}
                    >
                      <Link
                        to={localePath("/profile")}
                        className="block px-3 py-2 text-sm hover:bg-[var(--surface-hover)]"
                      >
                        {t("nav.profile")}
                      </Link>
                      <Link
                        to={localePath("/seller/products")}
                        className="block px-3 py-2 text-sm hover:bg-[var(--surface-hover)]"
                      >
                        {t("nav.myProducts")}
                      </Link>
                      {user.is_staff ? (
                        <Link
                          to={localePath("/admin")}
                          className="block px-3 py-2 text-sm hover:bg-[var(--surface-hover)]"
                        >
                          {t("nav.admin")}
                        </Link>
                      ) : null}
                      <button
                        type="button"
                        onClick={() => logout()}
                        className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-[var(--surface-hover)]"
                        style={{ color: "var(--danger)" }}
                      >
                        <LogOut size={15} />
                        {t("nav.logout")}
                      </button>
                    </div>
                  ) : null}
                </div>
                <Link to={localePath("/seller/products/new")} className="btn btn-primary btn-sm">
                  <Plus size={16} />
                  {t("nav.sell")}
                </Link>
              </>
            ) : (
              <>
                <Link to={localePath("/login")} className="btn btn-ghost btn-sm">
                  {t("nav.login")}
                </Link>
                <Link to={localePath("/seller/products/new")} className="btn btn-primary btn-sm">
                  <Plus size={16} />
                  {t("nav.sell")}
                </Link>
              </>
            )}
          </nav>

          {/* Mobil: faqat mavzu tugmasi, qolgani pastki navigatsiyada */}
          <button
            type="button"
            className="btn btn-ghost h-10 min-h-10 w-10 shrink-0 px-0 lg:hidden"
            onClick={toggleTheme}
            aria-label={t("nav.theme")}
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>

        {/* Desktop kategoriya qatori */}
        {featuredCategories.length > 0 ? (
          <nav
            className="hidden items-center gap-1 overflow-x-auto pb-2 lg:flex"
            aria-label={t("nav.categories")}
          >
            {featuredCategories.map((category) => (
              <Link
                key={category.slug}
                to={localePath(`/category/${category.slug}`)}
                className="whitespace-nowrap rounded-lg px-2.5 py-1 text-[13px] font-medium transition-colors hover:bg-[var(--bg-muted)]"
                style={{ color: "var(--text-muted)" }}
              >
                {category.name}
                <span className="ml-1 text-[11px]" style={{ color: "var(--text-subtle)" }}>
                  {category.products_count}
                </span>
              </Link>
            ))}
          </nav>
        ) : null}
      </div>

      {/* Mobil menyu paneli */}
      {menuOpen ? (
        <div className="border-t lg:hidden" style={{ background: "var(--surface)" }}>
          <div className="container-page max-h-[70vh] space-y-1 overflow-y-auto py-3">
            <div className="mb-2 flex gap-1">
              {LANGUAGES.map((code) => (
                <Link
                  key={code}
                  to={switchLangInPath(location.pathname, code) + location.search}
                  className="btn btn-secondary btn-sm flex-1"
                  style={
                    code === lang
                      ? { background: "var(--accent)", color: "var(--accent-text)", borderColor: "transparent" }
                      : undefined
                  }
                  reloadDocument
                >
                  {LANGUAGE_LABELS[code].short}
                </Link>
              ))}
            </div>
            {categories.map((category) => (
              <Link
                key={category.slug}
                to={localePath(`/category/${category.slug}`)}
                className="flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-[var(--bg-muted)]"
              >
                {category.name}
                <span className="text-xs" style={{ color: "var(--text-subtle)" }}>
                  {category.products_count}
                </span>
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </header>
  );
}
