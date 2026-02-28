/**
 * Enbox – Frontend Application
 */

(function () {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const feedContainer = $("#feed-container");
  const tabsContainer = $("#source-tabs");
  const loading = $("#loading");
  const refreshBtn = $("#refresh-btn");

  let allFeeds = []; // cached data
  let activeTab = "all";

  // ─── Bootstrap ──────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", () => {
    loadFeeds();
    refreshBtn.addEventListener("click", () => loadFeeds());
  });

  async function loadFeeds() {
    showLoading(true);
    try {
      const resp = await fetch("/api/feeds");
      allFeeds = await resp.json();
      buildTabs();
      renderFeeds();
    } catch (err) {
      feedContainer.innerHTML = `<p class="empty-msg">加载失败：${err.message}</p>`;
    } finally {
      showLoading(false);
    }
  }

  // ─── Tabs ───────────────────────────────────────────────────
  function buildTabs() {
    // Remove old tabs except "all"
    tabsContainer.innerHTML = `<button class="tab ${activeTab === "all" ? "active" : ""}" data-index="all">全部</button>`;
    allFeeds.forEach((source, idx) => {
      const btn = document.createElement("button");
      btn.className = `tab ${activeTab === String(idx) ? "active" : ""}`;
      btn.dataset.index = String(idx);
      btn.textContent = `${source.icon || ""} ${source.name}`.trim();
      tabsContainer.appendChild(btn);
    });
    // Event delegation
    tabsContainer.onclick = (e) => {
      const btn = e.target.closest(".tab");
      if (!btn) return;
      activeTab = btn.dataset.index;
      $$(".tab").forEach((t) => t.classList.remove("active"));
      btn.classList.add("active");
      renderFeeds();
    };
  }

  // ─── Render ─────────────────────────────────────────────────
  function renderFeeds() {
    feedContainer.innerHTML = "";

    const sources = activeTab === "all"
      ? allFeeds
      : [allFeeds[parseInt(activeTab, 10)]];

    if (!sources.length || sources.every((s) => !s.items.length)) {
      feedContainer.innerHTML = `<p class="empty-msg">暂无内容</p>`;
      return;
    }

    sources.forEach((source) => {
      if (!source || !source.items.length) return;
      const section = document.createElement("div");
      section.className = "source-section";
      section.innerHTML = `
        <div class="source-header">
          <span class="source-icon">${source.icon || "📰"}</span>
          <span class="source-name">${esc(source.name)}</span>
          <span class="source-count">${source.items.length} 条</span>
        </div>`;

      source.items.forEach((item) => {
        if (item.display === "post") {
          section.appendChild(createPostCard(item));
        } else {
          section.appendChild(createArticleCard(item));
        }
      });

      feedContainer.appendChild(section);
    });
  }

  // ─── Article Card ───────────────────────────────────────────
  function createArticleCard(item) {
    const el = document.createElement("div");
    el.className = "card";

    let meta = [];
    if (item.author) meta.push(item.author);
    if (item.node) meta.push(item.node);
    if (item.score !== undefined && item.score > 0) meta.push(`▲ ${item.score}`);
    if (item.comments !== undefined) meta.push(`💬 ${item.comments}`);
    if (item.replies !== undefined && item.replies > 0) meta.push(`💬 ${item.replies}`);
    if (item.time) meta.push(relTime(item.time));

    el.innerHTML = `
      <div class="card-title"><a href="${esc(item.url)}" target="_blank" rel="noopener">${esc(item.title)}</a></div>
      ${meta.length ? `<div class="card-meta">${meta.map((m) => `<span>${esc(String(m))}</span>`).join("")}</div>` : ""}
      ${item.summary ? `<div class="card-summary">${esc(item.summary)}</div>` : ""}
    `;
    return el;
  }

  // ─── Post Card (collapsible) ────────────────────────────────
  function createPostCard(item) {
    const el = document.createElement("div");
    el.className = "post-card";

    const bodyText = item.summary || item.title || "";
    const needsCollapse = bodyText.length > 140;

    el.innerHTML = `
      <div class="post-header">
        <span class="post-author">${esc(item.author || "")}</span>
        <span class="post-time">${item.time ? relTime(item.time) : ""}</span>
      </div>
      <div class="post-body ${needsCollapse ? "collapsed" : ""}">${esc(bodyText)}</div>
      ${needsCollapse ? `<button class="post-toggle">展开全文</button>` : ""}
      ${item.url ? `<a class="post-link" href="${esc(item.url)}" target="_blank" rel="noopener">查看原文 →</a>` : ""}
    `;

    if (needsCollapse) {
      const toggle = el.querySelector(".post-toggle");
      const body = el.querySelector(".post-body");
      toggle.addEventListener("click", () => {
        const collapsed = body.classList.toggle("collapsed");
        toggle.textContent = collapsed ? "展开全文" : "收起";
      });
    }

    return el;
  }

  // ─── Helpers ────────────────────────────────────────────────
  function esc(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
  }

  function relTime(ts) {
    const now = Date.now() / 1000;
    const diff = now - ts;
    if (diff < 0) return "";
    if (diff < 60) return "刚刚";
    if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`;
    if (diff < 2592000) return `${Math.floor(diff / 86400)} 天前`;
    const d = new Date(ts * 1000);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  function showLoading(show) {
    if (show) {
      loading.style.display = "flex";
    } else {
      loading.style.display = "none";
    }
  }
})();
