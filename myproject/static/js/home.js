/* home.js — hero video fallback, animated counters, testimonial slider */
(function () {
  "use strict";

  // ---- Hero video: fade it in over the poster/fallback once it can play.
  // Safety net: if "canplay" never fires (slow net, data-saver, autoplay
  // blockers, or the event racing past this listener on a cached video),
  // reveal it after a short timeout so the hero is never left blank.
  (function heroFallback() {
    var video = document.querySelector(".hero-video");
    if (!video) return;
    var media = video.closest(".hero-media");
    var hasBase = media && media.querySelector(".hero-img");
    video.addEventListener("error", function () {
      video.style.display = "none";
    });
    if (!hasBase) {
      video.style.opacity = "1";
      return;
    }
    var revealed = false;
    function reveal() {
      if (revealed) return;
      revealed = true;
      video.style.opacity = "1";
    }
    video.style.opacity = "0";
    video.style.transition = "opacity .8s ease";
    video.addEventListener("canplay", reveal);
    video.addEventListener("playing", reveal);
    setTimeout(reveal, 4000);
  })();

  // ---- Animated counters.
  var counters = document.querySelectorAll(".stat-num[data-count]");
  function animateCounter(el) {
    var target = parseInt(el.getAttribute("data-count"), 10) || 0;
    if (!target) {
      el.textContent = "0";
      return;
    }
    var suffix = el.getAttribute("data-suffix") || "";
    var duration = 1600;
    var start = null;
    function tick(now) {
      if (start === null) start = now;
      var p = Math.min((now - start) / duration, 1);
      el.textContent = Math.floor(target * (0.35 + 0.65 * p)).toLocaleString("en-IN") + suffix;
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = target.toLocaleString("en-IN") + suffix;
    }
    requestAnimationFrame(tick);
  }

  if ("IntersectionObserver" in window && counters.length) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );
    counters.forEach(function (el) {
      io.observe(el);
    });
  } else {
    counters.forEach(animateCounter);
  }

  // ---- Testimonial slider.
  var slider = document.querySelector("[data-slider]");
  if (slider) {
    var track = slider.querySelector("[data-slider-track]");
    var dots = Array.prototype.slice.call(slider.querySelectorAll("[data-dot]"));
    var slides = Array.prototype.slice.call(track.children);
    if (slides.length < 2) return;
    var index = 0;
    var timer = null;

    function goTo(i) {
      index = (i + slides.length) % slides.length;
      track.style.transform = "translateX(-" + index * 100 + "%)";
      dots.forEach(function (d, di) {
        d.classList.toggle("is-active", di === index);
      });
    }
    function next() {
      goTo(index + 1);
    }

    dots.forEach(function (d, di) {
      d.addEventListener("click", function () {
        goTo(di);
        restart();
      });
    });

    function restart() {
      if (timer) clearInterval(timer);
      timer = setInterval(next, 5200);
    }
    restart();

    slider.addEventListener("mouseenter", function () {
      if (timer) clearInterval(timer);
    });
    slider.addEventListener("mouseleave", restart);

    // Swipe support for touch devices.
    var startX = null;
    slider.addEventListener("touchstart", function (e) {
      startX = e.touches[0].clientX;
    }, { passive: true });
    slider.addEventListener("touchend", function (e) {
      if (startX === null) return;
      var dx = e.changedTouches[0].clientX - startX;
      goTo(index + (dx < 0 ? 1 : -1));
      startX = null;
      restart();
    }, { passive: true });
  }

  // ---- Hero parallax — media lags behind, content drifts ahead for depth.
  (function heroParallax() {
    var media = document.querySelector(".hero-media");
    var content = document.querySelector(".hero-content");
    if (!media) return;
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    var ticking = false;
    function update() {
      ticking = false;
      var y = window.pageYOffset || document.documentElement.scrollTop || 0;
      if (y > window.innerHeight * 1.3) return;
      media.style.transform = "translateY(" + (y * 0.32).toFixed(1) + "px)";
      if (content) content.style.transform = "translateY(" + (y * -0.14).toFixed(1) + "px)";
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener("resize", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  })();
})();