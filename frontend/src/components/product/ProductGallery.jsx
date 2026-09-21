import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, ImageOff, Play, X } from "lucide-react";

import { useI18n } from "../../i18n";

/**
 * Rasm va video galereyasi + lightbox.
 *
 * Birinchi rasm `eager` yuklanadi va u LCP elementi bo'ladi —
 * shuning uchun unga `fetchpriority="high"` beriladi.
 */
export default function ProductGallery({ images = [], videos = [], title }) {
  const { t } = useI18n();
  const items = [
    ...images.map((image) => ({ type: "image", data: image })),
    ...videos.map((video) => ({ type: "video", data: video })),
  ];

  const [index, setIndex] = useState(0);
  const [lightboxOpen, setLightboxOpen] = useState(false);

  const go = useCallback(
    (delta) => setIndex((current) => (current + delta + items.length) % items.length),
    [items.length]
  );

  // Lightbox ochiqligida klaviatura bilan boshqarish.
  useEffect(() => {
    if (!lightboxOpen) return;
    function onKey(event) {
      if (event.key === "Escape") setLightboxOpen(false);
      if (event.key === "ArrowRight") go(1);
      if (event.key === "ArrowLeft") go(-1);
    }
    document.addEventListener("keydown", onKey);
    // Orqa fon aylanmasin
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [lightboxOpen, go]);

  if (!items.length) {
    return (
      <div
        className="surface flex aspect-[4/3] items-center justify-center"
        style={{ color: "var(--text-subtle)" }}
      >
        <ImageOff size={40} strokeWidth={1.5} aria-hidden="true" />
      </div>
    );
  }

  const active = items[index];

  return (
    <div>
      <div
        className="surface relative aspect-[4/3] overflow-hidden"
        style={{ background: "var(--bg-muted)" }}
      >
        {active.type === "image" ? (
          <button
            type="button"
            className="h-full w-full cursor-zoom-in"
            onClick={() => setLightboxOpen(true)}
            aria-label={`${title} — ${index + 1}`}
          >
            <img
              src={active.data.large_url || active.data.url}
              alt={active.data.alt_text || title}
              className="h-full w-full object-contain"
              loading={index === 0 ? "eager" : "lazy"}
              fetchpriority={index === 0 ? "high" : "auto"}
              decoding="async"
              width={active.data.width || 1200}
              height={active.data.height || 900}
            />
          </button>
        ) : (
          <video
            src={active.data.url}
            poster={active.data.poster_url || undefined}
            controls
            preload="metadata"
            className="h-full w-full object-contain"
          >
            <track kind="captions" />
          </video>
        )}

        {items.length > 1 ? (
          <>
            <button
              type="button"
              onClick={() => go(-1)}
              className="absolute left-2 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full backdrop-blur"
              style={{ background: "color-mix(in srgb, var(--surface) 80%, transparent)" }}
              aria-label="Oldingi"
            >
              <ChevronLeft size={20} />
            </button>
            <button
              type="button"
              onClick={() => go(1)}
              className="absolute right-2 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full backdrop-blur"
              style={{ background: "color-mix(in srgb, var(--surface) 80%, transparent)" }}
              aria-label="Keyingi"
            >
              <ChevronRight size={20} />
            </button>
            <span
              className="absolute bottom-2 right-2 rounded-md px-2 py-0.5 text-xs font-semibold backdrop-blur"
              style={{ background: "color-mix(in srgb, var(--surface) 80%, transparent)" }}
            >
              {index + 1} / {items.length}
            </span>
          </>
        ) : null}
      </div>

      {items.length > 1 ? (
        <div className="mt-2 flex gap-2 overflow-x-auto pb-1">
          {items.map((item, itemIndex) => (
            <button
              key={`${item.type}-${item.data.id}`}
              type="button"
              onClick={() => setIndex(itemIndex)}
              className="relative h-16 w-20 shrink-0 overflow-hidden rounded-lg border-2 transition-colors"
              style={{
                borderColor: itemIndex === index ? "var(--accent)" : "transparent",
                background: "var(--bg-muted)",
              }}
              aria-label={`${itemIndex + 1}`}
              aria-current={itemIndex === index}
            >
              {item.type === "image" ? (
                <img
                  src={item.data.thumb_url || item.data.url}
                  alt=""
                  className="h-full w-full object-cover"
                  loading="lazy"
                  decoding="async"
                />
              ) : (
                <span
                  className="flex h-full w-full items-center justify-center"
                  style={{ color: "var(--text-muted)" }}
                >
                  <Play size={18} aria-hidden="true" />
                </span>
              )}
            </button>
          ))}
        </div>
      ) : null}

      {lightboxOpen && active.type === "image" ? (
        <div
          className="fixed inset-0 z-[80] flex items-center justify-center bg-black/92 p-4"
          role="dialog"
          aria-modal="true"
          aria-label={title}
        >
          <button
            type="button"
            className="absolute right-4 top-4 flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white"
            onClick={() => setLightboxOpen(false)}
            aria-label={t("common.close")}
          >
            <X size={22} />
          </button>

          {items.length > 1 ? (
            <>
              <button
                type="button"
                onClick={() => go(-1)}
                className="absolute left-3 flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white"
                aria-label="Oldingi"
              >
                <ChevronLeft size={24} />
              </button>
              <button
                type="button"
                onClick={() => go(1)}
                className="absolute right-3 flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white"
                aria-label="Keyingi"
              >
                <ChevronRight size={24} />
              </button>
            </>
          ) : null}

          <img
            src={active.data.large_url || active.data.url}
            alt={active.data.alt_text || title}
            className="max-h-full max-w-full object-contain"
          />
        </div>
      ) : null}
    </div>
  );
}
