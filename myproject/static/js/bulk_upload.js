/* bulk_upload.js — multi-photo upload, one file per request (Vercel 4.5MB safe). */
(function () {
  "use strict";

  function onReady(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  onReady(function () {
    var form = document.getElementById("bulkForm");
    if (!form) return;
    var drop = document.getElementById("apDrop");
    var input = document.getElementById("apFiles");
    var browse = document.getElementById("apBrowse");
    var preview = document.getElementById("apPreview");
    var barWrap = document.getElementById("apBarWrap");
    var bar = document.getElementById("apBar");
    var status = document.getElementById("apStatus");
    var btn = document.getElementById("apUploadBtn");

    var IMAGE_BUDGET = 2.5 * 1024 * 1024;
    var MAX_DIMENSION = 2048;
    var files = [];

    function fmt(b) {
      if (b >= 1024 * 1024) return (b / (1024 * 1024)).toFixed(1) + " MB";
      return Math.max(1, Math.round(b / 1024)) + " KB";
    }
    function csrf() {
      var m = document.querySelector('#bulkForm input[name="csrfmiddlewaretoken"]');
      return m ? m.value : "";
    }
    function loadImage(file) {
      return new Promise(function (res, rej) {
        var url = URL.createObjectURL(file);
        var img = new Image();
        img.onload = function () { URL.revokeObjectURL(url); res(img); };
        img.onerror = function () { URL.revokeObjectURL(url); rej(new Error("decode")); };
        img.src = url;
      });
    }
    function draw(img, whiteBg) {
      var s = Math.min(1, MAX_DIMENSION / Math.max(img.naturalWidth, img.naturalHeight));
      var c = document.createElement("canvas");
      c.width = Math.max(1, Math.round(img.naturalWidth * s));
      c.height = Math.max(1, Math.round(img.naturalHeight * s));
      var ctx = c.getContext("2d");
      if (whiteBg) { ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, c.width, c.height); }
      ctx.drawImage(img, 0, 0, c.width, c.height);
      return c;
    }
    function toBlob(canvas, type, q) {
      return new Promise(function (res, rej) {
        canvas.toBlob(function (b) { b ? res(b) : rej(new Error("encode")); }, type, q);
      });
    }
    function optimize(file) {
      if (!/^image\/(jpeg|png|webp)$/i.test(file.type)) return Promise.resolve(file);
      if (file.size <= IMAGE_BUDGET) return Promise.resolve(file);
      return loadImage(file).then(function (img) {
        var isPng = /^image\/png$/i.test(file.type);
        var formats = isPng ? ["image/webp", "image/jpeg"] : ["image/jpeg"];
        var chain = Promise.resolve(null);
        formats.forEach(function (type) {
          chain = chain.then(function (done) {
            if (done) return done;
            var canvas = type === "image/jpeg" ? draw(img, true) : draw(img, false);
            var qs = [0.85, 0.75, 0.65, 0.55, 0.45];
            var inner = Promise.resolve(null);
            qs.forEach(function (q) {
              inner = inner.then(function (hit) {
                if (hit) return hit;
                return toBlob(canvas, type, q).then(function (blob) {
                  return blob.size <= IMAGE_BUDGET ? blob : null;
                });
              });
            });
            return inner.then(function (blob) { return blob ? { blob: blob, type: type } : null; });
          });
        });
        return chain.then(function (out) {
          if (!out || out.blob.size >= file.size) return file;
          var ext = out.type === "image/webp" ? "webp" : "jpg";
          var name = (file.name || "photo").replace(/\.[^.]+$/, "") + "." + ext;
          return new File([out.blob], name, { type: out.type });
        });
      }).catch(function () { return file; });
    }

    function render() {
      preview.innerHTML = "";
      preview.hidden = files.length === 0;
      files.forEach(function (f, i) {
        var card = document.createElement("div");
        card.className = "ap-bulk-card";
        var url = URL.createObjectURL(f);
        card.innerHTML = '<img alt=""><span></span><button type="button" aria-label="Remove">✕</button>';
        card.querySelector("img").src = url;
        card.querySelector("span").textContent = f.name + " (" + fmt(f.size) + ")";
        card.querySelector("button").addEventListener("click", function () {
          files.splice(i, 1);
          render();
        });
        preview.appendChild(card);
      });
    }

    function addFiles(list) {
      Array.prototype.forEach.call(list || [], function (f) {
        if (/^image\//i.test(f.type)) files.push(f);
      });
      render();
    }

    if (browse) browse.addEventListener("click", function () { input.click(); });
    if (input) input.addEventListener("change", function () { addFiles(input.files); input.value = ""; });
    ["dragover", "dragenter"].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("is-drag"); });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove("is-drag"); });
    });
    drop.addEventListener("drop", function (e) {
      if (e.dataTransfer && e.dataTransfer.files) addFiles(e.dataTransfer.files);
    });

    form.addEventListener("submit", function (e) {
      // No JS files staged -> let classic form submit handle it (or show error).
      if (!files.length) return;
      e.preventDefault();
      if (!window.fetch || !window.FormData) { form.submit(); return; }

      btn.disabled = true;
      barWrap.hidden = false;
      var done = 0, ok = 0, fail = 0;
      var category = form.querySelector('select[name="category"]').value;
      var featured = form.querySelector('input[name="is_featured"]').checked ? "on" : "";
      var active = form.querySelector('input[name="is_active"]').checked ? "on" : "";

      function tick() {
        var pct = files.length ? Math.round((done / files.length) * 100) : 0;
        bar.style.width = pct + "%";
        status.textContent = "Uploading " + done + "/" + files.length + " — ✓ " + ok + ", ✕ " + fail;
      }
      tick();

      var seq = Promise.resolve();
      files.forEach(function (file) {
        seq = seq.then(function () {
          return optimize(file).then(function (finalFile) {
            var fd = new FormData();
            fd.append("image", finalFile, finalFile.name);
            fd.append("category", category);
            fd.append("is_featured", featured);
            fd.append("is_active", active);
            fd.append("csrfmiddlewaretoken", csrf());
            return fetch(window.location.pathname, {
              method: "POST",
              body: fd,
              credentials: "same-origin",
              headers: { "X-Requested-With": "XMLHttpRequest" }
            }).then(function (r) { return r.json().then(function (j) { return { s: r.ok, j: j }; }); })
              .then(function (out) { out.s && out.j.ok ? ok++ : fail++; })
              .catch(function () { fail++; })
              .then(function () { done++; tick(); });
          });
        });
      });
      seq.then(function () {
        btn.disabled = false;
        status.textContent = "Done — ✓ " + ok + " uploaded" + (fail ? ", ✕ " + fail + " failed" : "") + ".";
        if (ok && !fail) window.location.href = "/admin-portal/content/portfolio-photos/";
      });
    });
  });
})();
