import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const port = Number(process.env.PORT ?? 5173);
const apiUrl = process.env.API_URL ?? "http://api:8000/health/";
const apiOrigin = process.env.API_ORIGIN ?? "http://api:8000";
const applicationRoot = path.dirname(fileURLToPath(import.meta.url));
const distributionRoot = path.join(applicationRoot, "dist");
const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".svg": "image/svg+xml",
};

async function serveApplication(request, response) {
  const requestPath = new URL(request.url ?? "/", "http://localhost").pathname;
  const relativePath = requestPath === "/" ? "index.html" : requestPath.slice(1);
  const candidate = path.resolve(distributionRoot, relativePath);
  const safeCandidate = candidate.startsWith(`${distributionRoot}${path.sep}`);

  try {
    const body = await readFile(safeCandidate ? candidate : "");
    response.writeHead(200, {
      "Content-Type": contentTypes[path.extname(candidate)] ?? "application/octet-stream",
    });
    response.end(body);
  } catch {
    const body = await readFile(path.join(distributionRoot, "index.html"));
    response.writeHead(200, { "Content-Type": contentTypes[".html"] });
    response.end(body);
  }
}

async function proxyApi(request, response) {
  try {
    const requestPath = new URL(request.url ?? "/", "http://localhost");
    const url = new URL(requestPath.pathname + requestPath.search, apiOrigin);
    const chunks = [];
    let size = 0;
    for await (const chunk of request) {
      size += chunk.length;
      if (size > 1024 * 1024) {
        response.writeHead(413, { "Content-Type": "application/json" });
        response.end(JSON.stringify({ detail: "Request body is too large." }));
        return;
      }
      chunks.push(chunk);
    }
    const headers = {};
    for (const name of ["accept", "authorization", "content-type", "cookie"]) {
      if (typeof request.headers[name] === "string") headers[name] = request.headers[name];
    }
    const upstream = await fetch(url, {
      method: request.method,
      headers,
      ...(chunks.length ? { body: Buffer.concat(chunks) } : {}),
      redirect: "manual",
    });
    const responseHeaders = {
      "Content-Type": upstream.headers.get("content-type") ?? "application/octet-stream",
    };
    const cookies = upstream.headers.getSetCookie();
    if (cookies.length) responseHeaders["Set-Cookie"] = cookies;
    const responseBody = Buffer.from(await upstream.arrayBuffer());
    response.writeHead(upstream.status, responseHeaders);
    response.end(responseBody);
  } catch {
    response.writeHead(502, { "Content-Type": "application/json" });
    response.end(JSON.stringify({ detail: "The API is unavailable." }));
  }
}

const server = http.createServer(async (request, response) => {
  if (request.url === "/health/") {
    const body = JSON.stringify({ service: "frontend", status: "ok" });
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(body);
    return;
  }

  if (request.url === "/api-health/") {
    try {
      const apiResponse = await fetch(apiUrl);
      const body = await apiResponse.text();
      response.writeHead(apiResponse.status, {
        "Content-Type": "application/json",
      });
      response.end(body);
    } catch (error) {
      const body = JSON.stringify({ detail: String(error) });
      response.writeHead(502, { "Content-Type": "application/json" });
      response.end(body);
    }
    return;
  }

  if (new URL(request.url ?? "/", "http://localhost").pathname.startsWith("/api/")) {
    await proxyApi(request, response);
    return;
  }

  await serveApplication(request, response);
});

server.listen(port, "0.0.0.0", () => {
  console.log(`frontend listening on port ${port}`);
});
