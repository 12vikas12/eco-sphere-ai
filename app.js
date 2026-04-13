/* ─── EcoSphere Frontend JS ─── */
const API_BASE = "http://localhost:5000/api";

const PASTEL_COLORS = [
  "#B8D4F5", "#D4C5F5", "#F5E6B8", "#B8F5D4",
  "#C5F5B8", "#F5C5B8", "#F5D4B8", "#F5B8E6",
  "#C5C5F5", "#F5D8B8"
];

const WASTE_ICONS = {
  Plastic: "🧴", Metal: "🔩", Paper: "📄", Glass: "🍶",
  Organic: "🌿", "E-Waste": "💻", Cardboard: "📦",
  Textile: "👕", Rubber: "⭕", Wood: "🪵"
};

// ─── Drag & Drop ───
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById("drop-zone").classList.add("drag-active");
}

function handleDragLeave(e) {
  document.getElementById("drop-zone").classList.remove("drag-active");
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById("drop-zone").classList.remove("drag-active");
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) processFile(file);
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) processFile(file);
}

function processFile(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const fullBase64 = e.target.result;
    const base64Data = fullBase64.split(",")[1];
    showLoading();
    analyzeWaste(base64Data, file.name, fullBase64);
  };
  reader.readAsDataURL(file);
}

// ─── UI State ───
function showLoading() {
  hide("upload-section");
  hide("results-section");
  hide("error-section");
  show("loading-section");
  // Reset and restart progress animation
  const fill = document.getElementById("progress-fill");
  if (fill) { fill.style.animation = "none"; fill.offsetHeight; fill.style.animation = ""; }
}

function showResults() {
  hide("upload-section");
  hide("loading-section");
  hide("error-section");
  show("results-section");
}

function showError(msg) {
  hide("upload-section");
  hide("loading-section");
  hide("results-section");
  show("error-section");
  const el = document.getElementById("error-message");
  if (el) el.textContent = msg || "Something went wrong. Please try again.";
}

function resetApp() {
  hide("results-section");
  hide("error-section");
  hide("loading-section");
  show("upload-section");
  const fi = document.getElementById("file-input");
  if (fi) fi.value = "";
}

function show(id) { const el = document.getElementById(id); if (el) el.classList.remove("hidden"); }
function hide(id) { const el = document.getElementById(id); if (el) el.classList.add("hidden"); }

// ─── API Call ───
async function analyzeWaste(base64Data, filename, fullBase64) {
  try {
    const res = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ imageBase64: base64Data, filename })
    });

    if (!res.ok) {
      const err = await res.json();
      showError(err.message || "Analysis failed");
      return;
    }

    const data = await res.json();
    displayResults(data, fullBase64);
  } catch (err) {
    showError("Could not connect to server. Make sure the backend is running on port 5000.");
  }
}

// ─── Display Results ───
function displayResults(data, originalImage) {
  // Image
  const imgEl = document.getElementById("result-image");
  imgEl.src = data.boundingBoxImage || originalImage;

  // Badge + time
  const badge = document.getElementById("items-badge");
  if (badge) badge.textContent = `${data.totalDetected} Item${data.totalDetected !== 1 ? "s" : ""} Found`;
  const timeEl = document.getElementById("analysis-time");
  if (timeEl) timeEl.textContent = `Analyzed in ${data.analysisTime}s`;

  // Earning
  const earningEl = document.getElementById("estimated-earning");
  if (earningEl) earningEl.textContent = data.estimatedEarning;

  // Detections
  const grid = document.getElementById("detections-grid");
  grid.innerHTML = "";
  data.detections.forEach((det, i) => {
    const color = det.color || PASTEL_COLORS[i % PASTEL_COLORS.length];
    const icon = WASTE_ICONS[det.type] || "♻️";
    const pct = Math.round(det.confidence * 100);
    const card = document.createElement("div");
    card.className = "detection-card";
    card.style.animationDelay = `${i * 0.1}s`;
    card.innerHTML = `
      <div class="detection-icon" style="background: ${color}40">
        <span style="font-size: 1.5rem">${icon}</span>
      </div>
      <div class="detection-info">
        <div class="detection-name">
          <span>${det.type}</span>
          <span class="detection-price">₹${det.pricePerKg}/kg</span>
        </div>
        <div class="confidence-row">
          <span>Confidence</span>
          <span>${pct}%</span>
        </div>
        <div class="progress">
          <div class="progress-bar-inner" style="width: ${pct}%; background: ${color}"></div>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });

  // Recommendations
  const recEl = document.getElementById("recommendations");
  recEl.innerHTML = "";
  const recParts = data.recommendation.split("\n\n");
  recParts.forEach(part => {
    const colonIdx = part.indexOf(":");
    const div = document.createElement("div");
    div.className = "rec-item";
    if (colonIdx > -1) {
      const type = part.slice(0, colonIdx).replace(/\*\*/g, "").trim();
      const text = part.slice(colonIdx + 1).trim();
      div.innerHTML = `<span class="rec-type">${type}</span>${text}`;
    } else {
      div.textContent = part.replace(/\*\*/g, "");
    }
    recEl.appendChild(div);
  });

  // Centers
  const centersList = document.getElementById("centers-list");
  centersList.innerHTML = "";
  (data.recyclingCenters || []).slice(0, 3).forEach(c => {
    const item = document.createElement("div");
    item.className = "center-item";
    const typesHtml = c.supportedTypes.slice(0, 2).map(t => `<span class="waste-badge">${t}</span>`).join("");
    const extra = c.supportedTypes.length > 2 ? `<span class="waste-badge">+${c.supportedTypes.length - 2}</span>` : "";
    item.innerHTML = `
      <div class="center-info">
        <h4>${c.name}</h4>
        <p class="center-city"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>${c.city}</p>
      </div>
      <div class="center-badges">${typesHtml}${extra}</div>
    `;
    centersList.appendChild(item);
  });

  showResults();
}

// ─── Centers Page ───
let allCenters = [];

async function loadAllCenters() {
  try {
    const res = await fetch(`${API_BASE}/recycling-centers`);
    const data = await res.json();
    allCenters = data.centers || [];
    renderCenters(allCenters);
  } catch (err) {
    const grid = document.getElementById("centers-grid");
    if (grid) grid.innerHTML = `<p style="color: #dc2626; text-align: center; padding: 2rem">Could not load centers. Make sure backend is running on port 5000.</p>`;
  }
}

function filterCenters() {
  const query = (document.getElementById("search-input")?.value || "").toLowerCase();
  const wasteType = document.getElementById("waste-filter")?.value || "";
  const filtered = allCenters.filter(c => {
    const matchSearch = !query ||
      c.name.toLowerCase().includes(query) ||
      c.city.toLowerCase().includes(query) ||
      c.address.toLowerCase().includes(query);
    const matchType = !wasteType || c.supportedTypes.includes(wasteType);
    return matchSearch && matchType;
  });
  renderCenters(filtered);
}

function renderCenters(centers) {
  const grid = document.getElementById("centers-grid");
  if (!grid) return;
  if (centers.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 4rem; background: white; border-radius: 24px;">
        <p style="color: var(--text-muted); font-size: 1rem">No centers found. Try adjusting your search or filter.</p>
      </div>`;
    return;
  }
  grid.innerHTML = "";
  centers.forEach((c, i) => {
    const card = document.createElement("div");
    card.className = "center-card";
    card.style.animationDelay = `${i * 0.05}s`;
    const typeBadges = c.supportedTypes.map(t => `<span class="waste-badge">${t}</span>`).join("");
    card.innerHTML = `
      <div class="center-card-top-bar"></div>
      <div class="center-card-body">
        <div class="center-card-header">
          <h3>${c.name}</h3>
          <div class="star-badge">
            <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            ${c.rating}
          </div>
        </div>
        <div class="center-city-tag">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
          ${c.city}
        </div>
        <div class="center-detail">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
          ${c.address}
        </div>
        <div class="center-detail">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.99 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.92 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 8.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
          ${c.phone}
        </div>
        <div class="center-detail">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          ${c.operatingHours}
        </div>
        <div class="supported-types">
          <p>Supported Materials:</p>
          <div class="type-badges">${typeBadges}</div>
        </div>
      </div>
      <div class="center-card-footer">
        <button class="btn btn-outline" style="width: 100%">Get Directions</button>
      </div>
    `;
    grid.appendChild(card);
  });
}

// ─── Stats Page ───
async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/waste-stats`);
    const stats = await res.json();
    renderStats(stats);
  } catch (err) {
    const cards = document.getElementById("stats-cards");
    if (cards) cards.innerHTML = `<p style="color: #dc2626">Could not load stats. Make sure backend is running on port 5000.</p>`;
  }
}

function renderStats(stats) {
  // Summary cards
  const cardsEl = document.getElementById("stats-cards");
  if (cardsEl) {
    cardsEl.innerHTML = `
      <div class="stat-card">
        <div class="stat-header">
          <div>
            <p class="stat-label">Total Detections</p>
            <div class="stat-value">${stats.totalDetections.toLocaleString()}</div>
          </div>
          <div class="stat-icon green">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
          </div>
        </div>
        <p class="stat-footnote"><span class="stat-badge">+12%</span> from last month</p>
      </div>
      <div class="stat-card">
        <div class="stat-header">
          <div>
            <p class="stat-label">Avg. Earning / Drop</p>
            <div class="stat-value">₹${stats.averageEarning}</div>
          </div>
          <div class="stat-icon purple">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/></svg>
          </div>
        </div>
        <p class="stat-footnote">Based on recent community data</p>
      </div>
      <div class="stat-card">
        <div class="stat-header">
          <div>
            <p class="stat-label">Top Earning Material</p>
            <div class="stat-value" style="font-size: 1.75rem">${stats.topEarningWaste}</div>
          </div>
          <div class="stat-icon orange">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>
          </div>
        </div>
        <p class="stat-footnote">Currently in high demand</p>
      </div>
    `;
  }

  // Pie Chart
  const pieCtx = document.getElementById("pie-chart");
  if (pieCtx && stats.popularWasteTypes) {
    const colors = stats.popularWasteTypes.map((_, i) => PASTEL_COLORS[i % PASTEL_COLORS.length]);
    new Chart(pieCtx.getContext("2d"), {
      type: "doughnut",
      data: {
        labels: stats.popularWasteTypes.map(w => w.type),
        datasets: [{
          data: stats.popularWasteTypes.map(w => w.count),
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: "#fff"
        }]
      },
      options: {
        responsive: true,
        cutout: "65%",
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const item = stats.popularWasteTypes[ctx.dataIndex];
                return ` ${item.count} scans (${item.percentage}%)`;
              }
            }
          }
        }
      }
    });

    // Legend
    const legendEl = document.getElementById("pie-legend");
    if (legendEl) {
      legendEl.innerHTML = stats.popularWasteTypes.map((w, i) => `
        <div class="pie-legend-item">
          <div class="legend-dot" style="background: ${colors[i]}"></div>
          <span>${w.type}</span>
        </div>
      `).join("");
    }
  }

  // Bar Chart
  const barCtx = document.getElementById("bar-chart");
  if (barCtx && stats.popularWasteTypes) {
    const colors = stats.popularWasteTypes.map((_, i) => PASTEL_COLORS[i % PASTEL_COLORS.length]);
    new Chart(barCtx.getContext("2d"), {
      type: "bar",
      data: {
        labels: stats.popularWasteTypes.map(w => w.type),
        datasets: [{
          label: "Detections",
          data: stats.popularWasteTypes.map(w => w.count),
          backgroundColor: colors,
          borderRadius: 8,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { family: "Inter", size: 11 }, color: "#7a9a85" } },
          y: { grid: { color: "#e2ede7" }, ticks: { font: { family: "Inter", size: 11 }, color: "#7a9a85" }, border: { display: false } }
        }
      }
    });
  }
}
