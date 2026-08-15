/* admin_portal.js — tabs, enquiry search filter, status updates. */
(function () {
  "use strict";

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  onReady(function () {
    /* ---------- preloader (login page refresh animation) ---------- */
    var pre = document.getElementById("preloader");
    if (pre) {
      var prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (prefersReducedMotion) {
        pre.classList.add("is-done");
      } else {
        var MIN_SHOW = 1500;
        var started = Date.now();
        function hide() {
          var wait = Math.max(0, MIN_SHOW - (Date.now() - started));
          window.setTimeout(function () {
            pre.classList.add("is-done");
            pre.setAttribute("aria-hidden", "true");
          }, wait);
        }
        if (document.readyState === "complete") {
          hide();
        } else {
          window.addEventListener("load", hide);
        }
        window.setTimeout(function () {
          if (!pre.classList.contains("is-done")) {
            pre.classList.add("is-done");
          }
        }, 5000);
      }
    }

    /* ---------- tabs ---------- */
    var tabs = document.querySelectorAll(".ap-tab");
    var panels = document.querySelectorAll(".ap-panel");

    function currentTab() {
      var active = document.querySelector(".ap-tab.is-active");
      return active ? active.dataset.tab : "";
    }

    function activateTab(key) {
      tabs.forEach(function (tab) {
        tab.classList.toggle("is-active", tab.dataset.tab === key);
      });
      panels.forEach(function (panel) {
        var on = panel.dataset.panel === key;
        panel.classList.toggle("is-active", on);
        panel.hidden = !on;
      });
      if (key === "site") {
        startHealthPolling();
      } else {
        stopHealthPolling();
      }
    }

    // Keep the current tab after server-side form posts (maintenance toggle,
    // theme save) — the active tab is posted along and restored on redirect.
    document.querySelectorAll("form[data-keep-tab]").forEach(function (form) {
      form.addEventListener("submit", function () {
        var input = form.querySelector('input[name="tab"]');
        if (!input) {
          input = document.createElement("input");
          input.type = "hidden";
          input.name = "tab";
          form.appendChild(input);
        }
        input.value = currentTab() || "";
      });
    });

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        activateTab(tab.dataset.tab);
      });
    });

    // Preserve the ?tab= param across renders (e.g. "Manage New Enquiries" button).
    var params = new URLSearchParams(window.location.search);
    if (params.get("tab")) activateTab(params.get("tab"));

    /* ---------- enquiry search ---------- */
    var search = document.getElementById("apSearch");
    if (search) {
      search.addEventListener("input", function () {
        var q = search.value.trim().toLowerCase();
        document.querySelectorAll(".ap-row").forEach(function (row) {
          var hay = (row.dataset.query || "").toLowerCase();
          row.classList.toggle("is-filtered", q.length > 1 && hay.indexOf(q) === -1);
        });
      });
    }

    /* ---------- theme live preview ---------- */
    var colorToVar = {
      background: "--bg",
      background_secondary: "--bg-2",
      ink: "--ink",
      ink_secondary: "--ink-2",
      ivory: "--ivory",
      ivory_secondary: "--ivory-2",
      cream: "--cream",
      primary: "--gold",
      primary_strong: "--gold-strong",
      primary_deep: "--gold-deep",
      muted: "--muted",
      muted_secondary: "--muted-2"
    };

    var root = document.documentElement;
    var toggle = document.getElementById("apThemeToggle");
    var statePill = document.getElementById("apThemeState");

    function updateStatePill() {
      if (!statePill || !toggle) return;
      var on = toggle.checked;
      statePill.textContent = "Custom theme " + (on ? "ON" : "OFF");
      statePill.className = "ap-theme-state " + (on ? "ap-theme-state--on" : "ap-theme-state--off");
    }

    document.querySelectorAll(".ap-color").forEach(function (input) {
      input.addEventListener("input", function () {
        var prop = colorToVar[input.name];
        if (prop && toggle && toggle.checked) {
          root.style.setProperty(prop, input.value);
        }
      });
    });

    if (toggle) {
      toggle.addEventListener("change", function () {
        var on = toggle.checked;
        if (on) {
          // Re-apply saved values from the inputs.
          document.querySelectorAll(".ap-color").forEach(function (input) {
            var prop = colorToVar[input.name];
            if (prop) root.style.setProperty(prop, input.value);
          });
        } else {
          // Fall back to the defaults baked into base.css.
          Object.keys(colorToVar).forEach(function (key) {
            root.style.removeProperty(colorToVar[key]);
          });
        }
        updateStatePill();
      });
    }

    document.querySelectorAll(".ap-theme-select select, .ap-theme-select--num input").forEach(function (input) {
      input.addEventListener("change", function () {
        if (toggle && !toggle.checked) return;
        if (input.name === "heading_font") {
          root.style.setProperty("--serif", input.value);
        } else if (input.name === "body_font") {
          root.style.setProperty("--sans", input.value);
        } else if (input.name === "container_width") {
          root.style.setProperty("--container", input.value + "px");
        }
      });
    });

    /* ---------- ready-made theme presets (one-click apply & save) ---------- */
    function broadcastThemeChange() {
      if ("BroadcastChannel" in window) {
        try {
          new BroadcastChannel("chamunda-theme").postMessage("theme-changed");
        } catch (e) {}
      }
    }

    document.querySelectorAll(".ap-preset").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var colors = JSON.parse(btn.dataset.colors || "{}");
        var heading = btn.dataset.heading || "";
        var body = btn.dataset.body || "";

        Object.keys(colors).forEach(function (key) {
          var input = document.querySelector('.ap-color[name="' + key + '"]');
          if (input) input.value = colors[key];
        });

        var hSel = document.querySelector('select[name="heading_font"]');
        var bSel = document.querySelector('select[name="body_font"]');
        if (hSel && heading) hSel.value = heading;
        if (bSel && body) bSel.value = body;

        if (toggle) toggle.checked = true;

        // Live preview without leaving the page.
        Object.keys(colorToVar).forEach(function (key) {
          var input = document.querySelector('.ap-color[name="' + key + '"]');
          if (input) root.style.setProperty(colorToVar[key], input.value);
        });
        if (hSel) root.style.setProperty("--serif", hSel.value);
        if (bSel) root.style.setProperty("--sans", bSel.value);
        updateStatePill();

        document.querySelectorAll(".ap-preset").forEach(function (p) {
          p.classList.remove("is-current");
        });
        btn.classList.add("is-current");

        // Save the chosen palette immediately.
        var form = document.getElementById("apThemeForm");
        if (form) {
          broadcastThemeChange();
          form.submit();
        }
      });
    });

    // Broadcast when the theme is saved or reset via the buttons too.
    var themeForm = document.getElementById("apThemeForm");
    if (themeForm) {
      themeForm.addEventListener("submit", function () {
        broadcastThemeChange();
      });
    }

    updateStatePill();

    /* ---------- status update (AJAX, graceful fallback to no-op) ---------- */
    document.querySelectorAll(".ap-status").forEach(function (select) {
      select.addEventListener("change", function () {
        var row = select.closest(".ap-row");
        var url = select.dataset.url;
        var csrf = select.dataset.csrf;
        var id = select.dataset.id;

        if (!url || !csrf || !id) return;

        var body = new FormData();
        body.append("portal_action", "status");
        body.append("enquiry_id", id);
        body.append("status", select.value);
        body.append("csrfmiddlewaretoken", csrf);

        // Flash the changed colour before the server round-trip.
        var classMap = {
          NEW: "is-new",
          CONTACTED: "is-contact",
          FOLLOW_UP: "is-followup",
          BOOKED: "is-booked",
          COMPLETED: "is-completed",
          CLOSED: "is-closed"
        };
        select.className = "ap-status";
        select.classList.add(classMap[select.value] || "is-closed");

        fetch(url, {
          method: "POST",
          body: body,
          credentials: "same-origin",
          headers: { "X-Requested-With": "XMLHttpRequest" }
        }).then(function (res) {
          if (row) row.classList.add("is-flash");
          setTimeout(function () {
            if (row) row.classList.remove("is-flash");
          }, 700);
        }).catch(function () {
          window.location.reload();
        });
      });
    });

    /* ---------- site health dashboard ---------- */
    var healthPanel = document.getElementById("panel-site");
    var HEALTH_LABELS = {
      ok: ["is-ok", "Normal"],
      warn: ["is-warn", "Warning"],
      crit: ["is-crit", "Critical"],
      na: ["is-na", "Unavailable"]
    };

    function fmtBytes(n) {
      if (n === null || n === undefined || isNaN(n)) return "—";
      var units = ["B", "KB", "MB", "GB", "TB"];
      var v = Number(n);
      var u = 0;
      while (v >= 1024 && u < units.length - 1) {
        v /= 1024;
        u++;
      }
      return v.toFixed(u === 0 || v >= 100 ? 0 : 1) + " " + units[u];
    }

    function setHealthText(id, txt) {
      var el = document.getElementById(id);
      if (el) el.textContent = txt === null || txt === undefined || txt === "" ? "—" : txt;
    }

    function setHealthStatus(id, level) {
      var el = document.getElementById(id);
      if (!el) return;
      var s = HEALTH_LABELS[level] || HEALTH_LABELS.na;
      el.className = "ap-metric-dot " + s[0];
      var label = el.querySelector(".ap-metric-dot-label");
      if (label) label.textContent = s[1];
    }

    function renderGauge(gaugeId, ringId, pct, available) {
      var gauge = document.getElementById(gaugeId);
      var ring = document.getElementById(ringId);
      if (!gauge && !ring) return;
      var c = 326.725;
      var p = available && pct !== null && pct !== undefined ? Math.max(0, Math.min(100, pct)) : 0;
      if (ring) {
        ring.style.strokeDasharray = c.toFixed(2);
        ring.style.strokeDashoffset = (c * (1 - p / 100)).toFixed(2);
      }
    }

    function applyHealthGauge(prefix, d) {
      var ok = d && d.available && d.percent !== null && d.percent !== undefined;
      var pct = ok ? d.percent : 0;
      var level = d ? d.level : "na";
      renderGauge(prefix + "Gauge", prefix + "Ring", pct, ok);
      setHealthText(prefix + "V", ok ? Math.round(pct) + "" : "—");
      if (ok) {
        setHealthStatus(prefix + "Status", level);
      } else {
        setHealthStatus(prefix + "Status", "na");
      }
    }

    function applyHealthStorage(d, prefix, key) {
      var r = (d && d[key]) || null;
      var level = r ? r.level : "na";
      var pct = r && r.percent !== null && r.percent !== undefined ? r.percent : 0;
      setHealthText(prefix + "Pct", r && r.percent !== null && r.percent !== undefined ? Math.round(r.percent) + "%" : "—");
      setHealthText(prefix + "Used", fmtBytes(r && r.used));
      setHealthText(prefix + "Total", fmtBytes(r && r.total));
      setHealthText(prefix + "Avail", fmtBytes(r && r.available));
      setHealthStatus(prefix + "Status", level);
      var bar = document.getElementById(prefix + "Bar");
      if (bar) {
        bar.className = "ap-metric-bar-fill " + (HEALTH_LABELS[level] ? level : "is-na");
        bar.style.width = Math.max(0, Math.min(100, pct)).toFixed(2) + "%";
      }
      var src = document.getElementById(prefix + "Source");
      if (src) src.textContent = (r && r.engine) || "—";
    }

    function applyHealth(d) {
      if (!d || typeof d !== "object") return;
      var cpu = d.cpu || {};
      if (cpu.available && cpu.percent !== null && cpu.percent !== undefined) {
        setHealthText("cpuDetail", (cpu.cores ? cpu.cores + " logical cores · " : "") + "current server load");
      } else {
        setHealthText("cpuDetail", cpu.error || "CPU monitoring unavailable");
      }
      applyHealthGauge("cpu", cpu);

      var gpu = d.gpu || {};
      if (gpu.available && gpu.percent !== null && gpu.percent !== undefined) {
        setHealthText("gpuDetail", (gpu.name ? gpu.name + " · " : "") + "GPU load");
      } else {
        setHealthText("gpuDetail", gpu.error || "No GPU available on this host");
      }
      applyHealthGauge("gpu", gpu);

      applyHealthStorage(d, "db", "database");
      applyHealthStorage(d, "ph", "photos");
      applyHealthStorage(d, "vd", "videos");

      var ov = d.overall || null;
      applyHealthStorage(d, "ov", "overall");
      setHealthText("ovSource", (ov && ov.limit ? "Database + Cloudinary media" : "Not enough data to compute"));

      var updated = document.getElementById("apHealthUpdated");
      if (updated && d.generated_at) {
        updated.textContent = "Updated " + new Date(d.generated_at).toLocaleTimeString();
      }
    }

    var healthUrl = healthPanel ? (healthPanel.dataset.healthUrl || "/admin-portal/health/") : null;
    var healthTimer = null;

    function healthTick() {
      if (!healthUrl) return;
      var pill = document.getElementById("apHealthLive");
      if (pill) {
        pill.textContent = "● Updating";
        pill.className = "ap-health-live is-on";
      }
      fetch(healthUrl, {
        credentials: "same-origin",
        headers: { Accept: "application/json" }
      }).then(function (res) {
        if (res.status === 403) throw new Error("Unauthorized");
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      }).then(function (data) {
        if (data && data.error) throw new Error(data.error);
        applyHealth(data);
        if (pill) {
          pill.textContent = "● Live";
          pill.className = "ap-health-live is-on";
        }
      }).catch(function () {
        if (pill) {
          pill.textContent = "● Offline";
          pill.className = "ap-health-live";
        }
      });
    }

    function startHealthPolling() {
      if (!healthUrl || healthTimer) return;
      healthTick();
      healthTimer = setInterval(healthTick, 15000);
    }

    function stopHealthPolling() {
      if (healthTimer) {
        clearInterval(healthTimer);
        healthTimer = null;
      }
    }

    if (healthPanel) {
      var refreshBtn = document.getElementById("apRefresh");
      if (refreshBtn) refreshBtn.addEventListener("click", healthTick);
    }

    // Paint the first snapshot served with the page, then keep it live.
    if (window.AP_HEALTH) applyHealth(window.AP_HEALTH);
    if (params.get("tab") === "site") startHealthPolling();
  });
})();