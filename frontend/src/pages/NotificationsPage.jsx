import { useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  Ban,
  Bell,
  BellOff,
  CheckCheck,
  CircleCheck,
  CircleX,
  Clock,
  Info,
  Search,
  Send,
} from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { notifications as notificationsApi } from "../api/endpoints";
import RequireAuth from "../components/auth/RequireAuth";
import EmptyState from "../components/ui/EmptyState";
import PageLoader from "../components/ui/PageLoader";
import { useToast } from "../hooks/useToast";
import { useI18n, useLocalePath } from "../i18n";
import { useHead } from "../seo/Head";
import { formatRelativeDate } from "../utils/format";

// Har bir turga belgi va rang: ro'yxatni o'qimasdan ham nima
// bo'lganini ko'rish uchun.
const ICONS = {
  product_approved: { icon: CircleCheck, tone: "var(--success)" },
  product_rejected: { icon: CircleX, tone: "var(--danger)" },
  product_expiring: { icon: Clock, tone: "var(--warning)" },
  product_expired: { icon: Clock, tone: "var(--text-subtle)" },
  product_sold: { icon: CircleCheck, tone: "var(--success)" },
  product_reported: { icon: AlertTriangle, tone: "var(--warning)" },
  seller_verified: { icon: CircleCheck, tone: "var(--success)" },
  telegram_published: { icon: Send, tone: "var(--accent)" },
  telegram_failed: { icon: AlertTriangle, tone: "var(--danger)" },
  saved_search_match: { icon: Search, tone: "var(--accent)" },
  account_banned: { icon: Ban, tone: "var(--danger)" },
  system: { icon: Info, tone: "var(--text-muted)" },
};

function NotificationRow({ item, onRead }) {
  const localePath = useLocalePath();
  const { icon: Icon, tone } = ICONS[item.type] || ICONS.system;

  // Havola backendda til prefiksisiz saqlanadi — joriy tilga moslaymiz.
  const target = item.link ? localePath(item.link) : null;

  const body = (
    <div className="flex gap-3">
      <div
        className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
        style={{ background: "var(--bg-muted)", color: tone }}
      >
        <Icon size={17} aria-hidden="true" />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-semibold">{item.title}</p>
          {!item.is_read ? (
            <span
              className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
              style={{ background: "var(--accent)" }}
              aria-label="o'qilmagan"
            />
          ) : null}
        </div>

        {item.body ? (
          <p className="mt-0.5 text-sm" style={{ color: "var(--text-muted)" }}>
            {item.body}
          </p>
        ) : null}

        <p className="mt-1 text-xs" style={{ color: "var(--text-subtle)" }}>
          {formatRelativeDate(item.created_at)}
        </p>
      </div>
    </div>
  );

  const className = "block w-full rounded-xl p-3 text-left transition-colors hover:bg-[var(--bg-muted)]";
  const style = item.is_read ? undefined : { background: "var(--accent-soft)" };

  if (target) {
    return (
      <Link to={target} className={className} style={style} onClick={() => onRead(item)}>
        {body}
      </Link>
    );
  }

  return (
    <button type="button" className={className} style={style} onClick={() => onRead(item)}>
      {body}
    </button>
  );
}

function NotificationsContent() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [onlyUnread, setOnlyUnread] = useState(false);

  useHead({ title: t("nav.notifications"), robots: "noindex, nofollow" });

  const { data, isLoading, isError } = useQuery({
    queryKey: ["notifications", onlyUnread],
    queryFn: () => notificationsApi.list(onlyUnread ? { unread: "true" } : undefined),
  });

  const markRead = useMutation({
    mutationFn: (id) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAll = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: (result) => {
      toast.success(result.detail);
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  function handleRead(item) {
    if (!item.is_read) markRead.mutate(item.id);
  }

  if (isLoading) return <PageLoader />;

  const items = data?.results || [];
  const unread = data?.unread_count || 0;

  return (
    <div className="container-page max-w-3xl py-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold">
          {t("nav.notifications")}
          {unread > 0 ? (
            <span className="ml-2 text-sm font-medium" style={{ color: "var(--accent)" }}>
              {unread}
            </span>
          ) : null}
        </h1>

        <div className="flex gap-2">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setOnlyUnread((value) => !value)}
            aria-pressed={onlyUnread}
          >
            {onlyUnread ? <Bell size={15} /> : <BellOff size={15} />}
            {onlyUnread ? t("common.all") : t("notifications.onlyUnread")}
          </button>

          {unread > 0 ? (
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => markAll.mutate()}
              disabled={markAll.isPending}
            >
              <CheckCheck size={15} />
              {t("notifications.markAllRead")}
            </button>
          ) : null}
        </div>
      </div>

      {isError ? (
        <EmptyState title={t("error.generic")} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Bell}
          title={t("notifications.empty")}
          description={t("notifications.emptyHint")}
        />
      ) : (
        <div className="surface space-y-1 p-2">
          {items.map((item) => (
            <NotificationRow key={item.id} item={item} onRead={handleRead} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function NotificationsPage() {
  return (
    <RequireAuth>
      <NotificationsContent />
    </RequireAuth>
  );
}
