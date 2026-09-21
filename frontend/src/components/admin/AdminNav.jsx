import { NavLink } from "react-router-dom";
import {
  Flag,
  LayoutDashboard,
  Package,
  Send,
  ShieldCheck,
  Tags,
  Users,
} from "lucide-react";

import { useI18n, useLocalePath } from "../../i18n";

/**
 * Admin bo'limlari orasida o'tish.
 *
 * Har bir sahifa o'z sarlavhasini takrorlab yozmasligi uchun
 * navigatsiya bitta joyda. Gorizontal aylanadi — mobil ekranda
 * yettita bo'lim bitta qatorga sig'maydi.
 */
const SECTIONS = [
  { to: "/admin", label: "nav.admin", icon: LayoutDashboard, end: true },
  { to: "/admin/moderation", label: "admin.moderation", icon: ShieldCheck },
  { to: "/admin/products", label: "admin.products", icon: Package },
  { to: "/admin/reports", label: "admin.reports", icon: Flag },
  { to: "/admin/catalog", label: "admin.catalog", icon: Tags },
  { to: "/admin/users", label: "admin.users", icon: Users },
  { to: "/admin/telegram", label: "admin.telegram", icon: Send },
];

export default function AdminNav() {
  const { t } = useI18n();
  const localePath = useLocalePath();

  return (
    <nav className="mb-5 flex gap-1 overflow-x-auto pb-1" aria-label={t("nav.admin")}>
      {SECTIONS.map((section) => (
        <NavLink
          key={section.to}
          to={localePath(section.to)}
          end={section.end}
          className="flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors hover:bg-[var(--bg-muted)]"
          style={({ isActive }) =>
            isActive
              ? { background: "var(--accent)", color: "var(--accent-text)" }
              : { color: "var(--text-muted)" }
          }
        >
          <section.icon size={15} aria-hidden="true" />
          {t(section.label)}
        </NavLink>
      ))}
    </nav>
  );
}
