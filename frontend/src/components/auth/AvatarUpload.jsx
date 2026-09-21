import { useRef, useState } from "react";
import { Camera, Trash2, User } from "lucide-react";

import { fieldErrors } from "../../api/client";
import { auth as authApi } from "../../api/endpoints";
import { useToast } from "../../hooks/useToast";
import { useI18n } from "../../i18n";
import { useAuthStore } from "../../store/auth";

// Backend ham tekshiradi, lekin 8 MB li faylni yuborib bo'lib
// "hajmi katta" javobini olish foydalanuvchi uchun isrof.
const MAX_MB = 5;

export default function AvatarUpload() {
  const { t } = useI18n();
  const toast = useToast();
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);

  const inputRef = useRef(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const shown = preview || user?.avatar;

  async function upload(event) {
    const file = event.target.files?.[0];
    // Bir xil faylni qayta tanlash ham `change` hodisasini bersin.
    event.target.value = "";
    if (!file) return;

    if (file.size > MAX_MB * 1024 * 1024) {
      setError(t("auth.avatarTooLarge", { mb: MAX_MB }));
      return;
    }

    setError("");
    setBusy(true);
    const localPreview = URL.createObjectURL(file);
    setPreview(localPreview);

    try {
      const data = new FormData();
      data.append("avatar", file);
      const updated = await authApi.updateMe(data);
      updateUser(updated);
      toast.success(t("auth.avatarSaved"));
    } catch (requestError) {
      // Yuklanmadi — ko'rsatilayotgan rasmni orqaga qaytaramiz.
      setPreview(null);
      setError(fieldErrors(requestError).avatar || requestError.message);
    } finally {
      URL.revokeObjectURL(localPreview);
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    setError("");
    try {
      const data = new FormData();
      data.append("avatar", "");
      const updated = await authApi.updateMe(data);
      updateUser(updated);
      setPreview(null);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-4">
      <div
        className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full"
        style={{ background: "var(--accent-soft)", color: "var(--accent)" }}
      >
        {shown ? (
          <img src={shown} alt="" className="h-full w-full object-cover" />
        ) : (
          <User size={28} aria-hidden="true" />
        )}
      </div>

      <div className="min-w-0">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => inputRef.current?.click()}
            disabled={busy}
          >
            <Camera size={15} aria-hidden="true" />
            {shown ? t("auth.avatarChange") : t("auth.avatarUpload")}
          </button>

          {shown ? (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={remove}
              disabled={busy}
              style={{ color: "var(--danger)" }}
            >
              <Trash2 size={15} aria-hidden="true" />
              {t("auth.avatarRemove")}
            </button>
          ) : null}
        </div>

        <p className="mt-1.5 text-xs" style={{ color: "var(--text-subtle)" }}>
          {t("auth.avatarHint", { mb: MAX_MB })}
        </p>

        {error ? (
          <p className="mt-1 text-xs font-medium" style={{ color: "var(--danger)" }} role="alert">
            {error}
          </p>
        ) : null}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={upload}
      />
    </div>
  );
}
