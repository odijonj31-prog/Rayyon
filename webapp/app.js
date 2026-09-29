const tg = window.Telegram?.WebApp;

let CONFIG = { manager_username: "" };

function initTelegram() {
  if (!tg) return;
  tg.ready();
  tg.expand();
  try { tg.setHeaderColor("#0f0e0d"); } catch (e) {}
  try { tg.setBackgroundColor("#0f0e0d"); } catch (e) {}
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

async function apiGet(path) {
  const res = await fetch(path);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return res.json();
}

async function validateUser() {
  if (!tg || !tg.initData) return null;
  const data = await apiPost("/api/validate", { initData: tg.initData });
  return data.ok ? data.user : null;
}

async function loadConfig() {
  const data = await apiGet("/api/config");
  if (data.ok) CONFIG = data;
}

function setupManagerButton() {
  document.getElementById("manager-btn").addEventListener("click", () => {
    if (!CONFIG.manager_username) {
      tg?.showAlert?.("Menejer bilan bog'lanish hozircha sozlanmagan.");
      return;
    }
    tg?.openTelegramLink?.(`https://t.me/${CONFIG.manager_username}`);
  });
}

async function loadPortfolio() {
  const grid = document.getElementById("portfolio-grid");
  const data = await apiGet("/api/portfolio");
  if (!data.ok || !data.items.length) return;

  grid.innerHTML = data.items.map(item => `
    <div class="portfolio-card">
      <img src="${item.photo_url}" alt="${escapeHtml(item.title)}" loading="lazy" />
      <div class="portfolio-card-info">
        <p class="portfolio-card-title">${escapeHtml(item.title)}</p>
        ${item.style_tags ? `<p class="portfolio-card-tags">${escapeHtml(item.style_tags)}</p>` : ""}
      </div>
    </div>
  `).join("");
}

function setupTabs() {
  document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.dataset.tab;
      document.querySelectorAll(".nav-btn").forEach(b => b.classList.toggle("active", b === btn));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.toggle("active", p.id === tabId));
      if (tg?.HapticFeedback) { try { tg.HapticFeedback.impactOccurred("light"); } catch (e) {} }
    });
  });
}

async function main() {
  initTelegram();
  setupTabs();
  setupManagerButton();

  await Promise.all([loadConfig(), validateUser(), loadPortfolio()]);

  document.getElementById("splash").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
}

main();
