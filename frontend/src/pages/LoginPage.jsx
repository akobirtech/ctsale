import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";

import { fieldErrors } from "../api/client";
import Field, { PhoneField } from "../components/ui/Field";
import { useToast } from "../hooks/useToast";
import { useI18n, useLocalePath } from "../i18n";
import { useHead } from "../seo/Head";
import { useAuthStore } from "../store/auth";

export default function LoginPage() {
  const { t } = useI18n();
  const localePath = useLocalePath();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const login = useAuthStore((state) => state.login);

  const [phone, setPhone] = useState("+998");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useHead({
    title: `${t("auth.loginTitle")} — ${t("brand.name")}`,
    // Kirish sahifasining qidiruvda ko'rinishi shart emas.
    robots: "noindex, follow",
  });

  async function handleSubmit(event) {
    event.preventDefault();
    setErrors({});
    setSubmitting(true);

    try {
      await login({ phone, password });
      // Foydalanuvchi qayerdan kelgan bo'lsa o'sha yerga qaytaramiz.
      const target = location.state?.from || localePath("/");
      navigate(target, { replace: true });
    } catch (error) {
      const fields = fieldErrors(error);
      setErrors(fields);
      // Maydonga bog'lanmagan xato (parol noto'g'ri, blok, limit) — toast.
      if (!Object.keys(fields).length || fields.detail) {
        toast.error(error.message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container-page flex justify-center py-10 sm:py-16">
      <div className="w-full max-w-sm">
        <div className="surface p-6 sm:p-7">
          <h1 className="text-xl font-bold">{t("auth.loginTitle")}</h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
            {t("brand.tagline")}
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
            <PhoneField
              label={t("auth.phone")}
              value={phone}
              onChange={setPhone}
              error={errors.phone}
              required
              autoFocus
            />

            <Field
              label={t("auth.password")}
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              error={errors.password}
              required
            />

            <button type="submit" className="btn btn-primary w-full" disabled={submitting}>
              <LogIn size={17} aria-hidden="true" />
              {submitting ? t("common.loading") : t("nav.login")}
            </button>
          </form>

          <div className="mt-4 flex flex-col gap-2 text-center text-sm">
            <Link
              to={localePath("/password-reset")}
              className="hover:underline"
              style={{ color: "var(--accent)" }}
            >
              {t("auth.forgotPassword")}
            </Link>
            <p style={{ color: "var(--text-muted)" }}>
              {t("auth.noAccount")}{" "}
              <Link
                to={localePath("/register")}
                className="font-semibold hover:underline"
                style={{ color: "var(--accent)" }}
              >
                {t("nav.register")}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
