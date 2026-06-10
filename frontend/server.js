const express = require("express");
const path = require("path");
const fs = require("fs");
const http = require("http");
const https = require("https");
const httpProxy = require("http-proxy");

const app = express();
const PORT = process.env.PORT || 3000;

// Backend target for the WebSocket proxy. Use the http(s) scheme; the
// original request path (/ws) is preserved when proxied.
const BACKEND_TARGET = process.env.BACKEND_TARGET || "http://localhost:8000";

// Optional TLS. If both files exist we serve HTTPS (required so the browser
// exposes the microphone when the page is reached via an EC2 IP / LAN host).
const CERT_DIR = process.env.CERT_DIR || path.join(__dirname, "certs");
const CERT_PATH = process.env.CERT_PATH || path.join(CERT_DIR, "cert.pem");
const KEY_PATH = process.env.KEY_PATH || path.join(CERT_DIR, "key.pem");
const useHttps = fs.existsSync(CERT_PATH) && fs.existsSync(KEY_PATH);

app.use(express.static(path.join(__dirname, "public")));

// The client builds the WebSocket URL from its own origin and this path, so
// HTTPS pages get wss:// automatically with no mixed-content issues.
app.get("/config", (req, res) => {
  res.json({ wsPath: "/ws" });
});

const server = useHttps
  ? https.createServer(
      { cert: fs.readFileSync(CERT_PATH), key: fs.readFileSync(KEY_PATH) },
      app
    )
  : http.createServer(app);

const proxy = httpProxy.createProxyServer({
  target: BACKEND_TARGET,
  ws: true,
  changeOrigin: true,
});
proxy.on("error", (err) => {
  console.error("WebSocket proxy error:", err.message);
});

server.on("upgrade", (req, socket, head) => {
  if (req.url === "/ws" || req.url.startsWith("/ws?")) {
    proxy.ws(req, socket, head);
  } else {
    socket.destroy();
  }
});

server.listen(PORT, () => {
  const scheme = useHttps ? "https" : "http";
  console.log(`Frontend running at ${scheme}://localhost:${PORT}`);
  console.log(`Proxying WebSocket /ws -> ${BACKEND_TARGET}`);
  if (!useHttps) {
    console.log(
      `No TLS cert found at ${CERT_PATH}. Serving HTTP only ` +
        "(mic works on localhost; needs HTTPS for remote/IP access)."
    );
  }
});
