import { memo } from "react";
import { Link } from "react-router-dom";
import { Eye, Heart, ImageOff, MapPin } from "lucide-react";

import { useI18n, useLocalePath } from "../../i18n";
import { formatCount, formatRelativeDate } from "../../utils/format";
import Badge, { conditionTone } from "../ui/Badge";

function ProductCard({ product, onToggleFavorite, priority = false }) {
  const { t, lang } = useI18n();
  const localePath = useLocalePath();

  const image = product.primary_image;
  const isSold = product.status === "sold";

  return (
    <article
      className="surface group relative flex flex-col overflow-hidden transition-shadow hover:shadow-[var(--shadow-md)]"
      style={isSold ? { opacity: 0.72 } : undefined}
    >
      <Link
        to={localePath(`/product/${product.slug}`)}
        className="relative block aspect-[4/3] overflow-hidden"
        style={{ background: "var(--bg-muted)" }}
      >
        {image?.url ? (
          <img
            src={image.url}
            alt={image.alt || product.title}
            /* Ro'yxatdagi rasmlar kartaga bir xil sig'sin */
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
            /* Birinchi ekrandagi rasmlar darhol, qolganlari kerak bo'lganda */
            loading={priority ? "eager" : "lazy"}
            fetchPriority={priority ? "high" : "auto"}
            decoding="async"
            width={400}
            height={300}
          />
        ) : (
          <div
            className="flex h-full w-full items-center justify-center"
            style={{ color: "var(--text-subtle)" }}
          >
            <ImageOff size={28} aria-hidden="true" />
          </div>
        )}

        <div className="absolute left-2 top-2 flex flex-wrap gap-1">
          <Badge tone={conditionTone(product.condition)}>{product.condition_display}</Badge>
          {product.is_featured ? <Badge tone="brand">VIP</Badge> : null}
        </div>

        {isSold ? (
          <div className="absolute inset-0 flex items-center justify-center bg-black/45">
            <span className="rounded-lg bg-black/70 px-3 py-1.5 text-sm font-bold text-white">
              {t("status.sold")}
            </span>
          </div>
        ) : null}
      </Link>

      {onToggleFavorite ? (
        <button
          type="button"
          onClick={() => onToggleFavorite(product)}
          className="absolute right-2 top-2 flex h-9 w-9 items-center justify-center rounded-full backdrop-blur transition-colors"
          style={{
            background: "color-mix(in srgb, var(--surface) 85%, transparent)",
            color: product.is_favorited ? "var(--danger)" : "var(--text-muted)",
          }}
          aria-label={product.is_favorited ? t("product.removeFavorite") : t("product.addFavorite")}
          aria-pressed={Boolean(product.is_favorited)}
        >
          <Heart size={17} fill={product.is_favorited ? "currentColor" : "none"} />
        </button>
      ) : null}

      <div className="flex flex-1 flex-col p-3">
        <Link to={localePath(`/product/${product.slug}`)} className="hover:underline">
          <h3 className="line-clamp-2 text-[13.5px] font-semibold leading-snug sm:text-sm">
            {product.title}
          </h3>
        </Link>

        {product.card_specs?.length ? (
          <p
            className="mt-1 line-clamp-1 text-[11.5px]"
            style={{ color: "var(--text-subtle)" }}
          >
            {product.card_specs.join(" · ")}
          </p>
        ) : null}

        <p className="mt-2 text-[15px] font-bold sm:text-base" style={{ color: "var(--accent)" }}>
          {product.price_display}
        </p>

        <div
          className="mt-auto flex items-center justify-between gap-2 pt-2.5 text-[11px]"
          style={{ color: "var(--text-subtle)" }}
        >
          <span className="flex min-w-0 items-center gap-1">
            <MapPin size={12} className="shrink-0" aria-hidden="true" />
            <span className="truncate">{product.region_name}</span>
          </span>
          <span className="flex shrink-0 items-center gap-1">
            <Eye size={12} aria-hidden="true" />
            {formatCount(product.views_count)}
          </span>
        </div>

        <time
          className="mt-1 text-[11px]"
          style={{ color: "var(--text-subtle)" }}
          dateTime={product.published_at || product.created_at}
        >
          {formatRelativeDate(product.published_at || product.created_at, lang)}
        </time>
      </div>
    </article>
  );
}

// Katalogda yuzlab karta bo'ladi — ota qayta render bo'lganda
// o'zgarmagan kartalar qayta chizilmasin.
export default memo(ProductCard);
