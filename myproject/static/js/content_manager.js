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

    /* ---------- smart image upload (stay under the serverless 4.5 MB cap) ---------- */
    var SERVERLESS_FILE_LIMIT = 4.0 * 1024 * 1024; // Vercel rejects larger bodies with 413
    var IMAGE_BUDGET = 2.5 * 1024 * 1024;          // keep image bytes comfortably under the cap
    var MAX_DIMENSION = 2048;                      // resize longest edge to 2048 px max

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
        return { blob: blob, type: blob.type };
      });
    }

    function statusEl(input) {
      var wrap = input.closest(".ap-mfield");
      if (!wrap) return null;
      var note = wrap.querySelector(".ap-optimize");
      if (!note) {
        note = document.createElement("p");
        note.className = "ap-help ap-optimize";
        note.style.display = "none";
        wrap.appendChild(note);
      }
      return note;
    }

    function setStatus(input, message, isError) {
      var note = statusEl(input);
      if (!note) return;
      note.textContent = message || "";
      note.classList.toggle("is-error", !!isError);
      note.style.display = message ? "" : "none";
    }

    function clearInput(input) {
      try {
        var dt = new DataTransfer();
        input.files = dt.files;
      } catch (err) {
        input.value = "";
      }
    }

    function attachUploadGuard(input) {
      input.addEventListener("change", function () {
        var file = input.files && input.files[0];
        if (!file) { setStatus(input, "", false); return; }

        var isAutoImage = /^image\/(jpeg|png|webp)$/i.test(file.type);
        if (!isAutoImage) {
          if (file.size > SERVERLESS_FILE_LIMIT) {
            setStatus(
              input,
              "This " + fmt(file.size) + " file is too large for the current upload path (max ~4 MB). Please choose a smaller file or compress it first.",
              true
            );
            clearInput(input);
          } else {
            setStatus(input, "Ready to upload (" + fmt(file.size) + ").", false);
          }
          return;
        }

        if (file.size <= IMAGE_BUDGET) {
          setStatus(input, "Ready to upload (" + fmt(file.size) + ").", false);
          return;
        }

        setStatus(input, "Optimizing image\u2026", false);
        loadImage(file)
          .then(function (img) {
            return compressImage(file, img);
          })
          .then(function (out) {
            if (!out) {
              setStatus(input, "Couldn't shrink this image under the upload limit. Please pick a smaller version.", true);
              clearInput(input);
              return;
            }
            var ext = out.type === "image/webp" ? "webp" : "jpg";
            var name = (file.name || "image").replace(/\.[^.]+$/, "").concat("." + ext);
            var optimized = new File([out.blob], name, { type: out.type });
            var dt = new DataTransfer();
            dt.items.add(optimized);
            input.files = dt.files;
            setStatus(input, "Optimized " + fmt(file.size) + " \u2192 " + fmt(optimized.size) + ".", false);
          })
          .catch(function () {
            if (file.size > SERVERLESS_FILE_LIMIT) {
              setStatus(input, "Couldn't read this image (unsupported format). Please upload a JPEG/PNG under ~4 MB.", true);
              clearInput(input);
            } else {
              setStatus(input, "Uploaded as-is (" + fmt(file.size) + ").", false);
            }
          });
      });
    }

    var form = document.querySelector(".ap-cm-form");
    if (form) {
      Array.prototype.forEach.call(form.querySelectorAll('input[type="file"]'), function (input) {
        if (input.dataset.videoDirect === "1") {
          attachVideoDirect(input, form);
        } else {
          attachUploadGuard(input);
        }
      });
    }

    /* ---------- direct browser→Cloudinary video upload ---------- */
    // Sends video bytes straight to Cloudinary (no size limit), bypassing
    // Vercel's ~4.5 MB serverless request cap. Stores the returned public_id
    // in the hidden <name>_direct field, which the server saves as a reference.
    function attachVideoDirect(input, form) {
      var cfg = window.CLOUDINARY_CONFIG || {};
      var hidden = form.querySelector('[name="' + input.name + '_direct"]');
      var folder = input.dataset.folder || "videos";

      function fail(msg) {
        if (hidden) hidden.value = "";
        setStatus(input, msg, true);
        clearInput(input);
      }

      input.addEventListener("change", function () {
        var file = input.files && input.files[0];
        if (hidden) hidden.value = "";
        if (!file) {
          if (!input.dataset.hasVideo) setStatus(input, "", false);
          return;
        }
        if (!cfg.cloudName || !cfg.uploadPreset) {
          fail("Direct upload is not configured yet. Add the Cloudinary upload preset and retry.");
          return;
        }

        setStatus(input, "Uploading " + fmt(file.size) + " to Cloudinary\u2026", false);
        var fd = new FormData();
        fd.append("file", file);
        fd.append("upload_preset", cfg.uploadPreset);
        fd.append("folder", folder);

        var xhr = new XMLHttpRequest();
        xhr.open("POST", "https://api.cloudinary.com/v1_1/" + cfg.cloudName + "/video/upload");
        xhr.upload.onprogress = function (e) {
          if (e.lengthComputable) {
            setStatus(input, "Uploading " + Math.round((e.loaded / e.total) * 100) + "%", false);
          }
        };
        xhr.onload = function () {
          var ok = xhr.status >= 200 && xhr.status < 300;
          var publicId = "";
          if (ok) {
            try {
              publicId = (JSON.parse(xhr.responseText) || {}).public_id || "";
            } catch (err) {}
          }
          if (publicId) {
            if (hidden) hidden.value = publicId;
            input.dataset.hasVideo = "1";
            clearInput(input);
            setStatus(input, "Video uploaded \u2713  (" + fmt(file.size) + ", full quality).", false);
          } else {
            fail("Upload failed (" + xhr.status + "). Please retry or use a smaller video.");
          }
        };
        xhr.onerror = function () {
          fail("Upload failed — check your connection and retry.");
        };
        xhr.send(fd);
      });
    }
  });
})();
