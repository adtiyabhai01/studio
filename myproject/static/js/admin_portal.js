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
    /* ---------- tabs ---------- */
    var tabs = document.querySelectorAll(".ap-tab");
    var panels = document.querySelectorAll(".ap-panel");

    function activateTab(key) {
      tabs.forEach(function (tab) {
        tab.classList.toggle("is-active", tab.dataset.tab === key);
      });
      panels.forEach(function (panel) {
        var on = panel.dataset.panel === key;
        panel.classList.toggle("is-active", on);
        panel.hidden = !on;
      });
    }

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
  });
})();