/**
 * Cloudflare Worker – Google Sheet CSV proxy with CORS + 3s cache
 *
 * Deploy this as a Worker, then set WORKER_URL in index.html to the
 * workers.dev URL (or your custom domain route).
 *
 * Example: https://payments-sheet.YOUR_SUBDOMAIN.workers.dev
 */

const SHEET_ID = "1wJDOWDZL_7l-N-9yt5PhHJtVWsgF_mfbmlPohgr-Jyw";
const GID = "0";
const CACHE_SECONDS = 3;

const UPSTREAM = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?format=csv&gid=${GID}`;

export default {
  async fetch(request, env, ctx) {
    // Handle CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(),
      });
    }

    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405, headers: corsHeaders() });
    }

    try {
      // Cache key ignores query string so ?t=… does not bust the edge cache
      const cacheKey = new Request(UPSTREAM, { method: "GET" });
      const cache = caches.default;

      let response = await cache.match(cacheKey);

      if (!response) {
        const upstream = await fetch(UPSTREAM, {
          headers: {
            "User-Agent": "Cloudflare-Worker-Sheet-Proxy/1.0",
          },
        });

        if (!upstream.ok) {
          return new Response(`Upstream error: ${upstream.status}`, {
            status: upstream.status,
            headers: corsHeaders(),
          });
        }

        const body = await upstream.text();

        response = new Response(body, {
          status: 200,
          headers: {
            "Content-Type": "text/csv; charset=utf-8",
            "Cache-Control": `public, max-age=${CACHE_SECONDS}`,
            ...Object.fromEntries(corsHeaders()),
          },
        });

        // Store in edge cache (non-blocking)
        ctx.waitUntil(cache.put(cacheKey, response.clone()));
      } else {
        // Re-apply CORS on cached response
        response = new Response(response.body, {
          status: response.status,
          headers: {
            "Content-Type": "text/csv; charset=utf-8",
            "Cache-Control": `public, max-age=${CACHE_SECONDS}`,
            ...Object.fromEntries(corsHeaders()),
          },
        });
      }

      return response;
    } catch (err) {
      return new Response("Proxy error: " + (err.message || String(err)), {
        status: 502,
        headers: corsHeaders(),
      });
    }
  },
};

function corsHeaders() {
  return new Headers({
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  });
}
