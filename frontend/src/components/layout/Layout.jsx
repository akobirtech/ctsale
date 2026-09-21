import { useQuery } from "@tanstack/react-query";

import { catalog } from "../../api/endpoints";
import { ToastProvider } from "../../hooks/useToast";
import { useI18n } from "../../i18n";
import { useRouteData } from "../../store/routeData";
import BottomNav from "./BottomNav";
import Footer from "./Footer";
import Navbar from "./Navbar";

export default function Layout({ children }) {
  const { lang, t } = useI18n();

  // Kategoriyalar SSR'da allaqachon yuklangan bo'lishi mumkin —
  // shunda brauzer birinchi renderdan keyin qayta so'rov yubormaydi.
  const preloaded = useRouteData()?.categories;

  const { data: categories = [] } = useQuery({
    queryKey: ["categories", lang],
    queryFn: () => catalog.tree(lang),
    initialData: preloaded,
    staleTime: 10 * 60_000,
  });

  return (
    <ToastProvider>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:px-4 focus:py-2"
        style={{ background: "var(--accent)", color: "var(--accent-text)" }}
      >
        {t("nav.home")}
      </a>

      <div className="flex min-h-screen flex-col">
        <Navbar categories={categories} />
        {/* Mobil pastki navigatsiya kontentni to'smasligi uchun bo'shliq */}
        <main id="main" className="flex-1 pb-20 lg:pb-0">
          {children}
        </main>
        <Footer categories={categories} />
      </div>

      <BottomNav />
    </ToastProvider>
  );
}
