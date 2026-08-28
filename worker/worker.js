const REPO = "didicola/tv-matrix";
const BRANCH = "main";
const FILES = ["eu.m3u", "films.m3u", "mega.m3u"];
const CACHE_MAX_AGE = 600;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/^\/+|\/+$/g, "");

    if (path === "health" || path === "") {
      if (request.method !== "GET") return new Response(null, { status: 405 });
      const body = path === "health"
        ? JSON.stringify({ ok: true, served: FILES })
        : html();
      return new Response(body, {
        headers: {
          "content-type": path === "health" ? "application/json" : "text/html; charset=utf-8",
          "cache-control": "no-store",
        },
      });
    }

    if (!FILES.includes(path)) return new Response("Not found", { status: 404 });

    const cache = caches.default;
    const cached = await cache.match(request);
    if (cached) return cached;

    const gh = "https://raw.githubusercontent.com/" + REPO + "/" + BRANCH + "/" + path;
    let resp;
    try {
      resp = await fetch(gh, { headers: { "user-agent": "tv-matrix-worker" } });
    } catch (e) {
      return new Response("upstream error", { status: 502 });
    }
    if (!resp.ok) return new Response("list error: " + resp.status, { status: resp.status });

    const txt = await resp.text();
    const out = new Response(txt, {
      headers: {
        "content-type": "text/plain; charset=utf-8",
        "access-control-allow-origin": "*",
        "cache-control": "public, max-age=" + CACHE_MAX_AGE,
      },
    });
    ctx.waitUntil(cache.put(request, out.clone()));
    return out;
  },
};

function html() {
  return `<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>TV FREEDOM Cloud</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:system-ui;background:#0b1020;color:#e8eefc;margin:0;padding:2rem;text-align:center}
h1{color:#90CAF9}a{color:#4dd0e1;text-decoration:none}li{list-style:none;margin:.6rem;font-size:1.1rem}
.box{max-width:520px;margin:0 auto;background:#141b30;border-radius:14px;padding:1.5rem}</style></head>
<body><div class="box"><h1>TV FREEDOM Cloud</h1>
<p dir="rtl" style="color:#cdd7f0">سحابة قنواتك مجانية ومشفرة HTTPS</p>
<ul>
<li><a href="/mega.m3u">mega.m3u &#8212; 3238 chaînes (FR/DE/ES/IT/UK/US/AR)</a></li>
<li><a href="/eu.m3u">eu.m3u &#8212; chaînes vérifiées</a></li>
<li><a href="/films.m3u">films.m3u &#8212; films gratuits</a></li>
</ul><p><a href="/health">/health</a> &#183; HTTPS chiffré &#183; CORS&nbsp;*</p></div></body></html>`;
}