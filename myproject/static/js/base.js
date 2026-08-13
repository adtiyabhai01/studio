/* base.js — navigation, scroll reveal, auto-dismiss alerts */
(function () {
  "use strict";

  var nav = document.getElementById("siteNav");
  var burger = document.getElementById("navBurger");
  var drawer = document.getElementById("navDrawer");

  function onScroll() {
    if (nav) {
      nav.classList.toggle("is-scrolled", window.scrollY > 40);
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  function toggleMenu(open) {
    if (!burger || !drawer) return;
    var next = open !== undefined ? open : !drawer.classList.contains("is-open");
    drawer.classList.toggle("is-open", next);
    burger.classList.toggle("is-open", next);
    burger.setAttribute("aria-expanded", next ? "true" : "false");
    drawer.setAttribute("aria-hidden", next ? "false" : "true");
    document.body.style.overflow = next ? "hidden" : "";
  }
  if (burger) {
    burger.addEventListener("click", function () {
      toggleMenu();
      });
  }

  // Close the drawer when any link inside it is tapped.
  if (drawer) {
    drawer.addEventListener("click", function (event) {
      if (event.target.closest("a")) toggleMenu(false);
    });
  }

  // Smooth-scroll internal anchors (kept for pages with in-page links).
  document.addEventListener("click", function (event) {
    var anchor = event.target.closest('a[href^="#"]');
    if (!anchor) return;
    var id = anchor.getAttribute("href");
    if (id.length > 1) {
      var target = document.querySelector(id);
      if (target) {
        event.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  });

  // Scroll reveal.
  var prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Preloader — reveal the page once it has painted and the animation has had its moment.
  (function preloader() {
    var pre = document.getElementById("preloader");
    if (!pre) return;

    if (prefersReducedMotion) {
      pre.classList.add("is-done");
      return;
    }

    var MIN_SHOW = 1500; // ms — enough for the ring/bar animation to feel intentional.
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

    // Safety net — never trap the user behind the overlay.
    window.setTimeout(function () {
      if (!pre.classList.contains("is-done")) {
        pre.classList.add("is-done");
      }
    }, 5000);
  })();

  // Scroll reveal.
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    reveals.forEach(function (el) {
      io.observe(el);
    });
  } else {
    reveals.forEach(function (el) {
      el.classList.add("is-revealed");
    });
  }

  // Auto-dismiss Django flash messages.
  setTimeout(function () {
    var alerts = document.querySelectorAll(".page-alert");
    alerts.forEach(function (el) {
      el.style.transition = "opacity .5s ease";
      el.style.opacity = "0";
      setTimeout(function () {
        el.remove();
      }, 500);
    });
  }, 6000);

  // Live theme sync — public pages update instantly when the admin saves
  // a theme in the admin portal (BroadcastChannel) or whenever the tab is
  // shown again (visibility change / light polling as a fallback).
  (function themeSync() {
    var CHANNEL = "chamunda-theme";
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
    var lastSignature = null;
    var appliedOnce = false;

    function applyTheme(data) {
      var signature = JSON.stringify(data);
      if (data.is_custom === false) {
        // Turn the custom theme off — revert to the baked-in defaults.
        Object.keys(colorToVar).forEach(function (key) {
          root.style.removeProperty(colorToVar[key]);
        });
        root.style.removeProperty("--serif");
        root.style.removeProperty("--sans");
        root.style.removeProperty("--container");
        lastSignature = signature;
        return;
      }

      Object.keys(colorToVar).forEach(function (key) {
        if (data[key]) root.style.setProperty(colorToVar[key], data[key]);
      });
      if (data.primary) {
        root.style.setProperty("--line", "color-mix(in srgb, " + data.primary + " 24%, transparent)");
        root.style.setProperty("--line-soft", "color-mix(in srgb, " + data.primary + " 16%, transparent)");
      }
      if (data.heading_font) root.style.setProperty("--serif", data.heading_font);
      if (data.body_font) root.style.setProperty("--sans", data.body_font);
      if (data.container_width) root.style.setProperty("--container", data.container_width + "px");
      lastSignature = signature;
      appliedOnce = true;
    }

    function fetchTheme() {
      fetch("/theme.json", { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(function (res) {
          if (!res.ok) throw new Error("theme fetch failed");
          return res.json();
        })
        .then(function (data) {
          if (JSON.stringify(data) !== lastSignature) applyTheme(data);
        })
        .catch(function () {});
    }

    // Initial sync (self-heals if the server-side vars are stale).
    fetchTheme();

    // Same-origin tabs notify each other the instant a theme is saved.
    if ("BroadcastChannel" in window) {
      var channel = new BroadcastChannel(CHANNEL);
      channel.addEventListener("message", function () {
        // Slight delay so the portal's save request finishes first.
        window.setTimeout(fetchTheme, 700);
      });
    }

    // Catch up when the user switches back to this tab.
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible") fetchTheme();
    });

    // Lightweight fallback poll (only while the tab is visible).
    window.setInterval(function () {
      if (document.visibilityState === "visible") fetchTheme();
    }, 15000);
  })();

  // Visitor tracking — posts a stable visitor_id + screen resolution once per
  // page load. The server dedupes, so refreshes never create duplicate rows.
  (function visitorTrack() {
    var KEY = "chamunda_visitor_id";
    var vid = null;
    try {
      vid = localStorage.getItem(KEY);
      if (!vid) {
        vid = "v" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
        localStorage.setItem(KEY, vid);
      }
    } catch (e) {
      vid = "";
    }
    var body = JSON.stringify({
      visitor_id: vid,
      screen: window.screen && window.screen.width ? window.screen.width + "x" + window.screen.height : "",
      path: window.location.pathname + window.location.search,
      referrer: document.referrer || ""
    });
    fetch("/api/visitor/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
      body: body,
      keepalive: true
    }).catch(function () {});
  })();

  // Live maintenance mode — when the admin flips it on in the portal, every
  // already-open tab shows the maintenance screen instantly (no refresh needed).
  (function maintenanceWatch() {
    var overlay = null;
    var OVERLAY_GEAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>';

    function brandName() {
      var el = document.querySelector(".pre-name");
      return el ? el.textContent.trim() : "";
    }

    function showOverlay() {
      if (overlay || document.getElementById("maintScreen")) return;
      overlay = document.createElement("div");
      overlay.id = "maintScreen";
      overlay.setAttribute("aria-live", "assertive");
      overlay.innerHTML =
        '<div class="maint-inner">' +
        '<div class="maint-badge">' +
        '<svg class="ring" viewBox="0 0 120 120" aria-hidden="true"><circle class="track" cx="60" cy="60" r="52"></circle><circle class="bar" cx="60" cy="60" r="52"></circle></svg>' +
        '<span class="maint-gear" aria-hidden="true">' + OVERLAY_GEAR + "</span>" +
        "</div>" +
        '<span class="maint-pill">Under maintenance</span>' +
        '<h2 class="maint-title">We\'re fine-tuning <em>your stories</em></h2>' +
        '<p class="maint-sub">The studio is temporarily paused for a quick polish. Every frame is safe — we\'ll be right back.</p>' +
        '<p class="maint-dash maint-sub">Hold on&hellip;</p>' +
        '<p class="maint-name">' + brandName() + "</p>" +
        '<span class="maint-line"></span>' +
        "</div>";
      document.body.appendChild(overlay);
      document.body.style.overflow = "hidden";
    }

    function hideOverlay() {
      if (!overlay) return;
      if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
      overlay = null;
      document.body.style.overflow = "";
    }

    function poll() {
      fetch("/maintenance/mode/", { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(function (res) {
          if (!res.ok) throw new Error("status fetch failed");
          return res.json();
        })
        .then(function (data) {
          if (data && data.maintenance) showOverlay();
          else hideOverlay();
        })
        .catch(function () {});
    }

    poll();
    window.setInterval(poll, 10000);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible") poll();
    });
  })();
})();