import { Link } from "react-router-dom";
import { FileQuestion } from "lucide-react";

import { useI18n, useLocalePath } from "../i18n";
import { useHead } from "../seo/Head";

export default function NotFoundPage() {
  const { t } = useI18n();
  const localePath = useLocalePath();

  // 404 sahifasi hech qachon indekslanmasligi kerak.
  useHead({
    title: `${t("error.notFound")} — ${t("brand.name")}`,
    description: t("error.notFoundText"),
    robots: "noindex, follow",
  });

  return (
    <div className="container-page flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div
        className="mb-5 flex h-20 w-20 items-center justify-center rounded-3xl"
        style={{ background: "var(--bg-muted)", color: "var(--text-subtle)" }}
      >
        <FileQuestion size={36} strokeWidth={1.5} aria-hidden="true" />
      </div>
      <p className="text-5xl font-black" style={{ color: "var(--text-subtle)" }}>
        404
      </p>
      <h1 className="mt-3 text-xl font-bold sm:text-2xl">{t("error.notFound")}</h1>
      <p className="mt-2 max-w-md text-sm" style={{ color: "var(--text-muted)" }}>
        {t("error.notFoundText")}
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        <Link to={localePath("/")} className="btn btn-primary">
          {t("error.goHome")}
        </Link>
        <Link to={localePath("/catalog")} className="btn btn-secondary">
          {t("catalog.title")}
        </Link>
      </div>
    </div>
  );
}
