function formatKrw(value) {
  return `${Number(value || 0).toLocaleString("ko-KR")}원`;
}

function parseValues(raw) {
  return (raw || "")
    .split(",")
    .map((value) => Number(value.trim()))
    .filter((value) => Number.isFinite(value));
}

function setupCanvas(canvas) {
  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || canvas.width;
  const height = canvas.clientHeight || canvas.height;

  canvas.width = width * ratio;
  canvas.height = height * ratio;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  return { ctx, width, height };
}

function getChartState(canvas) {
  if (!canvas._chartState) {
    canvas._chartState = {};
  }
  return canvas._chartState;
}

function getTooltip() {
  let tooltip = document.querySelector(".chart-tooltip");
  if (!tooltip) {
    tooltip = document.createElement("div");
    tooltip.className = "chart-tooltip";
    document.body.appendChild(tooltip);
  }
  return tooltip;
}

function bindChartTooltip(canvas, payload, points, bounds) {
  if (!canvas || !points || points.length === 0) return;

  const state = getChartState(canvas);
  state.payload = payload;
  state.points = points;
  state.bounds = bounds;

  if (state.bound) return;
  state.bound = true;

  canvas.addEventListener("mousemove", (event) => {
    const current = getChartState(canvas);
    const tooltip = getTooltip();
    if (!current.points || current.points.length === 0) return;

    const rect = canvas.getBoundingClientRect();
    const localX = event.clientX - rect.left;
    let nearest = current.points[0];
    let nearestIndex = 0;
    let minDistance = Math.abs(localX - nearest.x);

    current.points.forEach((point, index) => {
      const distance = Math.abs(localX - point.x);
      if (distance < minDistance) {
        minDistance = distance;
        nearest = point;
        nearestIndex = index;
      }
    });

    drawDetailChart(canvas, current.payload, nearestIndex);

    const label = current.payload.labels?.[nearestIndex] || `${nearestIndex + 1}`;
    const price = current.payload.prices?.[nearestIndex] || 0;
    tooltip.textContent = `${label} · ${formatKrw(price)}`;
    tooltip.style.opacity = "1";
    tooltip.style.left = `${event.clientX + 14}px`;
    tooltip.style.top = `${event.clientY - 30}px`;
  });

  canvas.addEventListener("mouseleave", () => {
    const tooltip = getTooltip();
    tooltip.style.opacity = "0";
    const current = getChartState(canvas);
    drawDetailChart(canvas, current.payload);
  });
}

function drawLineChart(canvas, values) {
  if (!canvas || values.length === 0) return;

  const { ctx, width, height } = setupCanvas(canvas);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = 8;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;
  const range = max - min || 1;

  const points = values.map((value, index) => ({
    x: padding + (chartWidth * index) / Math.max(values.length - 1, 1),
    y: padding + chartHeight - ((value - min) / range) * chartHeight,
  }));

  const isUp = values.at(-1) >= values[0];
  const stroke = isUp ? "#f04452" : "#2f6fed";
  const fill = isUp ? "rgba(240, 68, 82, 0.12)" : "rgba(47, 111, 237, 0.12)";

  ctx.strokeStyle = stroke;
  ctx.fillStyle = fill;
  ctx.lineWidth = 2.25;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  ctx.beginPath();
  points.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(points[0].x, height - padding);
  points.forEach((point) => ctx.lineTo(point.x, point.y));
  ctx.lineTo(points.at(-1).x, height - padding);
  ctx.closePath();
  ctx.fill();
}

function drawDetailChart(canvas, payload, highlightedIndex = null) {
  const values = payload.prices || [];
  if (!canvas || values.length === 0) return;

  const { ctx, width, height } = setupCanvas(canvas);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const paddingTop = 28;
  const paddingBottom = 34;
  const paddingSide = 22;
  const chartWidth = width - paddingSide * 2;
  const chartHeight = height - paddingTop - paddingBottom;
  const range = max - min || 1;
  const isUp = values.at(-1) >= values[0];
  const stroke = isUp ? "#f04452" : "#2f6fed";
  const fill = isUp ? "rgba(240, 68, 82, 0.12)" : "rgba(47, 111, 237, 0.12)";

  for (let i = 0; i < 4; i += 1) {
    const y = paddingTop + (chartHeight / 3) * i;
    ctx.strokeStyle = "#e6ebf2";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(paddingSide, y);
    ctx.lineTo(width - paddingSide, y);
    ctx.stroke();
  }

  const points = values.map((value, index) => ({
    x: paddingSide + (chartWidth * index) / Math.max(values.length - 1, 1),
    y: paddingTop + chartHeight - ((value - min) / range) * chartHeight,
  }));

  ctx.strokeStyle = stroke;
  ctx.fillStyle = fill;
  ctx.lineWidth = 3;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  ctx.beginPath();
  points.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(points[0].x, height - paddingBottom);
  points.forEach((point) => ctx.lineTo(point.x, point.y));
  ctx.lineTo(points.at(-1).x, height - paddingBottom);
  ctx.closePath();
  ctx.fill();

  const labels = payload.labels || [];
  ctx.fillStyle = "#7e8796";
  ctx.font = '12px "Segoe UI", "Malgun Gothic", sans-serif';
  [0, Math.floor(labels.length / 2), labels.length - 1].forEach((index) => {
    if (labels[index]) {
      ctx.fillText(labels[index], points[index].x - 14, height - 10);
    }
  });

  ctx.fillStyle = stroke;
  ctx.font = '700 14px "Segoe UI", "Malgun Gothic", sans-serif';
  ctx.fillText(`${payload.stock} ${formatKrw(payload.current_price)}`, paddingSide, 18);

  if (highlightedIndex !== null && points[highlightedIndex]) {
    const activePoint = points[highlightedIndex];
    ctx.strokeStyle = "rgba(17, 24, 39, 0.22)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(activePoint.x, paddingTop);
    ctx.lineTo(activePoint.x, height - paddingBottom);
    ctx.stroke();

    ctx.fillStyle = stroke;
    ctx.beginPath();
    ctx.arc(activePoint.x, activePoint.y, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  bindChartTooltip(canvas, payload, points, { paddingTop, paddingBottom, paddingSide, width, height });
}

function updateLiveFields(payload) {
  const priceText = formatKrw(payload.current_price);
  const changePrefix = payload.change_amount >= 0 ? "+" : "";
  const ratePrefix = payload.change_rate >= 0 ? "+" : "";
  const changeText = `${changePrefix}${Number(payload.change_amount).toLocaleString("ko-KR")}원 (${ratePrefix}${payload.change_rate.toFixed(2)}%)`;
  const rateText = `${ratePrefix}${payload.change_rate.toFixed(2)}%`;
  const isUp = payload.change_amount >= 0;

  document.querySelectorAll("[data-live-price], [data-live-price-inline]").forEach((node) => {
    node.textContent = priceText;
  });

  document.querySelectorAll("[data-live-base]").forEach((node) => {
    const base = payload.prices.length > 1 ? payload.prices[payload.prices.length - 2] : payload.current_price;
    node.textContent = formatKrw(base);
  });

  document.querySelectorAll("[data-live-change], [data-live-rate]").forEach((node) => {
    node.textContent = node.hasAttribute("data-live-change") ? changeText : rateText;
    node.classList.remove("up", "down");
    node.classList.add(isUp ? "up" : "down");
  });
}

function updateHomePreview(payload) {
  const canvas = document.querySelector("[data-home-preview-chart]");
  if (!canvas) return;
  drawDetailChart(canvas, payload);

  document.querySelector("[data-preview-symbol]").textContent = payload.symbol;
  document.querySelector("[data-preview-name]").textContent = payload.stock;
  document.querySelector("[data-preview-price]").textContent = formatKrw(payload.current_price);

  const changeNode = document.querySelector("[data-preview-change]");
  const prefix = payload.change_amount >= 0 ? "+" : "";
  changeNode.textContent = `${prefix}${Number(payload.change_amount).toLocaleString("ko-KR")}원 (${prefix}${payload.change_rate.toFixed(2)}%)`;
  changeNode.classList.remove("up", "down");
  changeNode.classList.add(payload.change_amount >= 0 ? "up" : "down");
  document.querySelector("[data-preview-link]").href = payload.detail_url;
  canvas.dataset.previewPayload = JSON.stringify(payload);
}

async function hydrateDetailChart() {
  const canvas = document.querySelector("[data-stock-chart]");
  if (!canvas) return;

  const endpoint = canvas.dataset.endpoint;
  if (!endpoint) return;

  const refresh = async () => {
    try {
      const response = await fetch(endpoint, { cache: "no-store" });
      if (!response.ok) return;
      const payload = await response.json();
      drawDetailChart(canvas, payload);
      updateLiveFields(payload);
    } catch (_) {
      return;
    }
  };

  await refresh();
  window.addEventListener("resize", refresh);
  setInterval(refresh, 5000);
}

function hydrateHomePreview() {
  const canvas = document.querySelector("[data-home-preview-chart]");
  const rows = document.querySelectorAll("[data-stock-preview]");
  if (!canvas || rows.length === 0) return;

  rows.forEach((row) => {
    row.addEventListener("mouseenter", (event) => {
      rows.forEach((item) => item.classList.remove("is-active"));
      event.currentTarget.classList.add("is-active");
      updateHomePreview(JSON.parse(event.currentTarget.dataset.stockPreview));
    });
  });

  updateHomePreview(JSON.parse(canvas.dataset.previewPayload));
}

function renderMarketRow(row, stock) {
  row.href = stock.detail_url;
  row.dataset.stockPreview = stock.preview_json;
  row.dataset.stockId = stock.id;
  row.querySelector("[data-market-name]").textContent = stock.name;
  row.querySelector("[data-market-symbol]").textContent = stock.symbol;
  row.querySelector("[data-market-price]").textContent = formatKrw(stock.current_price);
  const rateNode = row.querySelector("[data-market-rate]");
  const prefix = stock.change_rate >= 0 ? "+" : "";
  rateNode.textContent = `${prefix}${Number(stock.change_rate).toFixed(2)}%`;
  rateNode.classList.remove("up", "down");
  rateNode.classList.add(stock.change_amount >= 0 ? "up" : "down");
}

function renderTickerCard(card, stock) {
  card.href = stock.detail_url;
  card.dataset.stockId = stock.id;
  card.querySelector("[data-ticker-name]").textContent = stock.name;
  card.querySelector("[data-ticker-symbol]").textContent = stock.symbol;
  card.querySelector("[data-ticker-price]").textContent = formatKrw(stock.current_price);
  const rateNode = card.querySelector("[data-ticker-rate]");
  const prefix = stock.change_rate >= 0 ? "+" : "";
  rateNode.textContent = `${prefix}${Number(stock.change_rate).toFixed(2)}%`;
  rateNode.classList.remove("up", "down");
  rateNode.classList.add(stock.change_amount >= 0 ? "up" : "down");
}

function renderAccountRow(row, stock) {
  row.href = `/stocks/${stock.id}`;
  row.querySelector("[data-account-name]").textContent = stock.name;
  row.querySelector("[data-account-qty]").textContent = `${stock.quantity}주`;
  row.querySelector("[data-account-value]").textContent = formatKrw(stock.current_value);
  const profitNode = row.querySelector("[data-account-profit]");
  const prefix = stock.profit >= 0 ? "+" : "";
  profitNode.textContent = `${prefix}${Number(stock.profit).toLocaleString("ko-KR")}원`;
  profitNode.classList.remove("up", "down");
  profitNode.classList.add(stock.profit >= 0 ? "up" : "down");
}

function renderOrderRow(row, item) {
  row.querySelector("[data-order-type]").textContent = item.display_type;
  row.querySelector("[data-order-meta]").textContent = item.meta;
}

async function hydrateMarketSnapshot() {
  const endpointNode = document.querySelector("#market-snapshot-endpoint");
  if (!endpointNode) return;

  const endpoint = endpointNode.textContent.trim();
  if (!endpoint) return;

  const refresh = async () => {
    try {
      const response = await fetch(endpoint, { cache: "no-store" });
      if (!response.ok) return;
      const payload = await response.json();

      document.querySelectorAll("[data-ticker-card]").forEach((card, index) => {
        if (payload.stocks[index]) renderTickerCard(card, payload.stocks[index]);
      });

      document.querySelectorAll("[data-market-row]").forEach((row, index) => {
        if (payload.stocks[index]) renderMarketRow(row, payload.stocks[index]);
      });

      const cashNode = document.querySelector("[data-cash-balance]");
      const stockNode = document.querySelector("[data-stock-balance]");
      const totalNode = document.querySelector("[data-total-assets]");
      if (cashNode) cashNode.textContent = formatKrw(payload.cash_balance);
      if (stockNode) stockNode.textContent = formatKrw(payload.total_stock_value);
      if (totalNode) totalNode.textContent = formatKrw(payload.total_assets);

      document.querySelectorAll("[data-account-row]").forEach((row, index) => {
        if (payload.account_stocks[index]) renderAccountRow(row, payload.account_stocks[index]);
      });

      document.querySelectorAll("[data-order-row]").forEach((row, index) => {
        if (payload.recent_transactions[index]) renderOrderRow(row, payload.recent_transactions[index]);
      });

      const activeRow = document.querySelector("[data-market-row].is-active") || document.querySelector("[data-market-row]");
      if (activeRow) {
        const activeId = Number(activeRow.dataset.stockId);
        const activeStock = payload.stocks.find((stock) => stock.id === activeId) || payload.stocks[0];
        if (activeStock) updateHomePreview(JSON.parse(activeStock.preview_json));
      }
    } catch (_) {
      return;
    }
  };

  await refresh();
  setInterval(refresh, 5000);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((item) => {
    setTimeout(() => {
      item.style.opacity = "0";
      item.style.transition = "opacity 0.3s ease";
    }, 2500);
  });

  document.querySelectorAll(".sparkline").forEach((canvas) => {
    drawLineChart(canvas, parseValues(canvas.dataset.values));
  });

  hydrateHomePreview();
  hydrateDetailChart();
  hydrateMarketSnapshot();
});
