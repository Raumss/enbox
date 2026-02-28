/**
 * Enbox – Frontend Application
 *
 * Two view modes:
 *   1. "timeline"  – all items mixed, sorted by time descending
 *   2. "platform"  – items grouped by platform type (same platform merged),
 *                    with tabs to filter by platform
 */

(function () {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const feedContainer = $("#feed-container");
  const tabsContainer = $("#source-tabs");
  const loading = $("#loading");
  const refreshBtn = $("#refresh-btn");
  const viewBtns = $$(".view-btn");

  let allFeeds = [];       // raw data from API (array of source groups)
  let viewMode = "timeline"; // "timeline" | "platform"
  let activeTab = "all";     // used in platform mode

  // ─── Bootstrap ──────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", () => {
    loadFeeds();
    refreshBtn.addEventListener("click", () => loadFeeds());

    // View mode toggle
    viewBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        viewBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        viewMode = btn.dataset.mode;
        activeTab = "all";
        buildTabs();
        renderFeeds();
      });
    });
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

  // ─── Platform map (type -> display label & icon) ────────────
  const PLATFORM_LABELS = {
    hackernews: { label: "Hacker News", icon: "🔶" },
    v2ex:       { label: "V2EX",        icon: "💬" },
    rss:        { label: "RSS",         icon: "📰" },
    youtube:    { label: "YouTube",     icon: "▶️" },
    podcast:    { label: "Podcast",     icon: "🎙️" },
    coolshell:  { label: "CoolShell",   icon: "🐚" },
    twitter:    { label: "X / Twitter", icon: "𝕏" },
    xueqiu:     { label: "雪球",        icon: "❄️" },
  };

  // ─── Helper: flatten all items ──────────────────────────────
  function getAllItems() {
    const items = [];
    allFeeds.forEach((source) => {
      (source.items || []).forEach((item) => items.push(item));
    });
    return items;
  }

  // ─── Helper: group items by platform type ───────────────────
  function groupByPlatform() {
    const map = {};
    allFeeds.forEach((source) => {
      const ptype = source.type || "rss";
      if (!map[ptype]) {
        const info = PLATFORM_LABELS[ptype] || { label: ptype, icon: "📰" };
        map[ptype] = {
          type: ptype,
          label: info.label,
          icon: source.icon || info.icon,
          items: [],
        };
      }
      (source.items || []).forEach((item) => map[ptype].items.push(item));
    });
    // Sort items within each platform by time descending
    Object.values(map).forEach((group) => {
      group.items.sort((a, b) => (b.time || 0) - (a.time || 0));
    });
    return map;
  }

  // ─── Tabs ───────────────────────────────────────────────────
  function buildTabs() {
    tabsContainer.innerHTML = "";

    if (viewMode === "timeline") {
      // No tabs in timeline mode
      tabsContainer.style.display = "none";
      return;
    }

    // Platform mode: "全部" + one tab per platform type
    tabsContainer.style.display = "flex";
    const allBtn = document.createElement("button");
    allBtn.className = `tab ${activeTab === "all" ? "active" : ""}`;
    allBtn.dataset.platform = "all";
    allBtn.textContent = "全部";
    tabsContainer.appendChild(allBtn);

    const platforms = groupByPlatform();
    Object.values(platforms).forEach((p) => {
      const btn = document.createElement("button");
      btn.className = `tab ${activeTab === p.type ? "active" : ""}`;
      btn.dataset.platform = p.type;
      btn.textContent = `${p.icon || ""} ${p.label}`.trim();
      tabsContainer.appendChild(btn);
    });

    tabsContainer.onclick = (e) => {
      const btn = e.target.closest(".tab");
      if (!btn) return;
      activeTab = btn.dataset.platform;
      $$(".tab").forEach((t) => t.classList.remove("active"));
      btn.classList.add("active");
      renderFeeds();
    };
  }

  // ─── Render ─────────────────────────────────────────────────
  function renderFeeds() {
    feedContainer.innerHTML = "";
    if (viewMode === "timeline") {
      renderTimeline();
    } else {
      renderPlatform();
    }
  }

  // ─── Timeline Mode ─────────────────────────────────────────
  function renderTimeline() {
    const items = getAllItems();
    items.sort((a, b) => (b.time || 0) - (a.time || 0));

    if (!items.length) {
      feedContainer.innerHTML = `<p class="empty-msg">暂无内容</p>`;
      return;
    }

    items.forEach((item) => {
      if (item.display === "post") {
        feedContainer.appendChild(createPostCard(item, true));
      } else {
        feedContainer.appendChild(createArticleCard(item, true));
      }
    });
  }

  // ─── Platform Mode ─────────────────────────────────────────
  function renderPlatform() {
    const platforms = groupByPlatform();
    const entries = activeTab === "all"
      ? Object.values(platforms)
      : [platforms[activeTab]].filter(Boolean);

    if (!entries.length || entries.every((p) => !p.items.length)) {
      feedContainer.innerHTML = `<p class="empty-msg">暂无内容</p>`;
      return;
    }

    entries.forEach((platform) => {
      if (!platform || !platform.items.length) return;
      const section = document.createElement("div");
      section.className = "source-section";
      section.innerHTML = `
        <div class="source-header">
          <span class="source-icon">${platform.icon || "📰"}</span>
          <span class="source-name">${esc(platform.label)}</span>
          <span class="source-count">${platform.items.length} 条</span>
        </div>`;

      platform.items.forEach((item) => {
        if (item.display === "post") {
          section.appendChild(createPostCard(item, false));
        } else {
          section.appendChild(createArticleCard(item, false));
        }
      });

      feedContainer.appendChild(section);
    });
  }

  // ─── Article Card ───────────────────────────────────────────
  function createArticleCard(item, showSource) {
    const el = document.createElement("div");
    el.className = "card";

    let meta = [];
    if (showSource && item.source_name) meta.push(`${item.source_icon || "📰"} ${item.source_name}`);
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
  function createPostCard(item, showSource) {
    const el = document.createElement("div");
    el.className = "post-card";

    const bodyText = item.summary || item.title || "";
    const needsCollapse = bodyText.length > 140;
    const sourceTag = showSource && item.source_name
      ? ` · <span class="post-source">${item.source_icon || "📰"} ${esc(item.source_name)}</span>`
      : "";

    el.innerHTML = `
      <div class="post-header">
        <span class="post-author">${esc(item.author || "")}${sourceTag}</span>
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
