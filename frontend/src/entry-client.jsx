/** Brauzer kirish nuqtasi — serverda render qilingan HTML ustidan hydrate. */

import { StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { ROUTER_FUTURE } from "./routerConfig";
import { DEFAULT_LANGUAGE, langFromPath } from "./i18n";
import { HeadCollector } from "./seo/Head";
import { RouteDataProvider } from "./store/routeData";
import { useAuthStore } from "./store/auth";
import { useThemeStore } from "./store/theme";

import "./styles/index.css";

/** Server joylagan JSON blokini o'qiydi. */
function readInitialData() {
  const node = document.getElementById("__INITIAL_DATA__");
  if (!node) return {};
  try {
    return JSON.parse(node.textContent || "{}");
  } catch {
    // Ma'lumot buzilgan bo'lsa sahifa baribir ishlasin — komponentlar
    // o'zlari yuklab oladi.
    return {};
  }
}

const initial = readInitialData();
const lang = initial.lang || langFromPath(window.location.pathname) || DEFAULT_LANGUAGE;

// Mavzuni hydrate'dan oldin qo'llaymiz — aks holda quyuq rejimda
// bir zumda oq ekran "miltillaydi".
useThemeStore.getState().init();

hydrateRoot(
  document.getElementById("root"),
  <StrictMode>
    <HeadCollector store={null}>
      <RouteDataProvider value={{ data: initial.data ?? null, routeId: initial.routeId ?? null }}>
        <BrowserRouter future={ROUTER_FUTURE}>
          <App lang={lang} />
        </BrowserRouter>
      </RouteDataProvider>
    </HeadCollector>
  </StrictMode>
);

// Sessiyani tiklash birinchi bo'yoqni kutadi — sahifa tezroq ko'rinsin.
const restoreSession = () => useAuthStore.getState().restore();
if (typeof requestIdleCallback === "function") requestIdleCallback(restoreSession);
else setTimeout(restoreSession, 200);
