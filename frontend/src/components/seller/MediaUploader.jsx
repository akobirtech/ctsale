import { useRef, useState } from "react";
import { ImagePlus, Loader2, Star, Trash2, Video } from "lucide-react";

import { media as mediaApi } from "../../api/endpoints";
import { useToast } from "../../hooks/useToast";
import { useI18n } from "../../i18n";

const MAX_IMAGES = 10;
const MAX_VIDEOS = 2;

/**
 * Rasm va video yuklash.
 *
 * Yuklash mahsulot yaratilgandan keyin bo'ladi (fayllar mahsulotga
 * bog'lanadi), shuning uchun komponent `slug` ni kutadi. Backend
 * validatsiyasi (MIME, magic bytes, hajm) xato matnini o'zbekcha
 * qaytaradi — uni o'zgartirmasdan ko'rsatamiz.
 */
export default function MediaUploader({ slug, images = [], videos = [], onChange }) {
  const { t } = useI18n();
  const toast = useToast();

  const imageInput = useRef(null);
  const videoInput = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [dragging, setDragging] = useState(false);

  const remainingImages = MAX_IMAGES - images.length;

  async function uploadImages(files) {
    const list = Array.from(files || []);
    if (!list.length) return;

    if (list.length > remainingImages) {
      toast.error(
        `Yana ${remainingImages} ta rasm qo'shish mumkin, siz ${list.length} ta tanladingiz.`
      );
      return;
    }

    setUploading(true);
    setProgress(0);
    try {
      const created = await mediaApi.uploadImages(slug, list, setProgress);
      onChange({ images: [...images, ...created], videos });
      toast.success(`${created.length} ta rasm yuklandi`);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setUploading(false);
      setProgress(0);
      if (imageInput.current) imageInput.current.value = "";
    }
  }

  async function uploadVideo(file) {
    if (!file) return;
    setUploading(true);
    try {
      const created = await mediaApi.uploadVideo(slug, file);
      onChange({ images, videos: [...videos, created] });
      toast.success("Video yuklandi");
    } catch (error) {
      toast.error(error.message);
    } finally {
      setUploading(false);
      if (videoInput.current) videoInput.current.value = "";
    }
  }

  async function removeImage(image) {
    try {
      await mediaApi.deleteImage(slug, image.id);
      onChange({ images: images.filter((item) => item.id !== image.id), videos });
    } catch (error) {
      toast.error(error.message);
    }
  }

  async function removeVideo(video) {
    try {
      await mediaApi.deleteVideo(slug, video.id);
      onChange({ images, videos: videos.filter((item) => item.id !== video.id) });
    } catch (error) {
      toast.error(error.message);
    }
  }

  async function setPrimary(image) {
    try {
      await mediaApi.setPrimary(slug, image.id);
      onChange({
        images: images.map((item) => ({ ...item, is_primary: item.id === image.id })),
        videos,
      });
    } catch (error) {
      toast.error(error.message);
    }
  }

  return (
    <div className="space-y-4">
      {/* Tashlash zonasi */}
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          uploadImages(event.dataTransfer.files);
        }}
        className="rounded-xl border-2 border-dashed p-6 text-center transition-colors"
        style={{
          borderColor: dragging ? "var(--accent)" : "var(--border-strong)",
          background: dragging ? "var(--accent-soft)" : "transparent",
        }}
      >
        <ImagePlus
          size={28}
          className="mx-auto mb-2"
          style={{ color: "var(--text-subtle)" }}
          aria-hidden="true"
        />
        <p className="text-sm font-medium">{t("seller.dragDrop")}</p>
        <p className="mt-1 text-xs" style={{ color: "var(--text-subtle)" }}>
          JPG, PNG yoki WebP · har biri 10 MB gacha · yana {remainingImages} ta
        </p>

        <input
          ref={imageInput}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          className="sr-only"
          onChange={(event) => uploadImages(event.target.files)}
        />
        <button
          type="button"
          className="btn btn-secondary btn-sm mt-3"
          onClick={() => imageInput.current?.click()}
          disabled={uploading || remainingImages <= 0}
        >
          {uploading ? (
            <>
              <Loader2 size={15} className="animate-spin" aria-hidden="true" />
              {progress > 0 ? `${progress}%` : t("common.loading")}
            </>
          ) : (
            t("seller.uploadImages")
          )}
        </button>
      </div>

      {/* Yuklangan rasmlar */}
      {images.length > 0 ? (
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
          {images.map((image) => (
            <div
              key={image.id}
              className="group relative aspect-square overflow-hidden rounded-lg"
              style={{ background: "var(--bg-muted)" }}
            >
              <img
                src={image.thumb_url || image.url}
                alt={image.alt_text || ""}
                className="h-full w-full object-cover"
                loading="lazy"
              />

              {image.is_primary ? (
                <span
                  className="absolute left-1 top-1 rounded px-1.5 py-0.5 text-[10px] font-bold"
                  style={{ background: "var(--accent)", color: "var(--accent-text)" }}
                >
                  {t("seller.primaryImage")}
                </span>
              ) : (
                <button
                  type="button"
                  onClick={() => setPrimary(image)}
                  className="absolute left-1 top-1 flex h-7 w-7 items-center justify-center rounded-full opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100"
                  style={{ background: "color-mix(in srgb, var(--surface) 88%, transparent)" }}
                  aria-label={t("seller.setPrimary")}
                  title={t("seller.setPrimary")}
                >
                  <Star size={14} />
                </button>
              )}

              <button
                type="button"
                onClick={() => removeImage(image)}
                className="absolute right-1 top-1 flex h-7 w-7 items-center justify-center rounded-full opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100"
                style={{
                  background: "color-mix(in srgb, var(--surface) 88%, transparent)",
                  color: "var(--danger)",
                }}
                aria-label={t("seller.delete")}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      ) : null}

      {/* Video */}
      <div>
        <input
          ref={videoInput}
          type="file"
          accept="video/mp4,video/webm"
          className="sr-only"
          onChange={(event) => uploadVideo(event.target.files?.[0])}
        />
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() => videoInput.current?.click()}
          disabled={uploading || videos.length >= MAX_VIDEOS}
        >
          <Video size={15} aria-hidden="true" />
          Video qo&apos;shish ({videos.length}/{MAX_VIDEOS})
        </button>

        {videos.length > 0 ? (
          <ul className="mt-2 space-y-1.5">
            {videos.map((video) => (
              <li
                key={video.id}
                className="flex items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm"
                style={{ background: "var(--bg-muted)" }}
              >
                <span className="flex min-w-0 items-center gap-2">
                  <Video size={15} className="shrink-0" aria-hidden="true" />
                  <span className="truncate">{video.title || "Video"}</span>
                </span>
                <button
                  type="button"
                  onClick={() => removeVideo(video)}
                  style={{ color: "var(--danger)" }}
                  aria-label={t("seller.delete")}
                >
                  <Trash2 size={15} />
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}
