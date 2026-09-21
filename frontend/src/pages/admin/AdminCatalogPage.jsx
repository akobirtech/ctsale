import { useState } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fieldErrors } from "../../api/client";
import { catalog as catalogApi } from "../../api/endpoints";
import AdminNav from "../../components/admin/AdminNav";
import RequireAuth from "../../components/auth/RequireAuth";
import EmptyState from "../../components/ui/EmptyState";
import Field from "../../components/ui/Field";
import Modal from "../../components/ui/Modal";
import { Skeleton } from "../../components/ui/Skeleton";
import { useToast } from "../../hooks/useToast";
import { useI18n } from "../../i18n";
import { useHead } from "../../seo/Head";

const TABS = ["categories", "brands", "attributes"];

const DATA_TYPES = ["text", "number", "boolean", "select", "multiselect"];

/**
 * Daraxtni tekis ro'yxatga yoyadi — tanlov ro'yxatlari uchun.
 *
 * `parentId` daraxt tuzilishidan olinadi: tree endpointi uni alohida
 * maydon sifatida qaytarmaydi, tahrirlash formasiga esa kerak.
 */
function flatten(nodes, depth = 0, parentId = null, result = []) {
  nodes.forEach((node) => {
    result.push({ ...node, depth, parentId });
    if (node.children?.length) flatten(node.children, depth + 1, node.id, result);
  });
  return result;
}

/** `node` berilgan kategoriyaning avlodimi? */
function isDescendant(rows, node, ancestorId) {
  if (!ancestorId) return false;
  let current = node;
  while (current?.parentId) {
    if (current.parentId === ancestorId) return true;
    current = rows.find((row) => row.id === current.parentId);
  }
  return false;
}

function Row({ title, subtitle, badge, onEdit, onDelete }) {
  const { t } = useI18n();
  return (
    <div className="flex items-center gap-3 border-t px-3 py-2.5 first:border-t-0">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{title}</p>
        {subtitle ? (
          <p className="truncate text-xs" style={{ color: "var(--text-subtle)" }}>
            {subtitle}
          </p>
        ) : null}
      </div>
      {badge ? (
        <span className="shrink-0 text-xs" style={{ color: "var(--text-subtle)" }}>
          {badge}
        </span>
      ) : null}
      <div className="flex shrink-0 gap-1">
        <button type="button" className="btn btn-ghost btn-sm" onClick={onEdit} title={t("seller.edit")}>
          <Pencil size={15} />
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          style={{ color: "var(--danger)" }}
          onClick={onDelete}
          title={t("seller.delete")}
        >
          <Trash2 size={15} />
        </button>
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------

function CategoriesTab() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [editing, setEditing] = useState(null);
  const [errors, setErrors] = useState({});

  const { data: tree = [], isLoading } = useQuery({
    queryKey: ["catalog-tree-admin"],
    queryFn: () => catalogApi.tree("uz"),
  });

  const rows = flatten(tree);

  const save = useMutation({
    mutationFn: (values) =>
      values.id ? catalogApi.updateCategory(values.id, values) : catalogApi.createCategory(values),
    onSuccess: () => {
      toast.success(t("common.save"));
      setEditing(null);
      setErrors({});
      queryClient.invalidateQueries({ queryKey: ["catalog-tree-admin"] });
    },
    onError: (error) => {
      const fields = fieldErrors(error);
      setErrors(fields);
      if (!Object.keys(fields).length) toast.error(error.message);
    },
  });

  const remove = useMutation({
    mutationFn: (id) => catalogApi.deleteCategory(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["catalog-tree-admin"] }),
    onError: (error) => toast.error(error.message),
  });

  if (isLoading) return <Skeleton className="h-64" />;

  return (
    <>
      <div className="mb-3 flex justify-end">
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={() => setEditing({ name_uz: "", name_ru: "", name_en: "", parent: "", is_active: true })}
        >
          <Plus size={15} />
          {t("admin.add")}
        </button>
      </div>

      <div className="surface">
        {rows.map((category) => (
          <Row
            key={category.id}
            title={"— ".repeat(category.depth) + category.name}
            subtitle={category.slug}
            badge={`${category.products_count}`}
            onEdit={() =>
              setEditing({
                id: category.id,
                name_uz: category.names?.uz || "",
                name_ru: category.names?.ru || "",
                name_en: category.names?.en || "",
                parent: category.parentId ?? "",
                is_featured: category.is_featured,
                order: category.order,
              })
            }
            onDelete={() => {
              if (window.confirm(t("admin.confirmDelete"))) remove.mutate(category.id);
            }}
          />
        ))}
      </div>

      <Modal
        open={Boolean(editing)}
        onClose={() => setEditing(null)}
        title={editing?.id ? t("seller.edit") : t("admin.add")}
        footer={
          <>
            <button type="button" className="btn btn-secondary flex-1" onClick={() => setEditing(null)}>
              {t("common.cancel")}
            </button>
            <button
              type="submit"
              form="category-form"
              className="btn btn-primary flex-1"
              disabled={save.isPending}
            >
              {t("common.save")}
            </button>
          </>
        }
      >
        {editing ? (
          <form
            id="category-form"
            className="space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              save.mutate({ ...editing, parent: editing.parent || null });
            }}
          >
            <Field
              label="Nomi (uz)"
              required
              value={editing.name_uz}
              onChange={(event) => setEditing({ ...editing, name_uz: event.target.value })}
              error={errors.name_uz}
            />
            <div className="grid gap-3 sm:grid-cols-2">
              <Field
                label="Nomi (ru)"
                value={editing.name_ru}
                onChange={(event) => setEditing({ ...editing, name_ru: event.target.value })}
              />
              <Field
                label="Nomi (en)"
                value={editing.name_en}
                onChange={(event) => setEditing({ ...editing, name_en: event.target.value })}
              />
            </div>

            <Field label={t("admin.parent")} error={errors.parent}>
              <select
                className="input"
                value={editing.parent ?? ""}
                onChange={(event) => setEditing({ ...editing, parent: event.target.value })}
              >
                <option value="">{t("admin.topLevel")}</option>
                {rows
                  // O'zini yoki o'z avlodini ota qilib tanlash halqa
                  // yasaydi — backend ham buni rad etadi.
                  .filter((row) => row.id !== editing.id && !isDescendant(rows, row, editing.id))
                  .map((row) => (
                    <option key={row.id} value={row.id}>
                      {"— ".repeat(row.depth) + row.name}
                    </option>
                  ))}
              </select>
            </Field>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={Boolean(editing.is_featured)}
                onChange={(event) => setEditing({ ...editing, is_featured: event.target.checked })}
              />
              {t("admin.popular")}
            </label>
          </form>
        ) : null}
      </Modal>
    </>
  );
}

// --------------------------------------------------------------------------

function BrandsTab() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [editing, setEditing] = useState(null);
  const [errors, setErrors] = useState({});

  const { data, isLoading } = useQuery({
    queryKey: ["admin-brands"],
    queryFn: () => catalogApi.brands({ page_size: 100 }),
  });

  const brands = data?.results || data || [];

  const save = useMutation({
    mutationFn: (values) =>
      values.id ? catalogApi.updateBrand(values.id, values) : catalogApi.createBrand(values),
    onSuccess: () => {
      toast.success(t("common.save"));
      setEditing(null);
      setErrors({});
      queryClient.invalidateQueries({ queryKey: ["admin-brands"] });
    },
    onError: (error) => {
      const fields = fieldErrors(error);
      setErrors(fields);
      if (!Object.keys(fields).length) toast.error(error.message);
    },
  });

  const remove = useMutation({
    mutationFn: (id) => catalogApi.deleteBrand(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-brands"] }),
    onError: (error) => toast.error(error.message),
  });

  if (isLoading) return <Skeleton className="h-64" />;

  return (
    <>
      <div className="mb-3 flex justify-end">
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={() => setEditing({ name: "", website: "", is_popular: false })}
        >
          <Plus size={15} />
          {t("admin.add")}
        </button>
      </div>

      <div className="surface">
        {brands.length === 0 ? (
          <EmptyState title={t("admin.brands")} />
        ) : (
          brands.map((brand) => (
            <Row
              key={brand.id}
              title={brand.name}
              subtitle={brand.website}
              badge={`${brand.products_count ?? 0}`}
              onEdit={() => setEditing({ ...brand })}
              onDelete={() => {
                if (window.confirm(t("admin.confirmDelete"))) remove.mutate(brand.id);
              }}
            />
          ))
        )}
      </div>

      <Modal
        open={Boolean(editing)}
        onClose={() => setEditing(null)}
        title={editing?.id ? t("seller.edit") : t("admin.add")}
        footer={
          <>
            <button type="button" className="btn btn-secondary flex-1" onClick={() => setEditing(null)}>
              {t("common.cancel")}
            </button>
            <button
              type="submit"
              form="brand-form"
              className="btn btn-primary flex-1"
              disabled={save.isPending}
            >
              {t("common.save")}
            </button>
          </>
        }
      >
        {editing ? (
          <form
            id="brand-form"
            className="space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              save.mutate(editing);
            }}
          >
            <Field
              label={t("catalog.brand")}
              required
              value={editing.name}
              onChange={(event) => setEditing({ ...editing, name: event.target.value })}
              error={errors.name}
            />
            <Field
              label="Website"
              type="url"
              placeholder="https://"
              value={editing.website || ""}
              onChange={(event) => setEditing({ ...editing, website: event.target.value })}
              error={errors.website}
            />
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={Boolean(editing.is_popular)}
                onChange={(event) => setEditing({ ...editing, is_popular: event.target.checked })}
              />
              {t("admin.popular")}
            </label>
          </form>
        ) : null}
      </Modal>
    </>
  );
}

// --------------------------------------------------------------------------

function AttributesTab() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [categoryId, setCategoryId] = useState("");
  const [editing, setEditing] = useState(null);
  const [errors, setErrors] = useState({});

  const { data: tree = [] } = useQuery({
    queryKey: ["catalog-tree-admin"],
    queryFn: () => catalogApi.tree("uz"),
  });
  const categories = flatten(tree);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-attributes", categoryId],
    queryFn: () => catalogApi.attributeList({ category: categoryId, page_size: 100 }),
    enabled: Boolean(categoryId),
  });

  const attributes = data?.results || data || [];

  const save = useMutation({
    mutationFn: (values) =>
      values.id ? catalogApi.updateAttribute(values.id, values) : catalogApi.createAttribute(values),
    onSuccess: () => {
      toast.success(t("common.save"));
      setEditing(null);
      setErrors({});
      queryClient.invalidateQueries({ queryKey: ["admin-attributes"] });
    },
    onError: (error) => {
      const fields = fieldErrors(error);
      setErrors(fields);
      if (!Object.keys(fields).length) toast.error(error.message);
    },
  });

  const remove = useMutation({
    mutationFn: (id) => catalogApi.deleteAttribute(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-attributes"] }),
    onError: (error) => toast.error(error.message),
  });

  return (
    <>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <select
          className="input h-9 w-auto min-w-56"
          value={categoryId}
          onChange={(event) => setCategoryId(event.target.value)}
        >
          <option value="">{t("admin.noCategory")}</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {"— ".repeat(category.depth) + category.name}
            </option>
          ))}
        </select>

        <button
          type="button"
          className="btn btn-primary btn-sm ml-auto"
          disabled={!categoryId}
          onClick={() =>
            setEditing({
              category: categoryId,
              code: "",
              label_uz: "",
              data_type: "text",
              is_required: false,
              is_filterable: true,
              is_in_card: false,
            })
          }
        >
          <Plus size={15} />
          {t("admin.add")}
        </button>
      </div>

      {!categoryId ? (
        <EmptyState title={t("admin.noCategory")} description={t("admin.pickCategoryHint")} />
      ) : isLoading ? (
        <Skeleton className="h-64" />
      ) : attributes.length === 0 ? (
        <EmptyState title={t("admin.noAttributes")} description={t("admin.noAttributesHint")} />
      ) : (
        <div className="surface">
          {attributes.map((attribute) => (
            <Row
              key={attribute.id}
              title={attribute.label || attribute.label_uz}
              subtitle={`${attribute.code} · ${attribute.data_type}`}
              badge={attribute.is_required ? t("admin.required") : ""}
              onEdit={() => setEditing({ ...attribute, category: attribute.category || categoryId })}
              onDelete={() => {
                if (window.confirm(t("admin.confirmDelete"))) remove.mutate(attribute.id);
              }}
            />
          ))}
        </div>
      )}

      <Modal
        open={Boolean(editing)}
        onClose={() => setEditing(null)}
        title={editing?.id ? t("seller.edit") : t("admin.add")}
        footer={
          <>
            <button type="button" className="btn btn-secondary flex-1" onClick={() => setEditing(null)}>
              {t("common.cancel")}
            </button>
            <button
              type="submit"
              form="attribute-form"
              className="btn btn-primary flex-1"
              disabled={save.isPending}
            >
              {t("common.save")}
            </button>
          </>
        }
      >
        {editing ? (
          <form
            id="attribute-form"
            className="space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              save.mutate(editing);
            }}
          >
            <Field
              label="Nomi (uz)"
              required
              value={editing.label_uz || ""}
              onChange={(event) => setEditing({ ...editing, label_uz: event.target.value })}
              error={errors.label_uz}
            />

            <Field
              label={t("admin.code")}
              required
              // Kod specs JSONB kaliti — yaratilgandan keyin backend uni
              // o'zgartirishga ruxsat bermaydi.
              disabled={Boolean(editing.id)}
              value={editing.code || ""}
              onChange={(event) => setEditing({ ...editing, code: event.target.value })}
              error={errors.code}
              hint={editing.id ? t("admin.codeLocked") : undefined}
            />

            <Field label={t("admin.dataType")} error={errors.data_type}>
              <select
                className="input"
                value={editing.data_type}
                disabled={Boolean(editing.id)}
                onChange={(event) => setEditing({ ...editing, data_type: event.target.value })}
              >
                {DATA_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </Field>

            <div className="space-y-2">
              {[
                ["is_required", t("admin.required")],
                ["is_filterable", t("admin.filterable")],
                ["is_in_card", t("admin.inCard")],
              ].map(([key, label]) => (
                <label key={key} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={Boolean(editing[key])}
                    onChange={(event) => setEditing({ ...editing, [key]: event.target.checked })}
                  />
                  {label}
                </label>
              ))}
            </div>
          </form>
        ) : null}
      </Modal>
    </>
  );
}

// --------------------------------------------------------------------------

export default function AdminCatalogPage() {
  const { t } = useI18n();
  const [tab, setTab] = useState("categories");

  useHead({ title: `${t("admin.catalog")} — ${t("nav.admin")}`, robots: "noindex, nofollow" });

  return (
    <div className="container-page py-6">
      <h1 className="mb-4 text-xl font-bold sm:text-2xl">{t("admin.catalog")}</h1>
      <AdminNav />

      <RequireAuth>
        <div className="mb-4 flex gap-1">
          {TABS.map((name) => (
            <button
              key={name}
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setTab(name)}
              style={
                name === tab
                  ? { background: "var(--accent)", color: "var(--accent-text)", borderColor: "transparent" }
                  : undefined
              }
            >
              {t(`admin.${name}`)}
            </button>
          ))}
        </div>

        {tab === "categories" ? <CategoriesTab /> : null}
        {tab === "brands" ? <BrandsTab /> : null}
        {tab === "attributes" ? <AttributesTab /> : null}
      </RequireAuth>
    </div>
  );
}
