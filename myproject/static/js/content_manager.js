/* content_manager.js — helpers for the portal's content editor pages. */
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
    /* ---------- auto slug from name / title ---------- */
    var slugInput = document.querySelector('[name="slug"]');
    var sourceInput = document.querySelector('[name="name"], [name="title"]');

    if (slugInput && sourceInput) {
      sourceInput.addEventListener("input", function () {
        if (slugInput.dataset.touched === "1") return;
        slugInput.value = sourceInput.value
          .toLowerCase()
          .trim()
          .replace(/[^a-z0-9\s-]+/g, "")
          .replace(/\s+/g, "-")
          .replace(/-+/g, "-")
          .replace(/^-|-$/g, "");
      });
      slugInput.addEventListener("input", function () {
        slugInput.dataset.touched = "1";
      });
    }
  });
})();
