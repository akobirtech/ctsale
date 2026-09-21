import { useEffect, useRef, useState } from "react";
import { Camera, Save, Store, Trash2 } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { fieldErrors } from "../../api/client";
import { auth as authApi } from "../../api/endpoints";
import RequireAuth from "../../components/auth/RequireAuth";
import Field from "../../components/ui/Field";
import PageLoader from "../../components/ui/PageLoader";
import { useToast } from "../../hooks/useToast";
import { useI18n } from "../../i18n";
import { useHead } from "../../seo/Head";

const EMPTY = {
  name: "",
  description: "",
  address: "",
  working_hours: "",
  website: "",
  telegram_url: "",
  instagram_url: "",
};

function ShopForm() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();

  const logoInput = useRef(null);
  const [form, setForm] = useState(EMPTY);
  const [logo, setLogo] = useState(null);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  useHead({ title: t("seller.shopProfile"), robots: "noindex, nofollow" });

  const { data: shop, isLoading } = useQuery({
    queryKey: ["shop-profile"],
    // Profil yo'qligi xato emas — shunchaki hali yaratilmagan.
    queryFn: () => authApi.shop().catch(() => null),
    retry: false,
  });

  useEffect(() => {
    if (shop) setForm({ ...EMPTY, ...shop });
  }, [shop]);

  const update = (field) => (event) =>
    setForm((current) => ({ ...current, [field]: event.target.value }));

  async function save(event) {
    event.preventDefault();
    setErrors({});
    setSaving(true);
    try {
      let payload = form;
      if (logo) {
        // Logo bor bo'lsa multipart kerak.
        payload = new FormData();
        Object.entries(form).forEach(([key, value]) => payload.append(key, value ?? ""));
        payload.append("logo", logo);
      }
      await authApi.saveShop(payload);
      setLogo(null);
      toast.success(t("common.save"));
      queryClient.invalidateQueries({ queryKey: ["shop-profile"] });
      queryClient.invalidateQueries({ queryKey: ["me"] });
    } catch (error) {
      const fields = fieldErrors(error);
      setErrors(fields);
      if (!Object.keys(fields).length) toast.error(error.message);
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    setSaving(true);
    try {
      await authApi.deleteShop();
      setForm(EMPTY);
      queryClient.invalidateQueries({ queryKey: ["shop-profile"] });
      toast.success(t("seller.shopRemoved"));
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSaving(false);
    }
  }

  if (isLoading) return <PageLoader />;

  const logoPreview = logo ? URL.createObjectURL(logo) : shop?.logo;

  return (
    <form onSubmit={save} className="surface space-y-4 p-5" noValidate>
      <div>
        <h1 className="text-lg font-bold">{t("seller.shopProfile")}</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
          {t("seller.shopHint")}
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div
          className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl"
          style={{ background: "var(--accent-soft)", color: "var(--accent)" }}
        >
          {logoPreview ? (
            <img src={logoPreview} alt="" className="h-full w-full object-cover" />
          ) : (
            <Store size={24} aria-hidden="true" />
          )}
        </div>
        <div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => logoInput.current?.click()}
          >
            <Camera size={15} aria-hidden="true" />
            {t("seller.shopLogo")}
          </button>
          {errors.logo ? (
            <p className="mt-1 text-xs font-medium" style={{ color: "var(--danger)" }}>
              {errors.logo}
            </p>
          ) : null}
        </div>
        <input
          ref={logoInput}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(event) => setLogo(event.target.files?.[0] || null)}
        />
      </div>

      <Field
        label={t("seller.shopName")}
        required
        value={form.name}
        onChange={update("name")}
        error={errors.name}
        maxLength={120}
      />

      <Field label={t("product.description")} error={errors.description}>
        <textarea
          className="input min-h-24"
          rows={4}
          value={form.description}
          onChange={update("description")}
        />
      </Field>

      <div className="grid gap-3 sm:grid-cols-2">
        <Field
          label={t("product.location")}
          value={form.address}
          onChange={update("address")}
          error={errors.address}
        />
        <Field
          label={t("seller.workingHours")}
          placeholder="Du-Sha 09:00-18:00"
          value={form.working_hours}
          onChange={update("working_hours")}
          error={errors.working_hours}
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Field
          label="Website"
          type="url"
          placeholder="https://"
          value={form.website}
          onChange={update("website")}
          error={errors.website}
        />
        <Field
          label="Telegram"
          type="url"
          placeholder="https://t.me/"
          value={form.telegram_url}
          onChange={update("telegram_url")}
          error={errors.telegram_url}
        />
        <Field
          label="Instagram"
          type="url"
          placeholder="https://instagram.com/"
          value={form.instagram_url}
          onChange={update("instagram_url")}
          error={errors.instagram_url}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          <Save size={16} aria-hidden="true" />
          {saving ? t("common.loading") : t("common.save")}
        </button>

        {shop ? (
          <button
            type="button"
            className="btn btn-ghost"
            onClick={remove}
            disabled={saving}
            style={{ color: "var(--danger)" }}
          >
            <Trash2 size={16} aria-hidden="true" />
            {t("seller.shopRemove")}
          </button>
        ) : null}
      </div>
    </form>
  );
}

export default function ShopProfilePage() {
  return (
    <div className="container-page max-w-2xl py-6">
      <RequireAuth>
        <ShopForm />
      </RequireAuth>
    </div>
  );
}
