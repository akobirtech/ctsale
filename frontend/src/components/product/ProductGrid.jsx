import { PackageOpen, SearchX } from "lucide-react";

import { useI18n } from "../../i18n";
import EmptyState from "../ui/EmptyState";
import { ProductGridSkeleton } from "../ui/Skeleton";
import ProductCard from "./ProductCard";

export default function ProductGrid({
  products = [],
  loading = false,
  onToggleFavorite,
  emptyTitle,
  emptyDescription,
  emptyAction,
  isSearch = false,
  skeletonCount = 8,
}) {
  const { t } = useI18n();

  if (loading) return <ProductGridSkeleton count={skeletonCount} />;

  if (!products.length) {
    return (
      <EmptyState
        icon={isSearch ? SearchX : PackageOpen}
        title={emptyTitle || t(isSearch ? "empty.search" : "empty.products")}
        description={emptyDescription || (isSearch ? t("empty.searchHint") : undefined)}
        action={emptyAction}
      />
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-4">
      {products.map((product, index) => (
        <ProductCard
          key={product.id}
          product={product}
          onToggleFavorite={onToggleFavorite}
          /* Birinchi qator rasmlari LCP ga ta'sir qiladi */
          priority={index < 4}
        />
      ))}
    </div>
  );
}
