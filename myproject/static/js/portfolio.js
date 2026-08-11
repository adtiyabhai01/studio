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

  /* ---------- video modal ---------- */
  var videoCards = Array.prototype.slice.call(document.querySelectorAll(".v-card"));
  var videoModal = document.getElementById("videoModal");
  var videoModalFrame = document.getElementById("videoModalFrame");
  var videoModalClose = document.getElementById("videoModalClose");

  function openVideoModal(card) {
    if (!videoModal || !videoModalFrame) return;
    videoModalFrame.innerHTML = "";
    var embedId = card.getAttribute("data-video") || "";
    var src = card.getAttribute("data-src") || "";
    if (embedId) {
      var iframe = document.createElement("iframe");
      iframe.src = "https://www.youtube.com/embed/" + embedId + "?autoplay=1&rel=0";
      iframe.setAttribute("frameborder", "0");
      iframe.setAttribute("allow", "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture");
      iframe.setAttribute("allowfullscreen", "");
      videoModalFrame.appendChild(iframe);
    } else if (src) {
      var videoEl = document.createElement("video");
      videoEl.src = src;
      videoEl.controls = true;
      videoEl.autoplay = true;
      videoModalFrame.appendChild(videoEl);
    } else {
      return;
    }
    videoModal.classList.add("is-open");
    videoModal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeVideoModal() {
    if (!videoModal) return;
    videoModal.classList.remove("is-open");
    videoModal.setAttribute("aria-hidden", "true");
    if (videoModalFrame) videoModalFrame.innerHTML = "";
    document.body.style.overflow = "";
  }

  videoCards.forEach(function (card) {
    card.addEventListener("click", function () {
      openVideoModal(card);
    });
  });

  if (videoModalClose) videoModalClose.addEventListener("click", closeVideoModal);
  if (videoModal) {
    videoModal.addEventListener("click", function (e) {
      if (e.target === videoModal) closeVideoModal();
    });
  }

  /* ---------- keyboard ---------- */
  document.addEventListener("keydown", function (e) {
    if (lightbox && lightbox.classList.contains("is-open")) {
      if (e.key === "Escape") closeLightbox();
      if (e.key === "ArrowRight") stepLightbox(1);
      if (e.key === "ArrowLeft") stepLightbox(-1);
    } else if (videoModal && videoModal.classList.contains("is-open")) {
      if (e.key === "Escape") closeVideoModal();
    }
  });
})();