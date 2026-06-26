export interface Env {
  ASSETS: Fetcher;
  PACKAGES: R2Bucket;
  RATE_LIMITER: RateLimit;
}

const GH_API = "https://api.github.com/repos/thuruht/q3n/releases/latest";
const CORS = { "Access-Control-Allow-Origin": "*" };

function json(data: unknown, status = 200, extra: HeadersInit = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...CORS, ...extra },
  });
}

async function checkRateLimit(env: Env, ip: string): Promise<boolean> {
  const { success } = await env.RATE_LIMITER.limit({ key: ip });
  return success;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const ip = request.headers.get("CF-Connecting-IP") ?? "unknown";

    // ── /api/releases — latest GitHub release metadata ────────────
    if (url.pathname === "/api/releases") {
      const cacheKey = new Request(GH_API, request);
      const cache = caches.default;
      const cached = await cache.match(cacheKey);
      if (cached) return cached;

      const resp = await fetch(GH_API, {
        headers: { "User-Agent": "q3n-site/1.0" },
      });
      if (!resp.ok) return json({ error: "upstream failed" }, resp.status);

      const data = await resp.json() as Record<string, unknown>;
      const response = json(data, 200, {
        "Cache-Control": "public, max-age=300",
      });
      ctx.waitUntil(cache.put(cacheKey, response.clone()));
      return response;
    }

    // ── /download/:file — serve from R2 with rate limiting ────────
    if (url.pathname.startsWith("/download/")) {
      const allowed = await checkRateLimit(env, ip);
      if (!allowed) {
        return json({ error: "Rate limit exceeded — try again in a minute." }, 429);
      }

      const key = url.pathname.slice("/download/".length);
      if (!key) return json({ error: "File not specified." }, 400);

      const obj = await env.PACKAGES.get(key);
      if (!obj) return json({ error: "File not found." }, 404);

      const headers = new Headers();
      obj.writeHttpMetadata(headers);
      headers.set("etag", obj.httpEtag);
      headers.set("Cache-Control", "public, max-age=3600");
      headers.set("Content-Disposition", `attachment; filename="${key}"`);

      return new Response(obj.body, { headers });
    }

    // ── /api/packages — list available package files in R2 ────────
    if (url.pathname === "/api/packages") {
      const list = await env.PACKAGES.list();
      const files = list.objects.map((o) => ({
        name: o.key,
        size: o.size,
        uploaded: o.uploaded,
        url: `/download/${o.key}`,
      }));
      return json({ files }, 200, { "Cache-Control": "public, max-age=60" });
    }

    // Static assets (React app)
    return env.ASSETS.fetch(request);
  },
} satisfies ExportedHandler<Env>;
