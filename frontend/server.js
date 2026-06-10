const express = require("express");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_WS = process.env.BACKEND_WS || "ws://localhost:8000/ws";

app.use(express.static(path.join(__dirname, "public")));

app.get("/config", (req, res) => {
  res.json({ wsUrl: BACKEND_WS });
});

app.listen(PORT, () => {
  console.log(`Frontend running at http://localhost:${PORT}`);
});
