import { Link, useLocation } from "react-router-dom";
import { Lock } from "lucide-react";

import { useI18n, useLocalePath } from "../../i18n";
import { useAuthStore } from "../../store/auth";
import EmptyState from "../ui/EmptyState";
import PageLoader from "../ui/PageLoader";

/**
 * Maxfiy bo'limlarni o'raydi.
 *
 * Redirect o'rniga sahifa ichida taklif ko'rsatiladi: sessiya tiklanishi
 * bir necha yuz millisekund davom etadi va shu payt yo'naltirish
 * foydalanuvchini "sakrab ketgandek" his qildiradi. Joriy manzil
 * `state.from` ga yoziladi — kirgandan keyin shu yerga qaytariladi.
 */
export default function RequireAuth({ children, permission }) {
  const { t } = useI18n();
  const localePath = useLocalePath();
  const location = useLocation();

  const status = useAuthStore((state) => state.status);
  const can = useAuthStore((state) => state.can);

  if (status === "idle" || status === "loading") {
    return <PageLoader />;
  }

  if (status !== "authenticated") {
    return (
      <EmptyState
        icon={Lock}
        title={t("error.forbidden")}
        description={t("auth.loginTitle")}
        action={
          <Link
            to={localePath("/login")}
            state={{ from: location.pathname + location.search }}
            className="btn btn-primary btn-sm"
          >
            {t("nav.login")}
          </Link>
        }
      />
    );
  }

  if (permission && !can(permission)) {
    return (
      <EmptyState
        icon={Lock}
        title={t("error.forbidden")}
        description={t("error.forbiddenText")}
        action={
          <Link to={localePath("/")} className="btn btn-secondary btn-sm">
            {t("error.goHome")}
          </Link>
        }
      />
    );
  }

  return children;
}
