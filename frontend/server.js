/**
 * SSR server.
 *
 * Nega SSR: talab #15 mahsulot ma'lumoti sahifa manba kodida
 * bo'lishini talab qiladi. User-Agent bo'yicha ajratish (crawlerga
 * boshqa kontent berish) ishlatilmaydi — Google buni cloaking deb
 * baholashi mumkin. Shuning uchun HTML hamma uchun bir xil serverda
 * render qilinadi, React esa uning ustidan hydrate bo'ladi.
 *
 * Development: Vite middleware rejimi (HMR ishlaydi).
 * Production:  dist/client statik + dist/server render funksiyasi.
 */

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import compression from "compression";
import express from "express";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const isProduction = process.env.NODE_ENV === "production";
const port = Number(process.env.PORT || 5173);
const base = process.env.BASE || "/";
const apiTarget = process.env.API_URL || "http://127.0.0.1:8000";

const app = express();
app.disable("x-powered-by");
app.use(compression());

// Backend ochiq bo'lmasligi mumkin — SSR paytida ham, brauzerdan ham
// bir xil `/api` yo'li ishlatiladi, shuning uchun proksilaymiz.
async function proxyToBackend(req, res) {
  const target = `${apiTarget}${req.originalUrl}`;
  try {
    const headers = { ...req.headers };
    delete headers.host;
    delete headers["content-length"];

    const response = await fetch(target, {
      method: req.method,
      headers,
      body: ["GET", "HEAD"].includes(req.method) ? undefined : req,
      duplex: "half",
      redirect: "manual",
    });

    res.status(response.status);
    response.headers.forEach((value, key) => {
      if (!["content-encoding", "transfer-encoding", "connection"].includes(key)) {
        res.setHeader(key, value);
      }
    });
    const buffer = Buffer.from(await response.arrayBuffer());
    res.end(buffer);
  } catch (error) {
    console.error("[proxy]", req.originalUrl, error.message);
    res.status(502).json({
      error: { code: "backend_unavailable", message: "Server javob bermayapti." },
    });
  }
}

/**
 * 404 chiqqan yo'l uchun backendda redirect bormi?
 *
 * Faqat topilmagan sahifalarda so'raladi — normal sahifalar uchun
 * qo'shimcha so'rov bo'lmaydi.
 */
async function lookupRedirect(pathname) {
  try {
    const url = `${apiTarget}/api/v1/seo/resolve/?path=${encodeURIComponent(pathname)}`;
    const response = await fetch(url, { signal: AbortSignal.timeout(2000) });
    if (!response.ok) return null;
    const body = await response.json();
    return body.redirect || body.status === 410 ? body : null;
  } catch {
    // Backend javob bermasa oddiy 404 ko'rsatiladi — redirect uchun
    // sahifani butunlay yiqitish noto'g'ri bo'lardi.
    return null;
  }
}

app.use("/api", proxyToBackend);
app.use("/media", proxyToBackend);
// robots.txt va sitemap ham backenddan keladi (dinamik generatsiya).
app.use("/robots.txt", proxyToBackend);
app.use(/^\/sitemap.*\.xml$/, proxyToBackend);

let vite;
let templateCache;
let renderCache;

if (!isProduction) {
  const { createServer } = await import("vite");
  vite = await createServer({
    server: { middlewareMode: true },
    appType: "custom",
    base,
  });
  app.use(vite.middlewares);
} else {
  const sirv = (await import("sirv")).default;
  app.use(
    base,
    sirv(path.resolve(__dirname, "dist/client"), {
      extensions: [],
      // Hashlangan fayllar uzoq keshlanadi, index.html esa hech qachon.
      maxAge: 31536000,
      immutable: true,
    })
  );
  templateCache = await fs.readFile(path.resolve(__dirname, "dist/client/index.html"), "utf-8");
  renderCache = (await import("./dist/server/entry-server.js")).render;
}

app.use("*", async (req, res) => {
  const url = req.originalUrl.replace(base, "/");

  try {
    let template;
    let render;

    if (!isProduction) {
      template = await fs.readFile(path.resolve(__dirname, "index.html"), "utf-8");
      template = await vite.transformIndexHtml(url, template);
      render = (await vite.ssrLoadModule("/src/entry-server.jsx")).render;
    } else {
      template = templateCache;
      render = renderCache;
    }

    const rendered = await render(url, { apiBase: apiTarget, cookie: req.headers.cookie });

    // Render `redirect` qaytarsa (masalan "/" -> "/uz") shu yerda bajariladi.
    if (rendered.redirect) {
      return res.redirect(rendered.status || 302, rendered.redirect);
    }

    // Sahifa topilmadi — ehtimol manzil o'zgargandir.
    if (rendered.status === 404) {
      const moved = await lookupRedirect(url.split("?")[0]);
      if (moved?.redirect) {
        return res.redirect(moved.status || 301, moved.redirect);
      }
      if (moved?.status === 410) {
        rendered.status = 410;
      }
    }

    const html = template
      .replace("<!--app-head-->", rendered.head ?? "")
      .replace("<!--app-html-->", rendered.html ?? "")
      .replace("<!--app-state-->", rendered.state ?? "")
      .replace('<html lang="uz"', `<html lang="${rendered.lang || "uz"}"`);

    res.status(rendered.status || 200).set({ "Content-Type": "text/html; charset=utf-8" }).send(html);
  } catch (error) {
    vite?.ssrFixStacktrace?.(error);
    console.error("[ssr]", url, error);
    res.status(500).set({ "Content-Type": "text/html; charset=utf-8" }).send(
      `<!doctype html><html lang="uz"><head><meta charset="utf-8"><title>Xatolik</title></head>
       <body style="font-family:system-ui;padding:40px;max-width:640px;margin:0 auto">
         <h1>Sahifani ochib bo'lmadi</h1>
         <p>Serverda kutilmagan xatolik yuz berdi. Biroz o'tib qaytadan urinib ko'ring.</p>
       </body></html>`
    );
  }
});

app.listen(port, () => {
  console.log(`CT Sale ${isProduction ? "(production)" : "(dev)"} -> http://localhost:${port}`);
});
