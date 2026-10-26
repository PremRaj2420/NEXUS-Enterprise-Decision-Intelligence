const API_BASE = (window.NEXUS_API_BASE || "").replace(/\/+$/, "");
const $ = (id) => document.getElementById(id);
let trendChart;
let forecastChart;

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) throw new Error(`API request failed (${response.status}): ${path}`);
  return response.json();
}
const money = (value) => "₹" + Number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 });

function setNotice(message, type = "") {
  const notice = $("connectionNotice");
  notice.textContent = message;
  notice.className = "notice" + (type ? " " + type : "");
}

async function loadDashboard() {
  if (!API_BASE) {
    setNotice("Backend URL not configured. Deploy the Flask API on Render, then set NEXUS_API_BASE in config.js.", "error");
    $("answer").textContent = "The frontend is deployed, but it needs the URL of your deployed Python API.";
    return;
  }
  try {
    const summary = await api("/api/summary");
    $("revenue").textContent = money(summary.revenue);
    $("profit").textContent = money(summary.profit);
    $("orders").textContent = Number(summary.orders).toLocaleString("en-IN");
    $("margin").textContent = summary.margin + "%";

    const monthly = await api("/api/monthly");
    if (trendChart) trendChart.destroy();
    trendChart = new Chart($("trend"), {
      type: "line",
      data: {
        labels: monthly.map((row) => row.month),
        datasets: [
          { label: "Revenue", data: monthly.map((row) => row.revenue), tension: 0.35 },
          { label: "Profit", data: monthly.map((row) => row.profit), tension: 0.35 }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });

    const forecast = await api("/api/forecast");
    if (forecastChart) forecastChart.destroy();
    forecastChart = new Chart($("forecast"), {
      type: "bar",
      data: { labels: forecast.months, datasets: [{ label: "Forecast revenue", data: forecast.values }] },
      options: { responsive: true, maintainAspectRatio: false }
    });

    const regionRows = await api("/api/regions");
    $("regions").innerHTML =
      '<div class="row head"><div>REGION</div><div>REVENUE</div><div>PROFIT</div><div>ORDERS</div></div>' +
      regionRows.map((row) => `<div class="row"><div>${row.region}</div><div>${money(row.revenue)}</div><div>${money(row.profit)}</div><div>${row.orders}</div></div>`).join("");

    const productRows = await api("/api/products");
    $("products").innerHTML =
      '<div class="row head"><div>PRODUCT</div><div>REVENUE</div><div>PROFIT</div><div>UNITS</div></div>' +
      productRows.slice(0, 6).map((row) => `<div class="row"><div>${row.product}</div><div>${money(row.revenue)}</div><div>${money(row.profit)}</div><div>${row.quantity}</div></div>`).join("");

    const anomalyRows = await api("/api/anomalies");
    $("anomalies").innerHTML =
      '<div class="row head"><div>DATE</div><div>REGION</div><div>PRODUCT</div><div>REVENUE</div></div>' +
      anomalyRows.map((row) => `<div class="row"><div>${row.date}</div><div>${row.region}</div><div>${row.product}</div><div>${money(row.revenue)}</div></div>`).join("");

    setNotice("Connected to NEXUS API · Dashboard data loaded", "ok");
  } catch (error) {
    console.error(error);
    setNotice("Could not reach the backend. Check the Render service URL, status, and CORS settings.", "error");
    $("answer").textContent = "API connection failed. Confirm the backend URL in config.js and check the Render service logs.";
  }
}

async function askBusinessQuestion() {
  const question = $("question").value.trim();
  if (!question) return;
  $("answer").textContent = "Analyzing business data...";
  try {
    const result = await api("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });
    $("answer").textContent = result.answer;
  } catch (error) {
    $("answer").textContent = "Could not reach the backend. Check the Render URL and service status.";
  }
}
$("askButton").addEventListener("click", askBusinessQuestion);
$("question").addEventListener("keydown", (event) => {
  if (event.key === "Enter") askBusinessQuestion();
});
loadDashboard();
