import { Link } from "react-router-dom";
import { Heart } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { favorites as favoritesApi } from "../api/endpoints";
import ProductGrid from "../components/product/ProductGrid";
import RequireAuth from "../components/auth/RequireAuth";
import ErrorState from "../components/ui/ErrorState";
import { useToast } from "../hooks/useToast";
import { useI18n, useLocalePath } from "../i18n";
import { useHead } from "../seo/Head";

function FavoritesContent() {
  const { t, lang } = useI18n();
  const localePath = useLocalePath();
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["favorites", lang],
    queryFn: () => favoritesApi.list({ lang }),
  });

  const toggle = useMutation({
    mutationFn: (product) => favoritesApi.toggle(product.slug),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
      toast.success(result.detail);
    },
    onError: (error) => toast.error(error.message),
  });

  if (isError) {
    return <ErrorState onRetry={refetch} />;
  }

  return (
    <ProductGrid
      products={data?.results || []}
      loading={isLoading}
      onToggleFavorite={(product) => toggle.mutate(product)}
      emptyTitle={t("empty.favorites")}
      emptyDescription={t("empty.favoritesHint")}
      emptyAction={
        <Link to={localePath("/catalog")} className="btn btn-primary btn-sm">
          {t("catalog.title")}
        </Link>
      }
    />
  );
}

export default function FavoritesPage() {
  const { t } = useI18n();

  useHead({
    title: `${t("nav.favorites")} — ${t("brand.name")}`,
    robots: "noindex, follow",
  });

  return (
    <div className="container-page py-6">
      <h1 className="mb-5 flex items-center gap-2 text-xl font-bold sm:text-2xl">
        <Heart size={22} aria-hidden="true" style={{ color: "var(--danger)" }} />
        {t("nav.favorites")}
      </h1>

      <RequireAuth>
        <FavoritesContent />
      </RequireAuth>
    </div>
  );
}
