/**
 * SSR kirish nuqtasi.
 *
 * Tartib: til aniqlanadi -> marshrut topiladi -> loader ishlaydi ->
 * HTML render qilinadi -> `<head>` yig'iladi -> ma'lumot brauzerga
 * serializatsiya qilinadi.
 */

import { StrictMode } from "react";
import { renderToString } from "react-dom/server";
import { StaticRouter } from "react-router-dom/server";

import App from "./App";
import { DEFAULT_LANGUAGE, isSupported, langFromPath } from "./i18n";
import { HeadCollector, renderHeadToString } from "./seo/Head";
import { matchRoute, routes } from "./routes";
import { RouteDataProvider } from "./store/routeData";

// Boshlang'ich ma'lumot JS kodi sifatida emas,
// <script type="application/json"> ichida uzatiladi. Shunda U+2028 va
// U+2029 kabi JS manbasini buzadigan belgilar muammo tug'dirmaydi —
// bu kontekstda faqat yopuvchi teg ketma-ketligini to'sish kerak.
const BACKSLASH = String.fromCharCode(92);
const CLOSE_TAG = "</script";
const ESCAPED_CLOSE_TAG = "<" + BACKSLASH + "/script";

function serializeState(data) {
  return JSON.stringify(data).split(CLOSE_TAG).join(ESCAPED_CLOSE_TAG);
}

export async function render(url, context = {}) {
  const [pathname, search = ""] = url.split("?");

  // Til prefiksisiz kirilsa standart tilga 302 bilan yo'naltiramiz.
  // 301 emas: kelajakda brauzer tiliga qarab tanlash qo'shilishi mumkin,
  // doimiy redirect esa keshda qotib qolardi.
  const lang = langFromPath(pathname);
  if (!lang) {
    const clean = pathname === "/" ? "" : pathname;
    return {
      redirect: `/${DEFAULT_LANGUAGE}${clean}${search ? `?${search}` : ""}`,
      status: 302,
    };
  }

  const query = Object.fromEntries(new URLSearchParams(search));
  const { route, params } = matchRoute(pathname, lang);

  let data = null;
  let status = route.id === "not-found" ? 404 : 200;

  if (route.loader) {
    try {
      data = await route.loader({ lang, params, query, context });
    } catch (error) {
      const code = error?.status || error?.response?.status;
      if (code === 404) {
        status = 404;
      } else if (code === 410) {
        status = 410;
      } else {
        console.error("[ssr loader]", route.id, error?.message || error);
        status = 500;
      }
      data = { error: { status: code || 500, message: error?.message } };
    }
  }

  // Maxfiy sahifalar SSR'da render qilinmaydi: server foydalanuvchi
  // sessiyasini bilmaydi va noto'g'ri kontent keshlanishi mumkin.
  if (route.private) {
    data = null;
  }

  const headStore = { title: "", meta: [], link: [], jsonld: [] };

  const html = renderToString(
    <StrictMode>
      <HeadCollector store={headStore}>
        <RouteDataProvider value={{ data, routeId: route.id }}>
          <StaticRouter location={url}>
            <App lang={lang} ssrStatus={status} />
          </StaticRouter>
        </RouteDataProvider>
      </HeadCollector>
    </StrictMode>
  );

  const state = `<script type="application/json" id="__INITIAL_DATA__">${serializeState({
    routeId: route.id,
    data,
    lang,
  })}</script>`;

  return {
    html,
    head: renderHeadToString(headStore),
    state,
    lang,
    status,
  };
}

export { routes, isSupported };
