function formatKrw(value) {
  return `${Number(value || 0).toLocaleString("ko-KR")}원`;
}

function parseValues(raw) {
  return (raw || "")
    .split(",")
    .map((value) => Number(value.trim()))
    .filter((value) => Number.isFinite(value));
}

function parseLabels(raw) {
  return (raw || "")
    .split(",")
    .map((value) => value.trim())
    .filter((value) => value.length > 0);
}

function parseChartTimestamp(timestamp) {
  if (!timestamp) return Number.NaN;
  return new Date(`${String(timestamp).trim().replace(" ", "T")}Z`).getTime();
}

function formatClock(timestamp, withSeconds = true) {
  const date = new Date(parseChartTimestamp(timestamp));
  if (Number.isNaN(date.getTime())) return withSeconds ? "지금" : "방금";
  return new Intl.DateTimeFormat("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    second: withSeconds ? "2-digit" : undefined,
    hour12: false,
    timeZone: "Asia/Seoul",
  }).format(date);
}

function getChartState(canvas) {
  if (!canvas._chartState) {
    canvas._chartState = {};
  }
  return canvas._chartState;
}

function resetCanvasLayout(canvas) {
  const state = getChartState(canvas);
  delete state.layoutWidth;
  delete state.layoutHeight;
}

function setupCanvas(canvas) {
  const state = getChartState(canvas);
  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;

  if (!state.layoutWidth || !state.layoutHeight) {
    const rect = canvas.getBoundingClientRect();
    const fallbackWidth = Number(canvas.dataset.layoutWidth || canvas.getAttribute("width")) || canvas.clientWidth || canvas.width || 1;
    const fallbackHeight = Number(canvas.dataset.layoutHeight || canvas.getAttribute("height")) || canvas.clientHeight || canvas.height || 1;
    const useResponsiveSize = canvas.dataset.responsive === "true";

    state.layoutWidth = Math.max(Math.round(useResponsiveSize ? (rect.width || fallbackWidth) : fallbackWidth), 1);
    state.layoutHeight = Math.max(Math.round(useResponsiveSize ? (rect.height || fallbackHeight) : fallbackHeight), 1);
  }

  const width = state.layoutWidth;
  const height = state.layoutHeight;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  canvas.dataset.layoutWidth = String(width);
  canvas.dataset.layoutHeight = String(height);

  if (canvas.width !== width * ratio || canvas.height !== height * ratio) {
    canvas.width = width * ratio;
    canvas.height = height * ratio;
  }

  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  return { ctx, width, height };
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

function buildRangePayload(payload, intervalSeconds) {
  const prices = payload.prices || [];
  const timestamps = payload.timestamps || [];
  if (!timestamps.length || !prices.length || !intervalSeconds) {
    return {
      ...payload,
      labels: payload.labels || [],
      latest_time_label: payload.latest_time_label || payload.labels?.at(-1) || "지금",
    };
  }

  const parsed = timestamps.map((value) => parseChartTimestamp(value));
  const entries = parsed
    .map((time, index) => ({
      time,
      price: Number(prices[index]),
      timestamp: timestamps[index],
    }))
    .filter((entry) => Number.isFinite(entry.time) && Number.isFinite(entry.price));

  if (!entries.length) {
    return {
      ...payload,
      labels: payload.labels || [],
      latest_time_label: payload.latest_time_label || payload.labels?.at(-1) || "지금",
    };
  }

  const sampled = [];
  let lastIncluded = Number.NEGATIVE_INFINITY;
  const intervalMs = intervalSeconds * 1000;

  entries.forEach((entry) => {
    if (sampled.length === 0 || entry.time - lastIncluded >= intervalMs) {
      sampled.push(entry);
      lastIncluded = entry.time;
    }
  });

  const latestEntry = entries.at(-1);
  if (sampled.at(-1)?.time !== latestEntry.time) {
    sampled.push(latestEntry);
  }

  if (sampled.length === 1 && entries.length > 1) {
    sampled.unshift(entries[0]);
  }

  const sampledPrices = sampled.map((entry) => entry.price);
  const sampledTimes = sampled.map((entry) => entry.timestamp);
  const useSeconds = intervalSeconds <= 60;
  const labels = sampledTimes.map((value) => formatClock(value, useSeconds));

  return {
    ...payload,
    prices: sampledPrices,
    timestamps: sampledTimes,
    labels,
    latest_time_label: labels.at(-1) || payload.latest_time_label || "지금",
  };
}

function setRangeButtons(group, activeRange) {
  group.querySelectorAll("[data-chart-range]").forEach((button) => {
    button.classList.toggle("is-active", Number(button.dataset.chartRange) === Number(activeRange));
  });
}

function bindChartTooltip(canvas, payload, points, redraw) {
  if (!canvas || !points || points.length === 0) return;

  const state = getChartState(canvas);
  state.payload = payload;
  state.points = points;
  state.redraw = redraw;

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

    if (current.highlightedIndex !== nearestIndex && typeof current.redraw === "function") {
      current.highlightedIndex = nearestIndex;
      current.redraw(canvas, current.payload, nearestIndex);
    }

    const label = current.payload.labels?.[nearestIndex] || formatClock(current.payload.timestamps?.[nearestIndex], true);
    const price = current.payload.prices?.[nearestIndex] || 0;
    tooltip.textContent = `${label || "지금"} · ${formatKrw(price)}`;
    tooltip.style.opacity = "1";
    tooltip.style.left = `${event.clientX + 14}px`;
    tooltip.style.top = `${event.clientY - 30}px`;
  });

  canvas.addEventListener("mouseleave", () => {
    const tooltip = getTooltip();
    tooltip.style.opacity = "0";
    const current = getChartState(canvas);
    current.highlightedIndex = null;
    if (typeof current.redraw === "function") {
      current.redraw(canvas, current.payload);
    }
  });
}

function drawCompactChart(canvas, payload, highlightedIndex = null) {
  const values = payload.prices || [];
  if (!canvas || values.length === 0) return;

  const { ctx, width, height } = setupCanvas(canvas);
  const min = Math.min(...values, Number.isFinite(payload.avg_price) ? payload.avg_price : Number.POSITIVE_INFINITY);
  const max = Math.max(...values, Number.isFinite(payload.avg_price) ? payload.avg_price : Number.NEGATIVE_INFINITY);
  const paddingTop = 10;
  const paddingBottom = payload.show_labels ? 22 : 10;
  const paddingSide = 8;
  const chartWidth = width - paddingSide * 2;
  const chartHeight = height - paddingTop - paddingBottom;
  const range = max - min || 1;
  const isUp = values.at(-1) >= values[0];
  const stroke = isUp ? "#f04452" : "#2f6fed";
  const fill = isUp ? "rgba(240, 68, 82, 0.12)" : "rgba(47, 111, 237, 0.12)";

  const points = values.map((value, index) => ({
    x: paddingSide + (chartWidth * index) / Math.max(values.length - 1, 1),
    y: paddingTop + chartHeight - ((value - min) / range) * chartHeight,
  }));

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
  ctx.moveTo(points[0].x, height - paddingBottom);
  points.forEach((point) => ctx.lineTo(point.x, point.y));
  ctx.lineTo(points.at(-1).x, height - paddingBottom);
  ctx.closePath();
  ctx.fill();

  if (Number.isFinite(payload.avg_price)) {
    const avgY = paddingTop + chartHeight - ((payload.avg_price - min) / range) * chartHeight;
    ctx.strokeStyle = "rgba(17, 24, 39, 0.62)";
    ctx.setLineDash([4, 4]);
    ctx.lineWidth = 1.25;
    ctx.beginPath();
    ctx.moveTo(paddingSide, avgY);
    ctx.lineTo(width - paddingSide, avgY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#111827";
    ctx.font = '700 11px "Segoe UI", "Malgun Gothic", sans-serif';
    ctx.fillText(`AVG ${formatKrw(payload.avg_price)}`, paddingSide, Math.max(avgY - 6, 11));
  }

  if (payload.show_labels) {
    const labels = payload.labels || [];
    ctx.fillStyle = "#7e8796";
    ctx.font = '11px "Segoe UI", "Malgun Gothic", sans-serif';
    [0, Math.floor(labels.length / 2), labels.length - 1].forEach((index) => {
      if (labels[index] && points[index]) {
        ctx.fillText(labels[index], Math.max(points[index].x - 16, 4), height - 6);
      }
    });
  }

  if (highlightedIndex !== null && points[highlightedIndex]) {
    const activePoint = points[highlightedIndex];
    ctx.strokeStyle = "rgba(17, 24, 39, 0.18)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(activePoint.x, paddingTop);
    ctx.lineTo(activePoint.x, height - paddingBottom);
    ctx.stroke();

    ctx.fillStyle = stroke;
    ctx.beginPath();
    ctx.arc(activePoint.x, activePoint.y, 3, 0, Math.PI * 2);
    ctx.fill();
  }

  if (canvas.dataset.tooltip !== "false") {
    bindChartTooltip(canvas, payload, points, drawCompactChart);
  }
}

function drawDetailChart(canvas, payload, highlightedIndex = null) {
  const values = payload.prices || [];
  if (!canvas || values.length === 0) return;

  const { ctx, width, height } = setupCanvas(canvas);
  const avgPrice = Number(payload.avg_price);
  const hasAvgPrice = Number.isFinite(avgPrice) && avgPrice > 0;
  const min = Math.min(...values, hasAvgPrice ? avgPrice : Number.POSITIVE_INFINITY);
  const max = Math.max(...values, hasAvgPrice ? avgPrice : Number.NEGATIVE_INFINITY);
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

  if (hasAvgPrice) {
    const avgY = paddingTop + chartHeight - ((avgPrice - min) / range) * chartHeight;
    ctx.strokeStyle = "rgba(17, 24, 39, 0.62)";
    ctx.setLineDash([6, 5]);
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(paddingSide, avgY);
    ctx.lineTo(width - paddingSide, avgY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#111827";
    ctx.font = '700 12px "Segoe UI", "Malgun Gothic", sans-serif';
    ctx.fillText(`AVG ${formatKrw(avgPrice)}`, paddingSide + 6, Math.max(avgY - 8, paddingTop + 12));
  }

  const labels = payload.labels || [];
  ctx.fillStyle = "#7e8796";
  ctx.font = '12px "Segoe UI", "Malgun Gothic", sans-serif';
  [0, Math.floor(labels.length / 2), labels.length - 1].forEach((index) => {
    if (labels[index] && points[index]) {
      ctx.fillText(labels[index], points[index].x - 18, height - 10);
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

  bindChartTooltip(canvas, payload, points, drawDetailChart);
}

function renderManagedChart(canvas, rawPayload) {
  if (!canvas || !rawPayload) return;
  const interval = Number(canvas.dataset.range || 0);
  const derived = buildRangePayload(rawPayload, interval);
  const avgPrice = Number(canvas.dataset.avgPrice);
  if (Number.isFinite(avgPrice) && avgPrice > 0) {
    derived.avg_price = avgPrice;
  }
  const state = getChartState(canvas);
  state.rawPayload = rawPayload;
  state.activeRange = interval;
  state.payload = derived;
  state.highlightedIndex = null;
  drawDetailChart(canvas, derived);
}

function buildMiniPayload(canvas) {
  return {
    stock: canvas.dataset.stockName || "",
    current_price: Number(canvas.dataset.currentPrice || 0),
    avg_price: canvas.dataset.avgPrice ? Number(canvas.dataset.avgPrice) : undefined,
    prices: parseValues(canvas.dataset.values),
    labels: parseLabels(canvas.dataset.labels),
    timestamps: parseLabels(canvas.dataset.timestamps),
    show_labels: canvas.hasAttribute("data-show-mini-labels"),
  };
}

function renderMiniManagedChart(canvas) {
  if (!canvas) return;
  const rawPayload = buildMiniPayload(canvas);
  const interval = Number(canvas.dataset.range || 0);
  const derived = buildRangePayload(rawPayload, interval);
  const state = getChartState(canvas);
  state.rawPayload = rawPayload;
  state.activeRange = interval;
  state.payload = { ...derived, avg_price: rawPayload.avg_price, show_labels: rawPayload.show_labels };
  state.highlightedIndex = null;
  drawCompactChart(canvas, state.payload);
}

function redrawMiniCharts(selector) {
  document.querySelectorAll(selector).forEach((canvas) => {
    resetCanvasLayout(canvas);
    renderMiniManagedChart(canvas);
  });
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

  document.querySelectorAll("[data-live-updated-at]").forEach((node) => {
    node.textContent = payload.latest_time_label || formatClock(payload.timestamps?.at(-1), true);
  });

  updateTradeForms(payload.current_price);
}

function updateHomePreview(payload) {
  const canvas = document.querySelector("[data-home-preview-chart]");
  if (!canvas) return;
  renderManagedChart(canvas, payload);

  document.querySelector("[data-preview-symbol]").textContent = payload.symbol;
  document.querySelector("[data-preview-name]").textContent = payload.stock;
  document.querySelector("[data-preview-price]").textContent = formatKrw(payload.current_price);

  const changeNode = document.querySelector("[data-preview-change]");
  const prefix = payload.change_amount >= 0 ? "+" : "";
  changeNode.textContent = `${prefix}${Number(payload.change_amount).toLocaleString("ko-KR")}원 (${prefix}${payload.change_rate.toFixed(2)}%)`;
  changeNode.classList.remove("up", "down");
  changeNode.classList.add(payload.change_amount >= 0 ? "up" : "down");
  document.querySelector("[data-preview-link]").href = payload.detail_url;

  const updatedAtNode = document.querySelector("[data-preview-updated-at]");
  if (updatedAtNode) {
    updatedAtNode.textContent = payload.latest_time_label || formatClock(payload.timestamps?.at(-1), true);
  }

  const newsBox = document.querySelector("[data-preview-news]");
  if (newsBox) {
    const heading = newsBox.querySelector("[data-preview-news-heading]");
    const symbol = newsBox.querySelector("[data-preview-news-symbol]");
    if (heading) heading.textContent = `${payload.stock} 이슈`;
    if (symbol) symbol.textContent = payload.symbol || "";

    const cards = Array.from(newsBox.querySelectorAll("[data-preview-news-card]"));
    const newsItems = payload.news_items || [];
    cards.forEach((card, index) => {
      const item = newsItems[index];
      card.style.display = item ? "" : "none";
      if (!item) return;
      card.querySelector("strong").textContent = item.title;
      card.querySelector("p").textContent = item.summary;
      card.querySelector("span").textContent = item.source;
    });
  }

  canvas.dataset.previewPayload = JSON.stringify(payload);
}

function bindRangeControls() {
  document.querySelectorAll("[data-chart-range-group]").forEach((group) => {
    const targetSelector = group.dataset.target;
    const canvas = targetSelector ? document.querySelector(targetSelector) : null;
    if (!canvas) return;

    group.querySelectorAll("[data-chart-range]").forEach((button) => {
      button.addEventListener("click", () => {
        canvas.dataset.range = button.dataset.chartRange;
        setRangeButtons(group, button.dataset.chartRange);
        const state = getChartState(canvas);
        if (state.rawPayload) {
          renderManagedChart(canvas, state.rawPayload);
        }
      });
    });

    setRangeButtons(group, canvas.dataset.range || 0);
  });
}

function bindMiniRangeControls() {
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-mini-range-group] [data-chart-range]");
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();

    const group = button.closest("[data-mini-range-group]");
    const selector = group?.dataset.targetSelector;
    if (!selector) return;

    setRangeButtons(group, button.dataset.chartRange);
    document.querySelectorAll(selector).forEach((canvas) => {
      canvas.dataset.range = button.dataset.chartRange;
      renderMiniManagedChart(canvas);
    });
  });

  document.querySelectorAll("[data-mini-range-group]").forEach((group) => {
    const selector = group.dataset.targetSelector;
    const activeRange = group.dataset.defaultRange || "10";
    setRangeButtons(group, activeRange);
    document.querySelectorAll(selector).forEach((canvas) => {
      canvas.dataset.range = activeRange;
    });
  });
}

function bindTickerCarousel() {
  const row = document.querySelector("[data-home-stocks]");
  const viewport = row?.closest(".ticker-viewport");
  const shell = row?.closest(".ticker-shell");
  const prev = document.querySelector("[data-ticker-prev]");
  const next = document.querySelector("[data-ticker-next]");
  const cards = Array.from(document.querySelectorAll("[data-ticker-card]"));
  if (!row || !viewport || !shell || !prev || !next || cards.length === 0) return;

  const getVisibleCount = () => {
    if (window.matchMedia("(max-width: 820px)").matches) return 1;
    if (window.matchMedia("(max-width: 1280px)").matches) return 2;
    return 5;
  };

  const render = () => {
    const visibleCount = getVisibleCount();
    const maxOffset = Math.max(cards.length - visibleCount, 0);
    const offset = Math.min(Math.max(Number(row.dataset.tickerOffset || 0), 0), maxOffset);
    row.dataset.tickerOffset = String(offset);
    const gap = Number.parseFloat(window.getComputedStyle(row).columnGap || window.getComputedStyle(row).gap || "0") || 0;
    const cardWidth = Math.max((viewport.clientWidth - gap * (visibleCount - 1)) / visibleCount, 1);
    row.style.setProperty("--ticker-card-width", `${cardWidth}px`);
    const shift = offset * (cardWidth + gap);
    row.style.transform = `translateX(-${shift}px)`;
    prev.disabled = offset === 0;
    next.disabled = offset === maxOffset;
  };

  const move = (delta) => {
    row.dataset.tickerOffset = String(Number(row.dataset.tickerOffset || 0) + delta);
    render();
  };

  shell.addEventListener("click", (event) => {
    const button = event.target.closest("[data-ticker-prev], [data-ticker-next]");
    if (!button || button.disabled) return;
    event.preventDefault();
    event.stopPropagation();
    move(button.hasAttribute("data-ticker-prev") ? -1 : 1);
  });

  render();
  window.addEventListener("resize", render);
}

function bindStockNewsTabs() {
  document.addEventListener("click", (event) => {
    const tab = event.target.closest("[data-news-tab]");
    if (!tab) return;
    event.preventDefault();

    const target = tab.dataset.newsTab;
    document.querySelectorAll("[data-news-tab]").forEach((item) => {
      item.classList.toggle("is-active", item === tab);
    });
    document.querySelectorAll("[data-news-group]").forEach((group) => {
      group.classList.toggle("is-hidden", group.dataset.newsGroup !== target);
    });
  });
}

function syncTransferHistoryHeight() {
  const leftColumn = document.querySelector(".transfer-left-column");
  const historyCard = document.querySelector(".transfer-history-card");
  if (!leftColumn || !historyCard) return;

  if (window.matchMedia("(max-width: 1280px)").matches) {
    historyCard.style.removeProperty("--transfer-history-height");
    return;
  }

  const height = Math.round(leftColumn.getBoundingClientRect().height);
  if (height > 0) {
    historyCard.style.setProperty("--transfer-history-height", `${height}px`);
  }
}

async function hydrateDetailChart() {
  const canvas = document.querySelector("[data-stock-chart]");
  if (!canvas) return;

  const endpoint = canvas.dataset.endpoint;
  if (!endpoint) return;

  const refresh = async (resetSize = false) => {
    try {
      if (resetSize) resetCanvasLayout(canvas);
      const response = await fetch(endpoint, { cache: "no-store" });
      if (!response.ok) return;
      const payload = await response.json();
      renderManagedChart(canvas, payload);
      updateLiveFields(payload);
    } catch (_) {
      return;
    }
  };

  await refresh();
  window.addEventListener("resize", () => refresh(true));
  setInterval(refresh, 5000);
}

function updateTradeForms(currentPrice) {
  document.querySelectorAll("[data-trade-form]").forEach((form) => {
    const qtyInput = form.querySelector("[data-quantity-input]");
    const totalInput = form.querySelector("[data-total-input]");
    if (!qtyInput || !totalInput) return;

    const quantity = Math.max(Number(qtyInput.value || 0), 0);
    totalInput.value = Math.round(quantity * Number(currentPrice || 0));
  });
}

function bindTradeForms() {
  document.querySelectorAll("[data-trade-form]").forEach((form) => {
    const qtyInput = form.querySelector("[data-quantity-input]");
    const priceNode = document.querySelector("[data-live-price-inline]");
    if (!qtyInput) return;

    const sync = () => {
      const currentText = priceNode ? priceNode.textContent.replace(/[^\d.-]/g, "") : "0";
      const currentPrice = Number(currentText || 0);
      updateTradeForms(currentPrice);
    };

    qtyInput.addEventListener("input", sync);
    sync();
  });
}

function bindTransferLayout() {
  syncTransferHistoryHeight();
  window.addEventListener("resize", syncTransferHistoryHeight);
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

  window.addEventListener("resize", () => {
    resetCanvasLayout(canvas);
    updateHomePreview(JSON.parse(canvas.dataset.previewPayload));
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
  row.querySelector("[data-account-qty]").textContent = `${stock.quantity}주 · 평단 ${Number(stock.avg_price).toLocaleString("ko-KR")}원`;
  row.querySelector("[data-account-value]").textContent = formatKrw(stock.current_value);
  const profitNode = row.querySelector("[data-account-profit]");
  const prefix = stock.profit >= 0 ? "+" : "";
  profitNode.textContent = `${prefix}${Number(stock.profit).toLocaleString("ko-KR")}원 (${prefix}${Number(stock.profit_rate).toFixed(2)}%)`;
  profitNode.classList.remove("up", "down");
  profitNode.classList.add(stock.profit >= 0 ? "up" : "down");
}

function renderOrderRow(row, item) {
  row.querySelector("[data-order-type]").textContent = item.display_type;
  row.querySelector("[data-order-meta]").textContent = item.meta;
}

function renderTransferRow(row, item) {
  row.querySelector("[data-transfer-type]").textContent = item.display_type;
  row.querySelector("[data-transfer-meta]").textContent = item.meta;
  const amountNode = row.querySelector(".subtle");
  if (amountNode) amountNode.textContent = formatKrw(item.amount);
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
        if (payload.recent_orders[index]) renderOrderRow(row, payload.recent_orders[index]);
      });

      document.querySelectorAll("[data-transfer-row]").forEach((row, index) => {
        if (payload.recent_transfers[index]) renderTransferRow(row, payload.recent_transfers[index]);
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

async function hydratePortfolioSnapshot() {
  const endpointNode = document.querySelector("#portfolio-snapshot-endpoint");
  if (!endpointNode) return;

  const endpoint = endpointNode.textContent.trim();
  if (!endpoint) return;

  const refresh = async () => {
    try {
      const response = await fetch(endpoint, { cache: "no-store" });
      if (!response.ok) return;
      const payload = await response.json();

      document.querySelectorAll("[data-portfolio-card]").forEach((card, index) => {
        const item = payload.holdings[index];
        if (!item) return;
        card.href = item.detail_url;
        card.querySelector("[data-portfolio-name]").textContent = item.name;
        card.querySelector("[data-portfolio-qty]").textContent = `${item.quantity}주 보유`;
        card.querySelector("[data-portfolio-value]").textContent = formatKrw(item.current_value);

        const profitNode = card.querySelector("[data-portfolio-profit]");
        const prefix = item.profit >= 0 ? "+" : "";
        profitNode.textContent = `${prefix}${Number(item.profit).toLocaleString("ko-KR")}원`;
        profitNode.classList.remove("up", "down");
        profitNode.classList.add(item.profit >= 0 ? "up" : "down");

        const avgNode = card.querySelector("[data-portfolio-avg]");
        const currentNode = card.querySelector("[data-portfolio-current]");
        const rateNode = card.querySelector("[data-portfolio-rate]");
        if (avgNode) avgNode.textContent = formatKrw(item.avg_price);
        if (currentNode) currentNode.textContent = formatKrw(item.current_price);
        if (rateNode) {
          rateNode.textContent = `${prefix}${Number(item.profit_rate).toFixed(2)}%`;
          rateNode.classList.remove("up", "down");
          rateNode.classList.add(item.profit >= 0 ? "up" : "down");
        }

        const chart = card.querySelector("[data-portfolio-chart]");
        chart.dataset.values = item.history_prices.join(",");
        chart.dataset.labels = item.history_labels.join(",");
        chart.dataset.timestamps = item.history_timestamps.join(",");
        chart.dataset.currentPrice = item.current_price;
        chart.dataset.avgPrice = item.avg_price;
        renderMiniManagedChart(chart);
      });
    } catch (_) {
      return;
    }
  };

  await refresh();
  setInterval(refresh, 5000);
}

function initializeMiniCharts() {
  document.querySelectorAll("[data-mini-chart]").forEach((canvas) => {
    renderMiniManagedChart(canvas);
  });

  window.addEventListener("resize", () => {
    redrawMiniCharts("[data-mini-chart]");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((item) => {
    setTimeout(() => {
      item.style.opacity = "0";
      item.style.transition = "opacity 0.3s ease";
    }, 2500);
  });

  initializeMiniCharts();
  bindRangeControls();
  bindMiniRangeControls();
  bindTickerCarousel();
  bindStockNewsTabs();
  hydrateHomePreview();
  hydrateDetailChart();
  hydrateMarketSnapshot();
  hydratePortfolioSnapshot();
  bindTradeForms();
  bindTransferLayout();
});
