/* portfolio.js — gallery filtering, lightbox, video modal.
   Loaded on the portfolio page AND the service pages (shared gallery). */
(function () {
  "use strict";

  /* ---------- category filtering ---------- */
  var filterButtons = Array.prototype.slice.call(document.querySelectorAll("#portfolioFilter .filter"));
  var items = Array.prototype.slice.call(document.querySelectorAll(".portfolio-grid .g-item"));

  if (filterButtons.length && items.length) {
    filterButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var f = btn.getAttribute("data-filter");
        filterButtons.forEach(function (b) {
          b.classList.toggle("filter--active", b === btn);
        });
        items.forEach(function (item) {
          var cat = item.getAttribute("data-cat") || "all";
          var show = f === "all" || cat === f;
          item.classList.toggle("is-hidden", !show);
        });
      });
    });
  }

  /* ---------- lightbox ---------- */
  var lightbox = document.getElementById("lightbox");
  var lightboxImg = document.getElementById("lightboxImg");
  var lightboxCap = document.getElementById("lightboxCap");
  var lightboxClose = document.getElementById("lightboxClose");
  var lightboxPrev = document.getElementById("lightboxPrev");
  var lightboxNext = document.getElementById("lightboxNext");

  var galleryLinks = Array.prototype.slice.call(document.querySelectorAll("[data-lightbox]"));
  var itemsData = galleryLinks.map(function (el) {
    return {
      src: el.getAttribute("data-lightbox"),
      caption: el.getAttribute("data-caption"),
    };
  });
  var currentIndex = 0;

  function openLightbox(index) {
    var data = itemsData[index];
    if (!data) return;
    currentIndex = index;
    lightboxImg.src = data.src;
    lightboxImg.alt = data.caption || "";
    if (lightboxCap) lightboxCap.textContent = data.caption || "";
    if (lightbox) {
      lightbox.classList.add("is-open");
      lightbox.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    }
  }

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.classList.remove("is-open");
    lightbox.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  function stepLightbox(dir) {
    if (!itemsData.length) return;
    openLightbox((currentIndex + dir + itemsData.length) % itemsData.length);
  }

  galleryLinks.forEach(function (el, i) {
    el.addEventListener("click", function () {
      openLightbox(i);
    });
  });

  if (lightboxClose) lightboxClose.addEventListener("click", closeLightbox);
  if (lightboxPrev) lightboxPrev.addEventListener("click", function () { stepLightbox(-1); });
  if (lightboxNext) lightboxNext.addEventListener("click", function () { stepLightbox(1); });
  if (lightbox) {
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox) closeLightbox();
    });
  }

  /* ---------- autoplay video cards ----------
     Uploaded films and YouTube clips autoplay muted + looped while in view,
     so no click is required to start playback. Videos only load as they
     approach the viewport (desktop and mobile) to avoid unnecessary lag. */
  function setupVideoCards() {
    var cards = Array.prototype.slice.call(document.querySelectorAll(".v-card"));
    if (!cards.length) return;

    var mediaEls = cards.map(function (card) {
      var media = card.querySelector(".v-media");
      var src = card.getAttribute("data-src") || "";
      var embedId = card.getAttribute("data-video") || "";

      if (!media) return null;

      if (src) {
        var poster = media.querySelector("img, .v-img--mono");
        var video = document.createElement("video");
        video.className = "v-video";
        video.muted = true;
        video.loop = true;
        video.playsInline = true;
        video.setAttribute("playsinline", "");
        video.preload = "none";
        video.src = src;
        if (poster && poster.tagName === "IMG") {
          video.setAttribute("poster", poster.getAttribute("src") || "");
        }
        media.innerHTML = "";
        media.appendChild(video);
        card.classList.add("v-card--inline");
        return video;
      }

      if (embedId) {
        var holder = document.createElement("div");
        holder.className = "v-embed";
        media.innerHTML = "";
        media.appendChild(holder);
        card.classList.add("v-card--inline");
        return holder;
      }

      return null;
    });

    function activate(el, card) {
      if (!el) return;
      if (el.tagName === "VIDEO") {
        el.preload = "auto";
        var p = el.play();
        if (p && p.catch) {
          p.catch(function () {
            el.addEventListener("loadedmetadata", function onReady() {
              el.removeEventListener("loadedmetadata", onReady);
              var q = el.play();
              if (q && q.catch) q.catch(function () {});
            });
          });
        }
      } else if (el.classList && el.classList.contains("v-embed") && !el.getAttribute("data-loaded")) {
        var id = card.getAttribute("data-video") || "";
        var titleEl = card.querySelector(".v-title");
        el.setAttribute("data-loaded", "1");
        el.innerHTML = '<iframe src="https://www.youtube.com/embed/' +
          encodeURIComponent(id) +
          '?autoplay=1&mute=1&loop=1&playlist=' + encodeURIComponent(id) +
          '&controls=0&playsinline=1&rel=0" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen title="' +
          (titleEl ? titleEl.textContent.replace(/"/g, "&quot;") : "Video") +
          '"></iframe>';
      }
    }

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var idx = cards.indexOf(entry.target);
          var el = mediaEls[idx];
          if (entry.isIntersecting) {
            activate(el, entry.target);
          } else if (el && el.tagName === "VIDEO") {
            el.pause();
          }
        });
      }, { rootMargin: "250px 0px", threshold: 0.1 });

      cards.forEach(function (card) { io.observe(card); });
    } else {
      cards.forEach(function (card, i) { activate(mediaEls[i], card); });
    }
  }

  setupVideoCards();

  /* ---------- keyboard ---------- */
  document.addEventListener("keydown", function (e) {
    if (lightbox && lightbox.classList.contains("is-open")) {
      if (e.key === "Escape") closeLightbox();
      if (e.key === "ArrowRight") stepLightbox(1);
      if (e.key === "ArrowLeft") stepLightbox(-1);
    }
  });
})();