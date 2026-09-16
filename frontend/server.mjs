import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const port = Number(process.env.PORT ?? 5173);
const apiUrl = process.env.API_URL ?? "http://api:8000/health/";
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

  await serveApplication(request, response);
});

server.listen(port, "0.0.0.0", () => {
  console.log(`frontend listening on port ${port}`);
});
