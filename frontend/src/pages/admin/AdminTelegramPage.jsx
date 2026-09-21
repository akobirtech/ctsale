import { useEffect, useState } from "react";
import { ExternalLink, RefreshCw, Save, Send } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fieldErrors } from "../../api/client";
import { admin as adminApi } from "../../api/endpoints";
import AdminNav from "../../components/admin/AdminNav";
import RequireAuth from "../../components/auth/RequireAuth";
import EmptyState from "../../components/ui/EmptyState";
import Field from "../../components/ui/Field";
import { Skeleton } from "../../components/ui/Skeleton";
import { useToast } from "../../hooks/useToast";
import { useI18n } from "../../i18n";
import { useHead } from "../../seo/Head";
import { formatRelativeDate } from "../../utils/format";

const STATUS_TONES = {
  published: "var(--success)",
  failed: "var(--danger)",
  pending: "var(--warning)",
  deleted: "var(--text-subtle)",
};

function SettingsForm() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [form, setForm] = useState(null);
  const [errors, setErrors] = useState({});

  const { data, isLoading } = useQuery({
    queryKey: ["telegram-settings"],
    queryFn: () => adminApi.telegramSettings(),
  });

  useEffect(() => {
    if (data) setForm(data);
  }, [data]);

  const save = useMutation({
    mutationFn: (values) => adminApi.updateTelegramSettings(values),
    onSuccess: () => {
      toast.success(t("common.save"));
      setErrors({});
      queryClient.invalidateQueries({ queryKey: ["telegram-settings"] });
    },
    onError: (error) => {
      const fields = fieldErrors(error);
      setErrors(fields);
      if (!Object.keys(fields).length) toast.error(error.message);
    },
  });

  if (isLoading || !form) return <Skeleton className="h-64" />;

  const update = (field) => (event) =>
    setForm({
      ...form,
      [field]: event.target.type === "checkbox" ? event.target.checked : event.target.value,
    });

  return (
    <form
      className="surface space-y-4 p-5"
      onSubmit={(event) => {
        event.preventDefault();
        save.mutate(form);
      }}
    >
      <h2 className="text-base font-bold">{t("admin.telegramSettings")}</h2>

      {/* Bot tokeni ataylab yo'q: u faqat .env da yashaydi va
          hech qachon API javobiga chiqmaydi. */}
      <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
        {t("admin.telegramTokenNote")}
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        <Field
          label={t("admin.channelId")}
          value={form.channel_id || ""}
          onChange={update("channel_id")}
          error={errors.channel_id}
          placeholder="@kanal yoki -100..."
        />
        <Field
          label={t("admin.channelUrl")}
          type="url"
          value={form.channel_url || ""}
          onChange={update("channel_url")}
          error={errors.channel_url}
        />
      </div>

      <Field label={t("admin.postTemplate")} error={errors.post_template}>
        <textarea
          className="input min-h-40 font-mono text-xs"
          rows={10}
          value={form.post_template || ""}
          onChange={update("post_template")}
        />
      </Field>

      <div className="grid gap-3 sm:grid-cols-2">
        <Field
          label={t("admin.buttonText")}
          value={form.button_text || ""}
          onChange={update("button_text")}
          error={errors.button_text}
        />
        <Field
          label={t("admin.maxSpecs")}
          type="number"
          min="0"
          max="20"
          value={form.max_specs_in_post ?? 5}
          onChange={update("max_specs_in_post")}
          error={errors.max_specs_in_post}
        />
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {[
          ["is_enabled", t("admin.telegramEnabled")],
          ["auto_publish", t("admin.autoPublish")],
          ["publish_media", t("admin.publishMedia")],
          ["publish_video", t("admin.publishVideo")],
          ["update_on_sold", t("admin.updateOnSold")],
        ].map(([key, label]) => (
          <label key={key} className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={Boolean(form[key])} onChange={update(key)} />
            {label}
          </label>
        ))}
      </div>

      <button type="submit" className="btn btn-primary" disabled={save.isPending}>
        <Save size={16} aria-hidden="true" />
        {save.isPending ? t("common.loading") : t("common.save")}
      </button>
    </form>
  );
}

function PostsList() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["telegram-posts", status],
    queryFn: () => adminApi.telegramPosts({ status: status || undefined }),
  });

  const republish = useMutation({
    mutationFn: (id) => adminApi.republish(id),
    onSuccess: (result) => {
      toast.success(result.detail);
      queryClient.invalidateQueries({ queryKey: ["telegram-posts"] });
    },
    onError: (error) => toast.error(error.message),
  });

  const rows = data?.results || [];

  return (
    <div className="surface mt-4 p-5">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-bold">{t("admin.telegramPosts")}</h2>
        <select
          className="input h-9 w-auto"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          <option value="">{t("common.all")}</option>
          <option value="published">published</option>
          <option value="failed">failed</option>
          <option value="pending">pending</option>
        </select>
      </div>

      {isLoading ? (
        <Skeleton className="h-40" />
      ) : rows.length === 0 ? (
        <EmptyState icon={Send} title={t("admin.telegramPosts")} />
      ) : (
        <ul className="space-y-1">
          {rows.map((post) => (
            <li
              key={post.id}
              className="flex flex-wrap items-center gap-3 border-t py-2.5 first:border-t-0"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{post.product_title}</p>
                <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                  {post.method} · {formatRelativeDate(post.created_at)}
                  {post.is_mock ? " · mock" : ""}
                </p>
                {post.error_message ? (
                  <p className="mt-0.5 text-xs" style={{ color: "var(--danger)" }}>
                    {post.error_message}
                  </p>
                ) : null}
              </div>

              <span
                className="shrink-0 text-xs font-medium"
                style={{ color: STATUS_TONES[post.status] || "var(--text-muted)" }}
              >
                {post.status_display || post.status}
              </span>

              <div className="flex shrink-0 gap-1">
                {post.message_url ? (
                  <a
                    href={post.message_url}
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-ghost btn-sm"
                    title={t("common.more")}
                  >
                    <ExternalLink size={15} />
                  </a>
                ) : null}
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => republish.mutate(post.id)}
                  disabled={republish.isPending}
                  title={t("admin.republish")}
                >
                  <RefreshCw size={15} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function AdminTelegramPage() {
  const { t } = useI18n();
  useHead({ title: `Telegram — ${t("nav.admin")}`, robots: "noindex, nofollow" });

  return (
    <div className="container-page py-6">
      <h1 className="mb-4 text-xl font-bold sm:text-2xl">Telegram</h1>
      <AdminNav />
      <RequireAuth>
        <SettingsForm />
        <PostsList />
      </RequireAuth>
    </div>
  );
}
