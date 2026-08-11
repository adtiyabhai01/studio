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
})();