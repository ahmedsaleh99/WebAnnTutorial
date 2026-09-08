import http from "node:http";

const port = Number(process.env.PORT ?? 5173);
const apiUrl = process.env.API_URL ?? "http://api:8000/health/";

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

  if (request.url === "/") {
    const body = "<h1>WebAnnTutorial container foundation</h1>";
    response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    response.end(body);
    return;
  }

  response.writeHead(404, { "Content-Type": "application/json" });
  response.end(JSON.stringify({ detail: "Not found" }));
});

server.listen(port, "0.0.0.0", () => {
  console.log(`frontend listening on port ${port}`);
});
