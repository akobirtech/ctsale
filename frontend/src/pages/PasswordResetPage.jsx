import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, KeyRound } from "lucide-react";

import { fieldErrors } from "../api/client";
import { auth as authApi } from "../api/endpoints";
import Field, { PhoneField } from "../components/ui/Field";
import { useToast } from "../hooks/useToast";
import { useI18n, useLocalePath } from "../i18n";
import { useHead } from "../seo/Head";
import { useAuthStore } from "../store/auth";
import { formatPhone } from "../utils/format";

export default function PasswordResetPage() {
  const { t } = useI18n();
  const localePath = useLocalePath();
  const navigate = useNavigate();
  const toast = useToast();
  const setSession = useAuthStore((state) => state.setSession);

  const [step, setStep] = useState("request");
  const [phone, setPhone] = useState("+998");
  const [form, setForm] = useState({
    code: "",
    new_password: "",
    new_password_confirm: "",
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useHead({
    title: `${t("auth.forgotPassword")} — ${t("brand.name")}`,
    robots: "noindex, nofollow",
  });

  const update = (field) => (event) =>
    setForm((current) => ({ ...current, [field]: event.target.value }));

  async function requestCode(event) {
    event.preventDefault();
    setErrors({});
    setSubmitting(true);
    try {
      const response = await authApi.resetRequest({ phone });
      setStep("confirm");
      // Backend raqam mavjudligidan qat'i nazar bir xil javob beradi —
      // bu hisob borligini aniqlash imkonini bermaslik uchun.
      if (response.debug_code) {
        setForm((current) => ({ ...current, code: response.debug_code }));
        toast.info(`Test kodi: ${response.debug_code}`);
      } else {
        toast.success(response.detail);
      }
    } catch (error) {
      setErrors(fieldErrors(error));
      toast.error(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function confirmReset(event) {
    event.preventDefault();
    setErrors({});
    setSubmitting(true);
    try {
      const payload = await authApi.resetConfirm({ phone, ...form });
      setSession(payload);
      toast.success(payload.detail);
      navigate(localePath("/"), { replace: true });
    } catch (error) {
      const fields = fieldErrors(error);
      setErrors(fields);
      if (!Object.keys(fields).length || fields.detail) toast.error(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container-page flex justify-center py-10 sm:py-16">
      <div className="w-full max-w-sm">
        <div className="surface p-6 sm:p-7">
          <div
            className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl"
            style={{ background: "var(--accent-soft)", color: "var(--accent)" }}
          >
            <KeyRound size={22} aria-hidden="true" />
          </div>

          {step === "request" ? (
            <>
              <h1 className="text-xl font-bold">{t("auth.forgotPassword")}</h1>
              <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
                Telefon raqamingizni kiriting — tasdiqlash kodi yuboramiz.
              </p>

              <form onSubmit={requestCode} className="mt-6 space-y-4" noValidate>
                <PhoneField
                  label={t("auth.phone")}
                  value={phone}
                  onChange={setPhone}
                  error={errors.phone}
                  required
                  autoFocus
                />
                <button type="submit" className="btn btn-primary w-full" disabled={submitting}>
                  {submitting ? t("common.loading") : t("auth.sendCode")}
                </button>
              </form>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => setStep("request")}
                className="btn btn-ghost btn-sm -ml-3 mb-2"
              >
                <ArrowLeft size={15} aria-hidden="true" />
                {t("seller.back")}
              </button>

              <h1 className="text-xl font-bold">Yangi parol</h1>
              <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
                {t("auth.codeSentTo", { phone: formatPhone(phone) })}
              </p>

              <form onSubmit={confirmReset} className="mt-6 space-y-4" noValidate>
                <Field label={t("auth.code")} error={errors.code || errors.detail}>
                  <input
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={6}
                    className="input text-center text-2xl font-bold tracking-[0.4em]"
                    placeholder="000000"
                    value={form.code}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        code: event.target.value.replace(/\D/g, ""),
                      }))
                    }
                    autoFocus
                  />
                </Field>

                <Field
                  label="Yangi parol"
                  type="password"
                  autoComplete="new-password"
                  value={form.new_password}
                  onChange={update("new_password")}
                  error={errors.new_password}
                  hint="Kamida 8 ta belgi, harf va raqam bilan"
                  required
                />
                <Field
                  label={t("auth.passwordConfirm")}
                  type="password"
                  autoComplete="new-password"
                  value={form.new_password_confirm}
                  onChange={update("new_password_confirm")}
                  error={errors.new_password_confirm}
                  required
                />

                <button type="submit" className="btn btn-primary w-full" disabled={submitting}>
                  {submitting ? t("common.loading") : t("common.save")}
                </button>
              </form>
            </>
          )}

          <p className="mt-4 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <Link
              to={localePath("/login")}
              className="font-semibold hover:underline"
              style={{ color: "var(--accent)" }}
            >
              {t("nav.login")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
