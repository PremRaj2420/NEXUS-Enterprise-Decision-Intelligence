const $ = (id) => document.getElementById(id);
const fmtMoney = (value) => "₹" + Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
const fmtNum = (value) => Number(value || 0).toLocaleString("en-IN");
const fmtPct = (value) => Number(value || 0).toFixed(1) + "%";
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (ch) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[ch]));
let overviewChart = null;
let salesChart = null;
let forecastChart = null;
let allRegions = [];
let allProducts = [];
let currentView = "overview";
let toastTimer = null;

async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = "Request failed (" + response.status + ")";
    try {
      const body = await response.json();
      if (body.error || body.message) message = body.error || body.message;
    } catch (_) {}
    throw new Error(message);
  }
  return response.json();
}

function showToast(message, isError = false) {
  const node = $("toast");
  node.textContent = message;
  node.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.className = "toast"; }, 3200);
}

function navigate(view) {
  if (!document.getElementById("view-" + view)) return;
  currentView = view;
  document.querySelectorAll(".page-view").forEach((node) => {
    node.classList.toggle("active", node.id === "view-" + view);
  });
  document.querySelectorAll(".nav[data-view]").forEach((node) => {
    node.classList.toggle("active", node.dataset.view === view);
  });
  const names = {
    overview: "Overview", sales: "Sales analytics", customers: "Customer 360",
    insights: "AI insights", assistant: "Business analyst", reports: "Reports & exports"
  };
  $("pageCrumb").textContent = names[view] || "Overview";
  if (view === "sales") loadSales();
  if (view === "customers") loadCustomers();
  if (view === "insights") loadInsights();
}

document.querySelectorAll("[data-view]").forEach((node) => {
  node.addEventListener("click", (event) => {
    event.preventDefault();
    navigate(node.dataset.view);
  });
});

function table(headers, rows, emptyText = "No data to display.") {
  if (!rows.length) return '<div class="empty-state">' + esc(emptyText) + "</div>";
  return '<table><thead><tr>' + headers.map((h) => "<th>" + esc(h.label) + "</th>").join("") +
    "</tr></thead><tbody>" + rows.map((row) => "<tr>" + headers.map((h) => {
      const value = h.render ? h.render(row[h.key], row) : esc(row[h.key]);
      return "<td>" + value + "</td>";
    }).join("") + "</tr>").join("") + "</tbody></table>";
}

function riskBadge(value) {
  const risk = Number(value || 0);
  const level = risk >= 70 ? "high" : risk >= 40 ? "medium" : "low";
  const label = level === "high" ? "High" : level === "medium" ? "Medium" : "Low";
  return '<span class="risk-badge risk-' + level + '">' + label + " · " + risk.toFixed(0) + "%</span>";
}

function setChart(previous, target, config) {
  if (previous) previous.destroy();
  return new Chart($(target), config);
}

function lineChart(labels, series) {
  return {
    type: "line",
    data: { labels, datasets: series.map((s) => ({
      label: s.label, data: s.data, borderColor: s.color, backgroundColor: s.fill || s.color,
      tension: 0.34, borderWidth: 2, pointRadius: 2, pointHoverRadius: 5,
      fill: false
    })) },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 7, padding: 18 } } },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#8290a3" } },
        y: { grid: { color: "#edf1f6" }, ticks: { color: "#8290a3", callback: (v) => v >= 1000000 ? "₹" + (v / 1000000).toFixed(1) + "M" : "₹" + Math.round(v / 1000) + "k" } }
      }
    }
  };
}

function renderRegionTable(target, rows) {
  $(target).innerHTML = table([
    {key:"region", label:"Region"},
    {key:"revenue", label:"Revenue", render:(v) => fmtMoney(v)},
    {key:"profit", label:"Profit", render:(v) => fmtMoney(v)},
    {key:"orders", label:"Orders", render:(v) => fmtNum(v)}
  ], rows);
}

function renderProductTable(target, rows) {
  $(target).innerHTML = table([
    {key:"product", label:"Product"},
    {key:"revenue", label:"Revenue", render:(v) => fmtMoney(v)},
    {key:"profit", label:"Profit", render:(v) => fmtMoney(v)},
    {key:"margin", label:"Margin", render:(v) => fmtPct(v)}
  ], rows);
}

async function loadOverview() {
  const [summary, monthly, regions, products, insightResult] = await Promise.all([
    api("/api/summary"), api("/api/monthly"), api("/api/regions"), api("/api/products"), api("/api/insights")
  ]);
  $("kpiRevenue").textContent = fmtMoney(summary.revenue);
  $("kpiProfit").textContent = fmtMoney(summary.profit);
  $("kpiOrders").textContent = fmtNum(summary.orders);
  $("kpiMargin").textContent = fmtPct(summary.margin);
  $("kpiCustomers").textContent = fmtNum(summary.customers);
  $("kpiAov").textContent = fmtMoney(summary.avg_order_value);
  $("kpiRisk").textContent = fmtNum(summary.high_risk_customers);
  $("lastUpdated").textContent = "Updated " + new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"});
  overviewChart = setChart(overviewChart, "overviewTrend", lineChart(
    monthly.map((x) => x.month),
    [{label:"Revenue",data:monthly.map((x)=>x.revenue),color:"#3579e8"},
     {label:"Profit",data:monthly.map((x)=>x.profit),color:"#8b68df"}]
  ));
  renderRegionTable("overviewRegions", regions.slice(0, 5));
  renderProductTable("overviewProducts", products.slice(0, 5));
  $("overviewInsights").innerHTML = insightResult.insights.slice(0, 3).map((item) =>
    '<div class="signal-row"><span class="signal-dot ' + esc(item.type) + '"></span><div><strong>' + esc(item.title) + '</strong><p>' + esc(item.detail) + '</p></div><span class="signal-arrow">→</span></div>'
  ).join("");
  allRegions = regions.map((x) => x.region);
  allProducts = products.map((x) => x.product);
  populateFilterOptions();
}

function populateFilterOptions() {
  $("salesRegion").innerHTML = '<option value="All">All regions</option>' +
    allRegions.map((r) => '<option value="' + esc(r) + '">' + esc(r) + "</option>").join("");
  $("salesProduct").innerHTML = '<option value="All">All products</option>' +
    allProducts.map((p) => '<option value="' + esc(p) + '">' + esc(p) + "</option>").join("");
}

function salesQuery() {
  const params = new URLSearchParams();
  const start = $("salesStart").value;
  const end = $("salesEnd").value;
  const region = $("salesRegion").value;
  const product = $("salesProduct").value;
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  if (region && region !== "All") params.set("region", region);
  if (product && product !== "All") params.set("product", product);
  return params.toString();
}

async function loadSales() {
  try {
    const result = await api("/api/sales" + (salesQuery() ? "?" + salesQuery() : ""));
    $("salesRevenue").textContent = fmtMoney(result.totals.revenue);
    $("salesProfit").textContent = fmtMoney(result.totals.profit);
    $("salesOrders").textContent = fmtNum(result.totals.orders);
    salesChart = setChart(salesChart, "salesTrend", lineChart(
      result.trend.map((x) => x.month),
      [{label:"Revenue",data:result.trend.map((x)=>x.revenue),color:"#3579e8"},
       {label:"Profit",data:result.trend.map((x)=>x.profit),color:"#8b68df"}]
    ));
    renderRegionTable("salesRegions", result.regions);
    renderProductTable("salesProducts", result.products);
  } catch (error) {
    showToast("Could not load sales analytics: " + error.message, true);
  }
}

async function loadCustomers() {
  try {
    const params = new URLSearchParams();
    params.set("risk", $("customerRisk").value || "all");
    params.set("segment", $("customerSegment").value || "All");
    if ($("customerSearch").value.trim()) params.set("search", $("customerSearch").value.trim());
    const [rows, allRows, segments, summary] = await Promise.all([
      api("/api/customers?" + params.toString()),
      api("/api/customers?risk=all&segment=All"),
      api("/api/segments"),
      api("/api/summary")
    ]);
    $("customerTotal").textContent = fmtNum(allRows.length);
    $("customerHighRisk").textContent = fmtNum(summary.high_risk_customers);
    const avg = allRows.length ? allRows.reduce((sum, x) => sum + Number(x.satisfaction), 0) / allRows.length : 0;
    $("customerSatisfaction").textContent = avg.toFixed(1) + " / 5";
    $("customerCount").textContent = "Showing " + rows.length + " of " + allRows.length + " customers";
    $("customerTable").innerHTML = table([
      {key:"customer",label:"Customer"},
      {key:"segment",label:"Segment"},
      {key:"region",label:"Region"},
      {key:"orders",label:"Orders",render:(v)=>fmtNum(v)},
      {key:"revenue",label:"Revenue",render:(v)=>fmtMoney(v)},
      {key:"satisfaction",label:"Satisfaction",render:(v)=>Number(v).toFixed(1)+" / 5"},
      {key:"churn_risk",label:"Churn risk",render:(v)=>riskBadge(v)}
    ], rows, "No customers match these filters.");
    $("segmentsTable").innerHTML = table([
      {key:"segment",label:"Segment"},
      {key:"customers",label:"Customers",render:(v)=>fmtNum(v)},
      {key:"revenue",label:"Revenue",render:(v)=>fmtMoney(v)},
      {key:"avg_satisfaction",label:"Avg. satisfaction",render:(v)=>Number(v).toFixed(1)+" / 5"},
      {key:"avg_churn_risk",label:"Avg. risk",render:(v)=>fmtPct(v)}
    ], segments);
  } catch (error) {
    showToast("Could not load customer intelligence: " + error.message, true);
  }
}

async function loadInsights() {
  try {
    const result = await api("/api/insights");
    $("insightCards").innerHTML = result.insights.map((item, index) =>
      '<article class="insight-card"><div class="insight-number">0' + (index + 1) + '</div><span class="insight-status ' + esc(item.type) + '">' + esc(item.type) + '</span><h3>' + esc(item.title) + '</h3><p>' + esc(item.detail) + '</p></article>'
    ).join("");
    forecastChart = setChart(forecastChart, "insightForecast", {
      type:"bar",
      data:{labels:result.forecast.months,datasets:[{label:"Baseline forecast",data:result.forecast.values,backgroundColor:["#8b68df","#a48ae9","#b9a7f1"],borderRadius:6,maxBarThickness:46}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false}},y:{beginAtZero:true,grid:{color:"#edf1f6"},ticks:{callback:(v)=>"₹"+Math.round(v/1000)+"k"}}}}
    });
    $("insightAnomalies").innerHTML = table([
      {key:"date",label:"Date"},
      {key:"region",label:"Region"},
      {key:"product",label:"Product"},
      {key:"revenue",label:"Revenue",render:(v)=>fmtMoney(v)}
    ], result.anomalies, "No outliers returned.");
  } catch (error) {
    showToast("Could not load AI insights: " + error.message, true);
  }
}

function appendChat(who, message, pending = false) {
  const node = document.createElement("div");
  node.className = "chat-message " + (who === "user" ? "user-message" : "assistant-message") + (pending ? " pending" : "");
  const label = document.createElement("span");
  label.className = "chat-label";
  label.textContent = who === "user" ? "YOU" : "NEXUS ANALYST";
  const p = document.createElement("p");
  p.textContent = message;
  node.append(label, p);
  $("chatHistory").appendChild(node);
  $("chatHistory").scrollTop = $("chatHistory").scrollHeight;
  return node;
}

async function askAnalyst(question) {
  const q = String(question || "").trim();
  if (!q) return;
  appendChat("user", q);
  $("chatQuestion").value = "";
  const pending = appendChat("assistant", "Reviewing the business data…", true);
  try {
    const result = await api("/api/ask", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({question:q})
    });
    pending.classList.remove("pending");
    pending.querySelector("p").textContent = result.answer;
  } catch (error) {
    pending.classList.remove("pending");
    pending.querySelector("p").textContent = "Could not query the analytics API. " + error.message;
  }
  $("chatHistory").scrollTop = $("chatHistory").scrollHeight;
}

$("salesFilter").addEventListener("submit", (event) => { event.preventDefault(); loadSales(); });
$("resetSales").addEventListener("click", () => {
  $("salesStart").value = "2025-01-01";
  $("salesEnd").value = "2025-12-31";
  $("salesRegion").value = "All";
  $("salesProduct").value = "All";
  loadSales();
});
$("customerFilter").addEventListener("submit", (event) => { event.preventDefault(); loadCustomers(); });
$("resetCustomers").addEventListener("click", () => {
  $("customerSearch").value = "";
  $("customerRisk").value = "all";
  $("customerSegment").value = "All";
  loadCustomers();
});
$("refreshBtn").addEventListener("click", async () => {
  try {
    await loadOverview();
    if (currentView === "sales") await loadSales();
    if (currentView === "customers") await loadCustomers();
    if (currentView === "insights") await loadInsights();
    showToast("Dashboard data refreshed.");
  } catch (error) { showToast("Refresh failed: " + error.message, true); }
});
$("refreshInsights").addEventListener("click", loadInsights);
$("askForm").addEventListener("submit", (event) => {
  event.preventDefault();
  askAnalyst($("chatQuestion").value);
});
document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => askAnalyst(button.dataset.prompt));
});

async function boot() {
  try {
    await api("/api/health");
    await loadOverview();
    setInterval(() => {
      if (currentView === "overview") loadOverview().catch((e) => console.warn(e));
    }, 60000);
  } catch (error) {
    showToast("The app could not connect to its API: " + error.message, true);
    $("lastUpdated").textContent = "API connection failed";
  }
}
boot();
