import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Check, Save, Send } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { fieldErrors } from "../../api/client";
import { catalog as catalogApi, products as productsApi } from "../../api/endpoints";
import RequireAuth from "../../components/auth/RequireAuth";
import MediaUploader from "../../components/seller/MediaUploader";
import SpecFields from "../../components/seller/SpecFields";
import Field from "../../components/ui/Field";
import { useToast } from "../../hooks/useToast";
import { useI18n, useLocalePath } from "../../i18n";
import { useHead } from "../../seo/Head";

const STEPS = ["Kategoriya", "Asosiy ma'lumot", "Xususiyatlar", "Rasm va manzil"];
const CONDITIONS = ["new", "like_new", "good", "fair", "for_parts"];

const EMPTY_FORM = {
  category: "",
  title: "",
  description: "",
  brand: "",
  model_name: "",
  condition: "",
  price: "",
  currency: "UZS",
  is_negotiable: false,
  price_on_request: false,
  is_exchange_possible: false,
  quantity: 1,
  usage_period: "",
  has_warranty: false,
  warranty_until: "",
  has_original_box: false,
  accessories: "",
  defects: "",
  region: "",
  district: "",
  address_note: "",
  contact_name: "",
  specs: {},
};

/** Faqat "barg" kategoriyalar — e'lon aniq bo'limga tushsin. */
function flattenLeaves(nodes, depth = 0, acc = []) {
  for (const node of nodes) {
    const children = node.children || [];
    if (children.length === 0) {
      acc.push({ ...node, depth });
    } else {
      acc.push({ ...node, depth, isParent: true });
      flattenLeaves(children, depth + 1, acc);
    }
  }
  return acc;
}

function ProductFormContent() {
  const { t, lang } = useI18n();
  const localePath = useLocalePath();
  const navigate = useNavigate();
  const toast = useToast();
  const { slug: editSlug } = useParams();
  const isEdit = Boolean(editSlug);

  const [step, setStep] = useState(isEdit ? 1 : 0);
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [savedSlug, setSavedSlug] = useState(editSlug || null);
  const [media, setMedia] = useState({ images: [], videos: [] });

  // --- Ma'lumotnomalar ---
  const { data: categoryTree = [] } = useQuery({
    queryKey: ["categories", lang],
    queryFn: () => catalogApi.tree(lang),
    staleTime: 10 * 60_000,
  });
  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: () => catalogApi.brands(),
    staleTime: 30 * 60_000,
  });
  const { data: regions = [] } = useQuery({
    queryKey: ["regions-with-districts"],
    queryFn: () => catalogApi.regions(true),
    staleTime: 30 * 60_000,
  });

  const categories = useMemo(() => flattenLeaves(categoryTree), [categoryTree]);
  const selectedCategory = categories.find((c) => String(c.id) === String(form.category));

  const { data: attributes = [] } = useQuery({
    queryKey: ["attributes", selectedCategory?.slug, lang],
    queryFn: () => catalogApi.attributes(selectedCategory.slug, lang),
    enabled: Boolean(selectedCategory?.slug),
  });

  // --- Tahrirlash rejimida mavjud e'lonni yuklaymiz ---
  const { data: existing } = useQuery({
    queryKey: ["product-edit", editSlug, lang],
    queryFn: () => productsApi.detail(editSlug, lang),
    enabled: isEdit,
  });

  useEffect(() => {
    if (!existing) return;
    setForm({
      ...EMPTY_FORM,
      ...Object.fromEntries(
        Object.keys(EMPTY_FORM).map((key) => [key, existing[key] ?? EMPTY_FORM[key]])
      ),
      category: existing.category ?? "",
      brand: existing.brand ?? "",
      region: existing.region ?? "",
      district: existing.district ?? "",
      price: existing.price ?? "",
      specs: existing.specs || {},
    });
    setMedia({ images: existing.images || [], videos: existing.videos || [] });
    setSavedSlug(existing.slug);
  }, [existing]);

  useHead({
    title: `${isEdit ? t("seller.edit") : t("seller.newProduct")} — ${t("brand.name")}`,
    robots: "noindex, nofollow",
  });

  const districts =
    regions.find((r) => String(r.id) === String(form.region))?.districts || [];

  const update = (field) => (event) => {
    const value =
      event?.target?.type === "checkbox" ? event.target.checked : event?.target?.value ?? event;
    setForm((current) => ({
      ...current,
      [field]: value,
      ...(field === "region" ? { district: "" } : {}),
      // Kategoriya o'zgarsa eski xususiyatlar yangi sxemaga mos kelmaydi.
      ...(field === "category" ? { specs: {} } : {}),
    }));
  };

  /** Serverga yuborish uchun formani tozalaydi. */
  function buildPayload() {
    return {
      ...form,
      category: form.category || null,
      brand: form.brand || null,
      region: form.region || null,
      district: form.district || null,
      price: form.price === "" ? null : Number(form.price),
      quantity: Number(form.quantity) || 1,
      warranty_until: form.warranty_until || null,
    };
  }

  async function save({ thenSubmit = false, silent = false } = {}) {
    setErrors({});
    setSaving(true);
    try {
      const payload = buildPayload();
      const result = savedSlug
        ? await productsApi.update(savedSlug, payload)
        : await productsApi.create(payload);

      setSavedSlug(result.slug);
      if (result.images) setMedia({ images: result.images, videos: result.videos || [] });

      if (thenSubmit) {
        await productsApi.submit(result.slug);
        toast.success("E'lon moderatsiyaga yuborildi. Tasdiqlangach saytda va Telegram kanalda chiqadi.");
        navigate(localePath("/seller/products"));
        return result;
      }

      if (!silent) toast.success(t("common.save"));
      return result;
    } catch (error) {
      const fields = fieldErrors(error);
      setErrors(fields);
      // Xususiyat xatolari 3-qadamda — foydalanuvchini o'sha yerga qaytaramiz.
      if (error.code === "invalid_specs") {
        setStep(2);
        toast.error(error.message);
      } else if (error.code === "images_required") {
        setStep(3);
        toast.error(error.message);
      } else {
        toast.error(error.message);
      }
      throw error;
    } finally {
      setSaving(false);
    }
  }

  async function goNext() {
    // 2-qadamdan 3-qadamga o'tishda e'lonni saqlaymiz: rasm yuklash
    // uchun mahsulot bazada mavjud bo'lishi kerak.
    if (step === 2 && !savedSlug) {
      try {
        await save({ silent: true });
      } catch {
        return;
      }
    }
    setStep((current) => Math.min(current + 1, STEPS.length - 1));
  }

  const canGoNext =
    (step === 0 && form.category) ||
    (step === 1 && form.title.length >= 10 && form.description.length >= 20 && form.condition) ||
    step === 2 ||
    step === 3;

  return (
    <>
      {/* Qadamlar */}
      <ol className="mb-6 flex gap-1.5" aria-label="Qadamlar">
        {STEPS.map((label, index) => (
          <li key={label} className="flex-1">
            <button
              type="button"
              onClick={() => index < step && setStep(index)}
              disabled={index > step}
              className="w-full text-left"
            >
              <div
                className="h-1 rounded-full"
                style={{
                  background: index <= step ? "var(--accent)" : "var(--border)",
                }}
              />
              <span
                className="mt-1.5 block text-[11px] font-medium sm:text-xs"
                style={{ color: index <= step ? "var(--accent)" : "var(--text-subtle)" }}
              >
                {index + 1}. {label}
              </span>
            </button>
          </li>
        ))}
      </ol>

      <div className="surface p-5 sm:p-6">
        {/* 1. Kategoriya */}
        {step === 0 ? (
          <div>
            <h2 className="mb-4 text-base font-bold">Kategoriyani tanlang</h2>
            <div className="max-h-[50vh] space-y-0.5 overflow-y-auto">
              {categories.map((category) =>
                category.isParent ? (
                  <p
                    key={category.id}
                    className="px-2 pt-3 text-xs font-bold uppercase tracking-wide"
                    style={{
                      color: "var(--text-subtle)",
                      paddingLeft: `${category.depth * 12 + 8}px`,
                    }}
                  >
                    {category.name}
                  </p>
                ) : (
                  <button
                    key={category.id}
                    type="button"
                    onClick={() => {
                      update("category")({ target: { value: category.id } });
                      setStep(1);
                    }}
                    className="flex w-full items-center justify-between rounded-lg px-2 py-2 text-left text-sm hover:bg-[var(--surface-hover)]"
                    style={{
                      paddingLeft: `${category.depth * 12 + 8}px`,
                      color:
                        String(form.category) === String(category.id)
                          ? "var(--accent)"
                          : "var(--text)",
                      fontWeight: String(form.category) === String(category.id) ? 600 : 400,
                    }}
                  >
                    {category.name}
                    <span className="text-xs" style={{ color: "var(--text-subtle)" }}>
                      {category.products_count}
                    </span>
                  </button>
                )
              )}
            </div>
          </div>
        ) : null}

        {/* 2. Asosiy ma'lumot */}
        {step === 1 ? (
          <div className="space-y-4">
            <h2 className="text-base font-bold">{STEPS[1]}</h2>

            <Field
              label="Sarlavha"
              value={form.title}
              onChange={update("title")}
              error={errors.title}
              hint="Kamida 10 ta belgi. Brend va modelni yozing — shunda topilishi oson bo'ladi."
              maxLength={200}
              required
            />

            <Field label="Tavsif" error={errors.description} required>
              <textarea
                className="input min-h-32 py-2.5"
                value={form.description}
                onChange={update("description")}
                maxLength={5000}
                placeholder="Holati, komplektatsiyasi, nima uchun sotayotganingiz..."
                aria-invalid={errors.description ? "true" : undefined}
              />
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={t("catalog.brand")} error={errors.brand}>
                <select className="input" value={form.brand} onChange={update("brand")}>
                  <option value="">—</option>
                  {brands.map((brand) => (
                    <option key={brand.id} value={brand.id}>
                      {brand.name}
                    </option>
                  ))}
                </select>
              </Field>

              <Field
                label="Model"
                value={form.model_name}
                onChange={update("model_name")}
                error={errors.model_name}
                placeholder="Masalan: ROG Strix G16"
              />
            </div>

            <Field label={t("product.condition")} error={errors.condition} required>
              <div className="flex flex-wrap gap-1.5">
                {CONDITIONS.map((condition) => (
                  <button
                    key={condition}
                    type="button"
                    className="btn btn-sm"
                    style={
                      form.condition === condition
                        ? { background: "var(--accent)", color: "var(--accent-text)" }
                        : { background: "var(--bg-muted)", color: "var(--text-muted)" }
                    }
                    aria-pressed={form.condition === condition}
                    onClick={() => update("condition")({ target: { value: condition } })}
                  >
                    {t(`condition.${condition}`)}
                  </button>
                ))}
              </div>
            </Field>

            <div className="grid gap-4 sm:grid-cols-[1fr_auto]">
              <Field
                label={t("catalog.price")}
                type="number"
                inputMode="numeric"
                value={form.price}
                onChange={update("price")}
                error={errors.price}
                disabled={form.price_on_request}
                placeholder="12500000"
              />
              <Field label={t("common.currency")}>
                <select className="input" value={form.currency} onChange={update("currency")}>
                  <option value="UZS">so&apos;m</option>
                  <option value="USD">USD</option>
                </select>
              </Field>
            </div>

            <div className="flex flex-wrap gap-4 text-sm">
              {[
                ["is_negotiable", t("catalog.negotiable")],
                ["price_on_request", t("product.onRequest")],
                ["is_exchange_possible", t("product.exchangePossible")],
              ].map(([key, label]) => (
                <label key={key} className="flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-[var(--accent)]"
                    checked={form[key]}
                    onChange={update(key)}
                  />
                  {label}
                </label>
              ))}
            </div>

            {/* Ishlatilgan mahsulot uchun qo'shimcha maydonlar */}
            {form.condition && form.condition !== "new" ? (
              <div className="grid gap-4 border-t pt-4 sm:grid-cols-2">
                <Field
                  label={t("product.usagePeriod")}
                  value={form.usage_period}
                  onChange={update("usage_period")}
                  error={errors.usage_period}
                  placeholder="Masalan: 8 oy"
                />
                <Field
                  label={t("product.accessories")}
                  value={form.accessories}
                  onChange={update("accessories")}
                  error={errors.accessories}
                  placeholder="Zaryadlovchi, sumka..."
                />
                <div className="sm:col-span-2">
                  <Field label={t("product.defects")} error={errors.defects}>
                    <textarea
                      className="input min-h-20 py-2.5"
                      value={form.defects}
                      onChange={update("defects")}
                      maxLength={1000}
                      placeholder="Bor kamchiliklarni yozing — bu ishonch qozonadi"
                    />
                  </Field>
                </div>
              </div>
            ) : null}

            <div className="flex flex-wrap items-end gap-4 border-t pt-4">
              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-[var(--accent)]"
                  checked={form.has_warranty}
                  onChange={update("has_warranty")}
                />
                {t("catalog.warranty")}
              </label>

              {form.has_warranty ? (
                <Field
                  label={t("product.warrantyUntil")}
                  type="date"
                  value={form.warranty_until}
                  onChange={update("warranty_until")}
                  error={errors.warranty_until}
                  required
                />
              ) : null}

              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-[var(--accent)]"
                  checked={form.has_original_box}
                  onChange={update("has_original_box")}
                />
                {t("product.originalBox")}
              </label>
            </div>
          </div>
        ) : null}

        {/* 3. Xususiyatlar */}
        {step === 2 ? (
          <div>
            <h2 className="mb-1 text-base font-bold">{STEPS[2]}</h2>
            <p className="mb-4 text-sm" style={{ color: "var(--text-muted)" }}>
              {selectedCategory?.name} uchun xususiyatlar. To&apos;ldirilganlari filtrlarda
              ishlaydi va xaridor tezroq topadi.
            </p>
            <SpecFields
              attributes={attributes}
              values={form.specs}
              errors={errors}
              onChange={(specs) => setForm((current) => ({ ...current, specs }))}
            />
          </div>
        ) : null}

        {/* 4. Rasm va manzil */}
        {step === 3 ? (
          <div className="space-y-5">
            <div>
              <h2 className="mb-1 text-base font-bold">{t("seller.uploadImages")}</h2>
              <p className="mb-4 text-sm" style={{ color: "var(--text-muted)" }}>
                Kamida bitta rasm kerak. Birinchi rasm asosiy bo&apos;ladi va Telegram
                kanalda ham o&apos;sha ko&apos;rinadi.
              </p>
              {savedSlug ? (
                <MediaUploader
                  slug={savedSlug}
                  images={media.images}
                  videos={media.videos}
                  onChange={setMedia}
                />
              ) : (
                <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
                  Avval e&apos;lonni saqlang.
                </p>
              )}
            </div>

            <div className="grid gap-4 border-t pt-5 sm:grid-cols-2">
              <Field label={t("catalog.region")} error={errors.region} required>
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

              <Field
                label="Manzil izohi"
                value={form.address_note}
                onChange={update("address_note")}
                error={errors.address_note}
                placeholder="Masalan: Chilonzor, Bunyodkor metrosi yonida"
              />

              <Field
                label="Aloqa uchun ism"
                value={form.contact_name}
                onChange={update("contact_name")}
                error={errors.contact_name}
                placeholder="Bo'sh qoldirilsa profildagi ism ishlatiladi"
              />
            </div>
          </div>
        ) : null}
      </div>

      {/* Navigatsiya */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-2">
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => setStep((current) => Math.max(0, current - 1))}
          disabled={step === 0}
        >
          <ArrowLeft size={16} aria-hidden="true" />
          {t("seller.back")}
        </button>

        <div className="flex flex-wrap gap-2">
          {step > 0 ? (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => save()}
              disabled={saving}
            >
              <Save size={16} aria-hidden="true" />
              {t("seller.saveDraft")}
            </button>
          ) : null}

          {step < STEPS.length - 1 ? (
            <button
              type="button"
              className="btn btn-primary"
              onClick={goNext}
              disabled={!canGoNext || saving}
            >
              {t("seller.next")}
              <ArrowRight size={16} aria-hidden="true" />
            </button>
          ) : (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => save({ thenSubmit: true }).catch(() => {})}
              disabled={saving || media.images.length === 0}
            >
              <Send size={16} aria-hidden="true" />
              {saving ? t("common.loading") : t("seller.submit")}
            </button>
          )}
        </div>
      </div>

      {savedSlug ? (
        <p className="mt-3 flex items-center gap-1.5 text-xs" style={{ color: "var(--success)" }}>
          <Check size={13} aria-hidden="true" />
          Qoralama saqlandi —{" "}
          <Link to={localePath("/seller/products")} className="underline">
            {t("seller.myProducts")}
          </Link>
        </p>
      ) : null}
    </>
  );
}

export default function ProductFormPage() {
  const { t } = useI18n();
  const { slug } = useParams();

  return (
    <div className="container-page max-w-3xl py-6">
      <h1 className="mb-5 text-xl font-bold sm:text-2xl">
        {slug ? t("seller.edit") : t("seller.newProduct")}
      </h1>
      <RequireAuth>
        <ProductFormContent />
      </RequireAuth>
    </div>
  );
}
