(() => {
  /* ─────────────────────────────────────────────────────────────────────────
     app.js  —  Smart Distributed Logging System
     ALL API calls go through /proxy/* on the dashboard server.
     The browser NEVER touches a JWT token — the server handles it silently.
  ───────────────────────────────────────────────────────────────────────── */

  // Proxy base — same origin as dashboard (port 5006)
  const PROXY = "";          // relative URLs  →  /proxy/order, /proxy/logs …
  const LOGGING_WS = "http://localhost:5005";   // WebSocket direct (read-only)

  /* ── Core fetch wrapper ────────────────────────────────────────────────── */

  async function apiFetch(url, opts = {}) {
    try {
      const res = await fetch(url, {
        headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
        ...opts,
      });
      if (res.status === 401) {
        // Session expired — redirect to login
        window.location.href = "/login";
        return null;
      }
      return await res.json();
    } catch (e) {
      console.error("apiFetch error:", url, e);
      return null;
    }
  }

  /* ── Toast ─────────────────────────────────────────────────────────────── */

  function toast(msg, type = "success") {
    let c = document.getElementById("toast-container");
    if (!c) { c = document.createElement("div"); c.id = "toast-container"; document.body.appendChild(c); }
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = msg;
    c.appendChild(el);
    setTimeout(() => el.remove(), 3500);
  }

  /* ── Badges / formatting ───────────────────────────────────────────────── */

  function statusBadge(status) {
    const map = { SUCCESS: "badge-success", ERROR: "badge-error",
                  WARNING: "badge-warning", INFO: "badge-info" };
    const cls = map[status?.toUpperCase()] || "badge-info";
    return `<span class="badge ${cls}">${status || "—"}</span>`;
  }

  function fmtTime(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleTimeString("en-IN", { hour12: false }) + " " +
           d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
  }

  function fmtMs(ms) { return (ms == null || ms === "") ? "—" : `${ms} ms`; }

  /* ── Theme ─────────────────────────────────────────────────────────────── */

  function toggleTheme() {
    document.body.classList.toggle("light-theme");
    const mode = document.body.classList.contains("light-theme") ? "light" : "dark";
    localStorage.setItem("theme", mode);
    updateThemeButton();
  }

  function updateThemeButton() {
    const btn = document.getElementById("theme-toggle-btn");
    if (!btn) return;
    btn.innerHTML = document.body.classList.contains("light-theme") ? "🌙 Dark" : "☀ Light";
  }

  (function loadTheme() {
    if (localStorage.getItem("theme") === "light") document.body.classList.add("light-theme");
    setTimeout(updateThemeButton, 100);
  })();

  /* ── Simulate order — calls /proxy/order (JWT added server-side) ────────── */

  async function simulateOrder(count = 1) {
    const btn = document.getElementById("simulate-btn");
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Sending…'; }

    let data;
    if (count === 1) {
      data = await apiFetch(`${PROXY}/proxy/order`, {
        method: "POST",
        body: JSON.stringify({
          product_id:  `PROD-00${Math.ceil(Math.random() * 5)}`,
          quantity:    Math.ceil(Math.random() * 3),
          customer_id: `CUST-${String(Math.ceil(Math.random() * 50)).padStart(4, "0")}`,
        }),
      });
    } else {
      data = await apiFetch(`${PROXY}/proxy/simulate`, {
        method: "POST",
        body: JSON.stringify({ count }),
      });
    }

    if (btn) { btn.disabled = false; btn.textContent = "Send Order"; }

    if (!data)            { toast("❌ Could not reach API Gateway", "error"); return; }
    if (data.success === false) { toast(`❌ ${data.message}`, "error"); }
    else                        { toast(`✅ Order accepted`, "success"); }

    if (typeof loadOverview    === "function") setTimeout(loadOverview,    800);
    if (typeof loadLatestLogs  === "function") setTimeout(loadLatestLogs,  800);
  }

  /* ── Shared log table renderer ──────────────────────────────────────────── */

  function renderLogsTable(logs, containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (!logs || logs.length === 0) {
      el.innerHTML = `<div class="empty-state">No logs found.</div>`;
      return;
    }
    const rows = logs.map(l => `
      <tr>
        <td class="td-mono text-accent">${l.trace_id}</td>
        <td class="td-mono">${l.service_name}</td>
        <td>${statusBadge(l.status)}</td>
        <td>${l.message}</td>
        <td>${fmtMs(l.response_time)}</td>
        <td>${fmtTime(l.timestamp)}</td>
      </tr>`).join("");
    el.innerHTML = `
      <table>
        <thead><tr><th>Trace ID</th><th>Service</th><th>Status</th>
                   <th>Message</th><th>Resp Time</th><th>Timestamp</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  /* ── Real-time WebSocket (read-only, no auth needed) ───────────────────── */

  const socket = io(LOGGING_WS);
  socket.on("connect",  () => console.log("✅ Live log socket connected"));
  socket.on("new_log",  ()  => {
    if (typeof loadLatestLogs === "function") loadLatestLogs();
    if (typeof loadLogs       === "function") loadLogs();
    if (typeof loadOverview   === "function") loadOverview();
  });

  /* ── Kubernetes scale control (calls /proxy/k8s/*) ─────────────────────── */

  async function scaleService(service, replicas) {
    const data = await apiFetch(`${PROXY}/proxy/k8s/scale`, {
      method: "POST",
      body: JSON.stringify({ service, replicas }),
    });
    if (data && data.success) toast(`✅ ${service} scaled to ${replicas} replicas`);
    else toast(`❌ Scale failed: ${data?.message || "unknown error"}`, "error");
    return data;
  }

  /* ── Export ─────────────────────────────────────────────────────────────── */

  window.APP = {
    apiFetch, PROXY,
    toast, statusBadge, fmtTime, fmtMs,
    simulateOrder, renderLogsTable,
    toggleTheme, scaleService,
  };

})();
