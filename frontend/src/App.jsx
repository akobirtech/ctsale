import { Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/layout/Layout";
import PageLoader from "./components/ui/PageLoader";
import { DEFAULT_LANGUAGE, I18nProvider, LANGUAGES } from "./i18n";
import { routes } from "./routes";

// SSR'da har so'rov uchun yangi klient kerak — aks holda bir
// foydalanuvchining keshi boshqasiga ko'rinib qolishi mumkin.
function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        retry: (failureCount, error) => {
          // 4xx xatolarni qayta urinish ma'nosiz.
          if (error?.status >= 400 && error?.status < 500) return false;
          return failureCount < 2;
        },
        refetchOnWindowFocus: false,
      },
    },
  });
}

let browserQueryClient;

function getQueryClient() {
  if (typeof window === "undefined") return createQueryClient();
  browserQueryClient ??= createQueryClient();
  return browserQueryClient;
}

/** Bitta til ostidagi barcha sahifalar. */
function LocalizedRoutes({ lang }) {
  return (
    <I18nProvider lang={lang}>
      <Layout>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {routes.map(({ id, path, Component }) => (
              <Route key={id} path={path} element={<Component />} />
            ))}
          </Routes>
        </Suspense>
      </Layout>
    </I18nProvider>
  );
}

export default function App({ lang = DEFAULT_LANGUAGE }) {
  // Til prefiksisiz kelgan yo'l standart tilga yo'naltiriladi.
  // SSR bu holatni 302 bilan hal qiladi; bu yerdagi Navigate —
  // brauzer ichidagi navigatsiya uchun zaxira.
  const fallback = `/${LANGUAGES.includes(lang) ? lang : DEFAULT_LANGUAGE}`;

  return (
    <QueryClientProvider client={getQueryClient()}>
      <Routes>
        {LANGUAGES.map((code) => (
          <Route key={code} path={`/${code}/*`} element={<LocalizedRoutes lang={code} />} />
        ))}
        <Route path="*" element={<Navigate to={fallback} replace />} />
      </Routes>
    </QueryClientProvider>
  );
}
