/* portfolio.js — gallery filtering, premium media lightbox, autoplay films.
   Loaded on the portfolio page AND the service pages (shared media). */
(function () {
  "use strict";

  /* ---------- category filtering (portfolio + service pages) ---------- */
  var filterBars = Array.prototype.slice.call(document.querySelectorAll(".filterbar"));
  filterBars.forEach(function (bar) {
    var buttons = Array.prototype.slice.call(bar.querySelectorAll(".filter"));
    var grids = Array.prototype.slice.call(document.querySelectorAll("[data-filter-grid]"));
    var items = [];

    grids.forEach(function (grid) {
      Array.prototype.slice.call(grid.querySelectorAll("[data-cat]")).forEach(function (el) {
        items.push(el);
      });
      if (!grid.querySelector(".g-empty")) {
        var empty = document.createElement("p");
        empty.className = "g-empty is-hidden";
        empty.textContent = "Nothing in this category yet — check back soon.";
        grid.appendChild(empty);
      }
    });

    if (!buttons.length || !items.length) return;

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var f = btn.getAttribute("data-filter") || "all";
        buttons.forEach(function (b) {
          b.classList.toggle("filter--active", b === btn);
        });
        items.forEach(function (item) {
          var cat = item.getAttribute("data-cat") || "all";
          var show = f === "all" || cat === f;
          item.classList.toggle("is-hidden", !show);
          if (show) item.classList.add("is-shown");
          else item.classList.remove("is-shown");
        });
        grids.forEach(function (grid) {
          var emptyEl = grid.querySelector(".g-empty");
          var shown = grid.querySelectorAll("[data-cat]:not(.is-hidden)").length;
          if (emptyEl) emptyEl.classList.toggle("is-hidden", shown > 0);
        });
      });
    });
  });

  /* ---------- unified media index (photos + films, DOM order) ---------- */
  var lightbox = document.getElementById("lightbox");
  var lightboxStage = document.getElementById("lightboxStage");
  var lightboxImg = document.getElementById("lightboxImg");
  var lightboxCap = document.getElementById("lightboxCap");
  var lightboxClose = document.getElementById("lightboxClose");
  var lightboxPrev = document.getElementById("lightboxPrev");
  var lightboxNext = document.getElementById("lightboxNext");

  var mediaItems = Array.prototype.slice
    .call(document.querySelectorAll("figure.g-item"))
    .filter(function (fig) {
      return fig.querySelector("[data-lightbox]") || fig.classList.contains("g-item--video");
    })
    .map(function (fig) {
      var btn = fig.querySelector("[data-lightbox]");
      if (btn) {
        return {
          type: "photo",
          src: btn.getAttribute("data-lightbox"),
          caption: btn.getAttribute("data-caption") || "",
          fig: fig,
        };
      }
      return {
        type: "video",
        src: fig.getAttribute("data-video-src") || "",
        embed: fig.getAttribute("data-embed") || "",
        caption: fig.getAttribute("data-caption") || "",
        fig: fig,
      };
    });

  var currentIndex = 0;

  function pauseAllPreviews() {
    document.querySelectorAll(".g-item--video.is-previewing").forEach(function (el) {
      el.classList.remove("is-previewing");
      var v = el.querySelector(".v-preview");
      if (v) v.pause();
    });
  }

  function openMedia(index) {
    var item = mediaItems[index];
    if (!item || !lightbox || !lightboxStage) return;
    currentIndex = index;
    pauseAllPreviews();

    lightboxStage.innerHTML = "";
    if (item.type === "photo") {
      lightbox.classList.remove("is-video");
      lightboxStage.appendChild(lightboxImg);
      lightboxImg.src = item.src;
      lightboxImg.alt = item.caption || "";
      if (lightboxCap) lightboxCap.textContent = item.caption || "";
    } else {
      lightbox.classList.add("is-video");
      if (lightboxCap) lightboxCap.textContent = item.caption || "";
      var media;
      if (item.embed) {
        media = document.createElement("iframe");
        media.setAttribute("frameborder", "0");
        media.setAttribute(
          "allow",
          "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        );
        media.setAttribute("allowfullscreen", "");
        media.src =
          "https://www.youtube.com/embed/" + encodeURIComponent(item.embed) + "?autoplay=1&rel=0";
      } else if (item.src) {
        media = document.createElement("video");
        media.controls = true;
        media.loop = true;
        media.autoplay = true;
        media.setAttribute("playsinline", "");
        media.src = item.src;
      }
      if (media) lightboxStage.appendChild(media);
    }

    lightbox.classList.add("is-open");
    lightbox.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeMedia() {
    if (!lightbox) return;
    lightbox.classList.remove("is-open");
    lightbox.setAttribute("aria-hidden", "true");
    pauseAllPreviews();
    if (lightboxStage) lightboxStage.innerHTML = "";
    document.body.style.overflow = "";
    resumeGridVideos();
  }

  function stepMedia(dir) {
    if (!mediaItems.length) return;
    openMedia((currentIndex + dir + mediaItems.length) % mediaItems.length);
  }

  mediaItems.forEach(function (item, i) {
    item.fig.addEventListener("click", function () {
      openMedia(i);
    });
  });

  if (lightboxClose) lightboxClose.addEventListener("click", closeMedia);
  if (lightboxPrev) lightboxPrev.addEventListener("click", function () { stepMedia(-1); });
  if (lightboxNext) lightboxNext.addEventListener("click", function () { stepMedia(1); });
  if (lightbox) {
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox) closeMedia();
    });
  }

  /* ---------- inline autoplay for films in the mixed grid ----------
     Grid films autoplay muted + looped as soon as they enter the viewport
     (desktop and mobile) — no click needed. Tapping one opens the fullscreen
     lightbox with sound for full playback. */
  var gridVideoItems = Array.prototype.slice.call(
    document.querySelectorAll(".g-item--video")
  );

  gridVideoItems.forEach(function (fig) {
    var src = fig.getAttribute("data-video-src") || "";
    var poster = fig.querySelector(".g-item-img--video");
    var posterSrc = poster && poster.tagName === "IMG" ? poster.getAttribute("src") : "";
    if (!src || fig.getAttribute("data-embed")) return;

    var video = document.createElement("video");
    video.className = "v-preview";
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    video.setAttribute("playsinline", "");
    video.preload = "none";
    if (posterSrc) video.setAttribute("poster", posterSrc);
    video.src = src;
    fig.appendChild(video);
  });

  function playGridVideo(fig) {
    var v = fig.querySelector(".v-preview");
    if (!v) return;
    fig.classList.add("is-previewing");
    v.preload = "auto";
    var p = v.play();
    if (p && p.catch) {
      p.catch(function () {
        v.addEventListener("loadedmetadata", function onReady() {
          v.removeEventListener("loadedmetadata", onReady);
          var q = v.play();
          if (q && q.catch) q.catch(function () {});
        });
      });
    }
  }

  function resumeGridVideos() {
    gridVideoItems.forEach(function (fig) {
      var v = fig.querySelector(".v-preview");
      if (!v) return;
      var r = fig.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0) playGridVideo(fig);
    });
  }

  if ("IntersectionObserver" in window && gridVideoItems.length) {
    var gridIo = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var v = entry.target.querySelector(".v-preview");
        if (!v) return;
        if (entry.isIntersecting) {
          playGridVideo(entry.target);
        } else {
          entry.target.classList.remove("is-previewing");
          v.pause();
        }
      });
    }, { rootMargin: "250px 0px", threshold: 0.1 });
    gridVideoItems.forEach(function (fig) { gridIo.observe(fig); });
  } else if (gridVideoItems.length) {
    gridVideoItems.forEach(function (fig) {
      if (!fig.getAttribute("data-embed")) playGridVideo(fig);
    });
  }

  /* ---------- autoplay film cards on service pages ----------
     Uploaded films and YouTube clips autoplay muted + looped while in view,
     so no click is required. Videos only load as they approach the viewport. */
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
      if (e.key === "Escape") closeMedia();
      if (e.key === "ArrowRight") stepMedia(1);
      if (e.key === "ArrowLeft") stepMedia(-1);
    }
  });
})();