import { useI18n } from "../i18n";
import { useHead } from "../seo/Head";

export default function FavoritesPage() {
  const { t } = useI18n();
  useHead({ title: `${t("nav.favorites")} — ${t("brand.name")}`, robots: "noindex, follow" });
  return (
    <div className="container-page py-10">
      <h1 className="text-xl font-bold">{t("nav.favorites")}</h1>
      <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
        Bu sahifa tayyorlanmoqda.
      </p>
    </div>
  );
}
