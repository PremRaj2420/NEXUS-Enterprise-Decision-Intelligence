const $ = (id) => document.getElementById(id);
async function getJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed: ${url}`);
  return response.json();
}
const money = (value) => "₹" + Number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 });

async function loadDashboard() {
  try {
    const summary = await getJSON("/api/summary");
    $("revenue").textContent = money(summary.revenue);
    $("profit").textContent = money(summary.profit);
    $("orders").textContent = Number(summary.orders).toLocaleString("en-IN");
    $("margin").textContent = summary.margin + "%";

    const monthly = await getJSON("/api/monthly");
    new Chart($("trend"), {
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

    const forecast = await getJSON("/api/forecast");
    new Chart($("forecast"), {
      type: "bar",
      data: { labels: forecast.months, datasets: [{ label: "Forecast revenue", data: forecast.values }] },
      options: { responsive: true, maintainAspectRatio: false }
    });

    const regionRows = await getJSON("/api/regions");
    $("regions").innerHTML =
      '<div class="row head"><div>REGION</div><div>REVENUE</div><div>PROFIT</div><div>ORDERS</div></div>' +
      regionRows.map((row) => `<div class="row"><div>${row.region}</div><div>${money(row.revenue)}</div><div>${money(row.profit)}</div><div>${row.orders}</div></div>`).join("");

    const productRows = await getJSON("/api/products");
    $("products").innerHTML =
      '<div class="row head"><div>PRODUCT</div><div>REVENUE</div><div>PROFIT</div><div>UNITS</div></div>' +
      productRows.slice(0, 6).map((row) => `<div class="row"><div>${row.product}</div><div>${money(row.revenue)}</div><div>${money(row.profit)}</div><div>${row.quantity}</div></div>`).join("");

    const anomalyRows = await getJSON("/api/anomalies");
    $("anomalies").innerHTML =
      '<div class="row head"><div>DATE</div><div>REGION</div><div>PRODUCT</div><div>REVENUE</div></div>' +
      anomalyRows.map((row) => `<div class="row"><div>${row.date}</div><div>${row.region}</div><div>${row.product}</div><div>${money(row.revenue)}</div></div>`).join("");
  } catch (error) {
    console.error(error);
    $("answer").textContent = "Dashboard data could not be loaded. Check the Flask terminal for details.";
  }
}

async function askBusinessQuestion() {
  const question = $("question").value.trim();
  if (!question) return;
  $("answer").textContent = "Analyzing business data...";
  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });
    const result = await response.json();
    $("answer").textContent = result.answer;
  } catch (error) {
    $("answer").textContent = "Could not analyze that question. Check that the server is running.";
  }
}
$("askButton").addEventListener("click", askBusinessQuestion);
$("question").addEventListener("keydown", (event) => {
  if (event.key === "Enter") askBusinessQuestion();
});
loadDashboard();
