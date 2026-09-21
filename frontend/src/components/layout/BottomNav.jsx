import { Link, useLocation } from "react-router-dom";
import { Heart, Home, LayoutGrid, PlusCircle, User } from "lucide-react";

import { useI18n, useLocalePath } from "../../i18n";
import { useAuthStore } from "../../store/auth";

/** Mobil pastki navigatsiya — barmoq yetadigan joyda. */
export default function BottomNav() {
  const { t } = useI18n();
  const localePath = useLocalePath();
  const location = useLocation();
  const user = useAuthStore((state) => state.user);

  const items = [
    { to: "/", icon: Home, label: t("nav.home") },
    { to: "/catalog", icon: LayoutGrid, label: t("nav.catalog") },
    { to: "/seller/products/new", icon: PlusCircle, label: t("nav.sell"), highlight: true },
    { to: "/favorites", icon: Heart, label: t("nav.favorites") },
    { to: user ? "/profile" : "/login", icon: User, label: user ? t("nav.profile") : t("nav.login") },
  ];

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t lg:hidden"
      style={{
        background: "var(--surface)",
        // iPhone'dagi pastki chiziq tugmalarni to'smasin
        paddingBottom: "env(safe-area-inset-bottom)",
      }}
      aria-label={t("nav.menu")}
    >
      <div className="flex items-stretch">
        {items.map(({ to, icon: Icon, label, highlight }) => {
          const path = localePath(to);
          const active = location.pathname === path;
          return (
            <Link
              key={to}
              to={path}
              className="flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 px-1 py-1.5 text-[10px] font-medium"
              style={{
                color: highlight || active ? "var(--accent)" : "var(--text-subtle)",
              }}
              aria-current={active ? "page" : undefined}
            >
              <Icon size={highlight ? 24 : 20} strokeWidth={active || highlight ? 2.25 : 1.75} />
              <span className="max-w-full truncate">{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
