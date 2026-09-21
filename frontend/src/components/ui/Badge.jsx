const TONES = {
  neutral: { background: "var(--bg-muted)", color: "var(--text-muted)" },
  brand: { background: "var(--accent-soft)", color: "var(--accent)" },
  success: { background: "var(--success-soft)", color: "var(--success)" },
  warning: { background: "var(--warning-soft)", color: "var(--warning)" },
  danger: { background: "var(--danger-soft)", color: "var(--danger)" },
};

export default function Badge({ tone = "neutral", icon: Icon, children, className = "" }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-semibold ${className}`}
      style={TONES[tone] || TONES.neutral}
    >
      {Icon ? <Icon size={12} strokeWidth={2.5} aria-hidden="true" /> : null}
      {children}
    </span>
  );
}

/** Mahsulot holati uchun rang tanlovi — bir joyda turgani ma'qul. */
export function conditionTone(condition) {
  if (condition === "new") return "success";
  if (condition === "like_new") return "brand";
  if (condition === "for_parts") return "danger";
  return "neutral";
}

export function statusTone(status) {
  return (
    {
      approved: "success",
      pending: "warning",
      rejected: "danger",
      sold: "neutral",
      reserved: "brand",
      draft: "neutral",
      expired: "warning",
      archived: "neutral",
    }[status] || "neutral"
  );
}
