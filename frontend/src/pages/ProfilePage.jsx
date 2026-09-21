import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bell, Heart, KeyRound, LogOut, Package, Save, Store, User } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { fieldErrors } from "../api/client";
import { auth as authApi, catalog as catalogApi } from "../api/endpoints";
import AvatarUpload from "../components/auth/AvatarUpload";
import RequireAuth from "../components/auth/RequireAuth";
import Field from "../components/ui/Field";
import { useToast } from "../hooks/useToast";
import { useI18n, useLocalePath } from "../i18n";
import { useHead } from "../seo/Head";
import { useAuthStore } from "../store/auth";
import { formatPhone } from "../utils/format";

function ProfileForm() {
  const { t } = useI18n();
  const toast = useToast();
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    region: "",
    district: "",
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  // Profil yuklangach forma to'ldiriladi.
  useEffect(() => {
    if (!user) return;
    setForm({
      first_name: user.first_name || "",
      last_name: user.last_name || "",
      email: user.email || "",
      region: user.region || "",
      district: user.district || "",
    });
  }, [user]);

  const { data: regions = [] } = useQuery({
    queryKey: ["regions-with-districts"],
    queryFn: () => catalogApi.regions(true),
    staleTime: 30 * 60_000,
  });

  const districts = regions.find((r) => String(r.id) === String(form.region))?.districts || [];
  const update = (field) => (event) =>
    setForm((current) => ({
      ...current,
      [field]: event.target.value,
      // Viloyat o'zgarsa eski tuman noto'g'ri bo'lib qoladi.
      ...(field === "region" ? { district: "" } : {}),
    }));

  async function save(event) {
    event.preventDefault();
    setErrors({});
    setSaving(true);
    try {
      const payload = {
        ...form,
        region: form.region || null,
        district: form.district || null,
        email: form.email || null,
      };
      const updated = await authApi.updateMe(payload);
      updateUser(updated);
      toast.success(t("common.save"));
    } catch (error) {
      const fields = fieldErrors(error);
      setErrors(fields);
      if (!Object.keys(fields).length) toast.error(error.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={save} className="surface space-y-4 p-5" noValidate>
      <h2 className="text-base font-bold">{t("nav.profile")}</h2>

      <AvatarUpload />

      <div>
        <span className="label">{t("auth.phone")}</span>
        <p className="flex items-center gap-2 text-sm font-medium">
          {formatPhone(user?.phone)}
          {user?.is_phone_verified ? (
            <span className="text-xs" style={{ color: "var(--success)" }}>
              tasdiqlangan
            </span>
          ) : null}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Field
          label={t("auth.firstName")}
          value={form.first_name}
          onChange={update("first_name")}
          error={errors.first_name}
        />
        <Field
          label={t("auth.lastName")}
          value={form.last_name}
          onChange={update("last_name")}
          error={errors.last_name}
        />
      </div>

      <Field
        label="Email"
        type="email"
        autoComplete="email"
        value={form.email}
        onChange={update("email")}
        error={errors.email}
      />

      <div className="grid gap-3 sm:grid-cols-2">
        <Field label={t("catalog.region")} error={errors.region}>
          <select className="input" value={form.region} onChange={update("region")}>
            <option value="">—</option>
            {regions.map((region) => (
              <option key={region.id} value={region.id}>
                {region.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Tuman" error={errors.district}>
          <select
            className="input"
            value={form.district}
            onChange={update("district")}
            disabled={!districts.length}
          >
            <option value="">—</option>
            {districts.map((district) => (
              <option key={district.id} value={district.id}>
                {district.name}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <button type="submit" className="btn btn-primary" disabled={saving}>
        <Save size={16} aria-hidden="true" />
        {saving ? t("common.loading") : t("common.save")}
      </button>
    </form>
  );
}

function PasswordForm() {
  const { t } = useI18n();
  const toast = useToast();
  const setSession = useAuthStore((state) => state.setSession);

  const [form, setForm] = useState({
    old_password: "",
    new_password: "",
    new_password_confirm: "",
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const update = (field) => (event) =>
    setForm((current) => ({ ...current, [field]: event.target.value }));

  async function save(event) {
    event.preventDefault();
    setErrors({});
    setSaving(true);
    try {
      const payload = await authApi.changePassword(form);
      // Parol o'zgargach barcha sessiyalar yopiladi — backend joriy
      // qurilmaga yangi token beradi.
      setSession(payload);
      setForm({ old_password: "", new_password: "", new_password_confirm: "" });
      toast.success(payload.detail);
    } catch (error) {
      const fields = fieldErrors(error);
      setErrors(fields);
      if (fields.non_field_errors) toast.error(fields.non_field_errors);
      else if (!Object.keys(fields).length) toast.error(error.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={save} className="surface mt-5 space-y-4 p-5" noValidate>
      <h2 className="flex items-center gap-2 text-base font-bold">
        <KeyRound size={17} aria-hidden="true" />
        {t("auth.password")}
      </h2>

      <Field
        label="Joriy parol"
        type="password"
        autoComplete="current-password"
        value={form.old_password}
        onChange={update("old_password")}
        error={errors.old_password}
        required
      />
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

      <button type="submit" className="btn btn-secondary" disabled={saving}>
        {saving ? t("common.loading") : t("common.save")}
      </button>
    </form>
  );
}

export default function ProfilePage() {
  const { t } = useI18n();
  const localePath = useLocalePath();
  const logout = useAuthStore((state) => state.logout);

  useHead({
    title: `${t("nav.profile")} — ${t("brand.name")}`,
    robots: "noindex, nofollow",
  });

  return (
    <div className="container-page py-6">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-xl font-bold sm:text-2xl">
          <User size={22} aria-hidden="true" />
          {t("nav.profile")}
        </h1>
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => logout()}>
          <LogOut size={15} aria-hidden="true" />
          {t("nav.logout")}
        </button>
      </div>

      <RequireAuth>
        <div className="grid gap-5 lg:grid-cols-[1fr_260px]">
          <div className="min-w-0">
            <ProfileForm />
            <PasswordForm />
          </div>

          <nav className="surface h-fit p-2">
            <Link
              to={localePath("/seller/products")}
              className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-[var(--surface-hover)]"
            >
              <Package size={16} aria-hidden="true" />
              {t("nav.myProducts")}
            </Link>
            <Link
              to={localePath("/favorites")}
              className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-[var(--surface-hover)]"
            >
              <Heart size={16} aria-hidden="true" />
              {t("nav.favorites")}
            </Link>
            <Link
              to={localePath("/notifications")}
              className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-[var(--surface-hover)]"
            >
              <Bell size={16} aria-hidden="true" />
              {t("nav.notifications")}
            </Link>
            <Link
              to={localePath("/seller/shop")}
              className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-[var(--surface-hover)]"
            >
              <Store size={16} aria-hidden="true" />
              {t("seller.shopProfile")}
            </Link>
          </nav>
        </div>
      </RequireAuth>
    </div>
  );
}
