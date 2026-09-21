import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ShieldCheck, UserPlus } from "lucide-react";

import { fieldErrors } from "../api/client";
import { auth as authApi } from "../api/endpoints";
import Field, { PhoneField } from "../components/ui/Field";
import { useToast } from "../hooks/useToast";
import { useI18n, useLocalePath } from "../i18n";
import { useHead } from "../seo/Head";
import { useAuthStore } from "../store/auth";
import { formatPhone } from "../utils/format";

const STEP_FORM = "form";
const STEP_CODE = "code";

export default function RegisterPage() {
  const { t } = useI18n();
  const localePath = useLocalePath();
  const navigate = useNavigate();
  const toast = useToast();
  const setSession = useAuthStore((state) => state.setSession);

  const [step, setStep] = useState(STEP_FORM);
  const [form, setForm] = useState({
    phone: "+998",
    first_name: "",
    last_name: "",
    password: "",
    password_confirm: "",
  });
  const [code, setCode] = useState("");
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(0);

  useHead({
    title: `${t("auth.registerTitle")} — ${t("brand.name")}`,
    robots: "noindex, follow",
  });

  // Kodni qayta yuborish taymeri.
  useEffect(() => {
    if (secondsLeft <= 0) return undefined;
    const timer = setTimeout(() => setSecondsLeft((value) => value - 1), 1000);
    return () => clearTimeout(timer);
  }, [secondsLeft]);

  const update = (field) => (event) =>
    setForm((current) => ({ ...current, [field]: event.target.value }));

  async function submitForm(event) {
    event.preventDefault();
    setErrors({});
    setSubmitting(true);

    try {
      const response = await authApi.register(form);
      setStep(STEP_CODE);
      setSecondsLeft(60);

      // Dev muhitida SMS provayder yo'q — backend kodni javobga
      // qo'shadi va uni darhol ko'rsatamiz (DEBUG=False da bo'lmaydi).
      if (response.debug_code) {
        setCode(response.debug_code);
        toast.info(`Test kodi: ${response.debug_code}`);
      } else {
        toast.success(t("auth.codeSentTo", { phone: formatPhone(form.phone) }));
      }
    } catch (error) {
      const fields = fieldErrors(error);
      setErrors(fields);
      if (!Object.keys(fields).length || fields.detail || fields.non_field_errors) {
        toast.error(fields.non_field_errors || error.message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function submitCode(event) {
    event.preventDefault();
    setErrors({});
    setSubmitting(true);

    try {
      const payload = await authApi.verify({ phone: form.phone, code });
      setSession(payload);
      toast.success(t("auth.verify"));
      navigate(localePath("/"), { replace: true });
    } catch (error) {
      setErrors(fieldErrors(error));
      toast.error(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function resend() {
    try {
      const response = await authApi.resendOtp({ phone: form.phone });
      setSecondsLeft(60);
      if (response.debug_code) {
        setCode(response.debug_code);
        toast.info(`Test kodi: ${response.debug_code}`);
      } else {
        toast.success(t("auth.resendCode"));
      }
    } catch (error) {
      toast.error(error.message);
    }
  }

  return (
    <div className="container-page flex justify-center py-10 sm:py-16">
      <div className="w-full max-w-sm">
        <div className="surface p-6 sm:p-7">
          {step === STEP_FORM ? (
            <>
              <h1 className="text-xl font-bold">{t("auth.registerTitle")}</h1>
              <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
                {t("home.ctaText")}
              </p>

              <form onSubmit={submitForm} className="mt-6 space-y-4" noValidate>
                <PhoneField
                  label={t("auth.phone")}
                  value={form.phone}
                  onChange={(value) => setForm((current) => ({ ...current, phone: value }))}
                  error={errors.phone}
                  required
                  autoFocus
                />

                <div className="grid grid-cols-2 gap-3">
                  <Field
                    label={t("auth.firstName")}
                    autoComplete="given-name"
                    value={form.first_name}
                    onChange={update("first_name")}
                    error={errors.first_name}
                  />
                  <Field
                    label={t("auth.lastName")}
                    autoComplete="family-name"
                    value={form.last_name}
                    onChange={update("last_name")}
                    error={errors.last_name}
                  />
                </div>

                <Field
                  label={t("auth.password")}
                  type="password"
                  autoComplete="new-password"
                  value={form.password}
                  onChange={update("password")}
                  error={errors.password}
                  hint="Kamida 8 ta belgi, harf va raqam bilan"
                  required
                />

                <Field
                  label={t("auth.passwordConfirm")}
                  type="password"
                  autoComplete="new-password"
                  value={form.password_confirm}
                  onChange={update("password_confirm")}
                  error={errors.password_confirm}
                  required
                />

                <button type="submit" className="btn btn-primary w-full" disabled={submitting}>
                  <UserPlus size={17} aria-hidden="true" />
                  {submitting ? t("common.loading") : t("auth.sendCode")}
                </button>
              </form>

              <p className="mt-4 text-center text-sm" style={{ color: "var(--text-muted)" }}>
                {t("auth.hasAccount")}{" "}
                <Link
                  to={localePath("/login")}
                  className="font-semibold hover:underline"
                  style={{ color: "var(--accent)" }}
                >
                  {t("nav.login")}
                </Link>
              </p>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => setStep(STEP_FORM)}
                className="btn btn-ghost btn-sm -ml-3 mb-2"
              >
                <ArrowLeft size={15} aria-hidden="true" />
                {t("seller.back")}
              </button>

              <div
                className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl"
                style={{ background: "var(--accent-soft)", color: "var(--accent)" }}
              >
                <ShieldCheck size={22} aria-hidden="true" />
              </div>

              <h1 className="text-xl font-bold">{t("auth.verify")}</h1>
              <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
                {t("auth.codeSentTo", { phone: formatPhone(form.phone) })}
              </p>

              <form onSubmit={submitCode} className="mt-6 space-y-4" noValidate>
                <Field label={t("auth.code")} error={errors.code || errors.detail}>
                  <input
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={6}
                    className="input text-center text-2xl font-bold tracking-[0.4em]"
                    placeholder="000000"
                    value={code}
                    onChange={(event) => setCode(event.target.value.replace(/\D/g, ""))}
                    aria-invalid={errors.code ? "true" : undefined}
                    autoFocus
                  />
                </Field>

                <button
                  type="submit"
                  className="btn btn-primary w-full"
                  disabled={submitting || code.length < 4}
                >
                  {submitting ? t("common.loading") : t("auth.verify")}
                </button>
              </form>

              <div className="mt-4 text-center text-sm">
                {secondsLeft > 0 ? (
                  <span style={{ color: "var(--text-subtle)" }}>
                    {t("auth.codeExpires", { seconds: secondsLeft })}
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={resend}
                    className="font-semibold hover:underline"
                    style={{ color: "var(--accent)" }}
                  >
                    {t("auth.resendCode")}
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
