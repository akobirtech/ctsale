import { PackageOpen } from "lucide-react";

export default function EmptyState({ icon: Icon = PackageOpen, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16 text-center">
      <div
        className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl"
        style={{ background: "var(--bg-muted)", color: "var(--text-subtle)" }}
      >
        <Icon size={28} strokeWidth={1.75} aria-hidden="true" />
      </div>
      <h3 className="text-base font-semibold" style={{ color: "var(--text)" }}>
        {title}
      </h3>
      {description ? (
        <p className="mt-1.5 max-w-sm text-sm" style={{ color: "var(--text-muted)" }}>
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
