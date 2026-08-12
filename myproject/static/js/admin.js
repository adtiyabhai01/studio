/* admin.js — light usability touches for the Django admin CMS. */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    // Highlight rows of model list tables based on a data flag from the
    // changelist (we mark it via the model's list template where needed).
    document.querySelectorAll("#result_list tbody tr").forEach(function (row) {
      var status = row.querySelector(".column-status");
      if (status && /new/i.test(status.textContent || "")) {
        row.classList.add("enquiry-new");
        row.style.background = "rgba(178, 138, 84, 0.08)";
      }
    });

    // Auto-open the first fieldset collapsible sections that are important.
    document.querySelectorAll(".module.collapsible:first-of-type details").forEach(function (details) {
      details.open = true;
    });

    // Nice touch: confirm before deactivating featured items.
    document.querySelectorAll("select[name$='is_featured']").forEach(function (select) {
      select.addEventListener("change", function () {
        var value = select.value === "0" || select.value === "False";
        if (value && !window.confirm("Hide this from the featured sections?")) {
          select.value = select.dataset.prev || "";
        }
        select.dataset.prev = select.value;
      });
      select.dataset.prev = select.value;
    });

    /* ---------- keep uploads under the serverless 4.5 MB cap ---------- */
    var SERVERLESS_FILE_LIMIT = 4.0 * 1024 * 1024; // Vercel rejects larger bodies with 413
    var IMAGE_BUDGET = 2.5 * 1024 * 1024;          // target size after browser compression
    var MAX_DIMENSION = 2048;

    function fmt(bytes) {
      if (bytes >= 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + " MB";
      return Math.max(1, Math.round(bytes / 1024)) + " KB";
    }

    function loadImage(file) {
      return new Promise(function (resolve, reject) {
        var url = URL.createObjectURL(file);
        var img = new Image();
        img.onload = function () { URL.revokeObjectURL(url); resolve(img); };
        img.onerror = function () { URL.revokeObjectURL(url); reject(new Error("cannot-decode")); };
        img.src = url;
      });
    }

    function drawToCanvas(img, whiteBg) {
      var scale = Math.min(1, MAX_DIMENSION / Math.max(img.naturalWidth, img.naturalHeight));
      var w = Math.max(1, Math.round(img.naturalWidth * scale));
      var h = Math.max(1, Math.round(img.naturalHeight * scale));
      var canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      var ctx = canvas.getContext("2d");
      if (whiteBg) {
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, w, h);
      }
      ctx.drawImage(img, 0, 0, w, h);
      return canvas;
    }

    function toBlob(canvas, type, quality) {
      return new Promise(function (resolve, reject) {
        canvas.toBlob(function (b) {
          b ? resolve(b) : reject(new Error("encode-failed"));
        }, type, quality);
      });
    }

    function canvasSupports(canvas, type) {
      return canvas.toDataURL(type).indexOf("data:" + type) === 0;
    }

    function compressImage(file, img) {
      var isPng = /^image\/png$/i.test(file.type);
      var formats = isPng ? ["image/webp", "image/jpeg"] : ["image/jpeg"];
      var baseCanvas = drawToCanvas(img, false);
      var qualities = [0.85, 0.75, 0.65, 0.55, 0.45];

      function tryQuality(canvas, type, qi) {
        if (qi >= qualities.length) return Promise.resolve(null);
        return toBlob(canvas, type, qualities[qi]).then(function (blob) {
          return blob.size <= IMAGE_BUDGET ? blob : tryQuality(canvas, type, qi + 1);
        });
      }

      function tryFormat(fi) {
        var type = formats[fi];
        if (!type) return Promise.resolve(null);
        if (type === "image/webp" && !canvasSupports(baseCanvas, type)) {
          return tryFormat(fi + 1);
        }
        var canvas = type === "image/jpeg" ? drawToCanvas(img, true) : baseCanvas;
        return tryQuality(canvas, type, 0).then(function (blob) {
          return blob || tryFormat(fi + 1);
        });
      }

      return tryFormat(0).then(function (blob) {
        if (!blob || blob.size >= file.size) return null;
        return blob;
      });
    }

    function noteEl(input) {
      var el = document.createElement("div");
      el.style.cssText = "font-size:12px;margin-top:4px;color:#b08d57";
      input.closest(".form-row") && input.closest(".form-row").appendChild(el);
      return el;
    }

    function setNote(input, text, isError) {
      var el = input._note || (input._note = noteEl(input));
      el.textContent = text || "";
      el.style.color = isError ? "#cc6b4c" : "#b08d57";
    }

    function clearInput(input) {
      try {
        var dt = new DataTransfer();
        input.files = dt.files;
      } catch (err) {
        input.value = "";
      }
    }

    var adminForm = document.querySelector('form.enctype-multipart, form[enctype="multipart/form-data"]');
    if (adminForm) {
      Array.prototype.forEach.call(adminForm.querySelectorAll('input[type="file"]'), function (input) {
        input.addEventListener("change", function () {
          var file = input.files && input.files[0];
          if (!file) { setNote(input, "", false); return; }

          var isAutoImage = /^image\/(jpeg|png|webp)$/i.test(file.type);
          if (!isAutoImage) {
            if (file.size > SERVERLESS_FILE_LIMIT) {
              setNote(input, "Too large for the server upload limit (max ~4 MB). Pick a smaller file.", true);
              clearInput(input);
            } else {
              setNote(input, "Ready to upload (" + fmt(file.size) + ").", false);
            }
            return;
          }

          if (file.size <= IMAGE_BUDGET) {
            setNote(input, "Ready to upload (" + fmt(file.size) + ").", false);
            return;
          }

          setNote(input, "Optimizing image\u2026", false);
          loadImage(file)
            .then(function (img) { return compressImage(file, img); })
            .then(function (blob) {
              if (!blob) {
                setNote(input, "Couldn't shrink this image under the limit. Pick a smaller version.", true);
                clearInput(input);
                return;
              }
              var ext = blob.type === "image/webp" ? "webp" : "jpg";
              var name = (file.name || "image").replace(/\.[^.]+$/, "").concat("." + ext);
              var optimized = new File([blob], name, { type: blob.type });
              var dt = new DataTransfer();
              dt.items.add(optimized);
              input.files = dt.files;
              setNote(input, "Optimized " + fmt(file.size) + " \u2192 " + fmt(optimized.size) + ".", false);
            })
            .catch(function () {
              setNote(input, file.size > SERVERLESS_FILE_LIMIT
                ? "Couldn't read this image. Please upload a JPEG/PNG under ~4 MB."
                : "Uploaded as-is (" + fmt(file.size) + ").", file.size > SERVERLESS_FILE_LIMIT);
            });
        });
      });
    }
  });
})();