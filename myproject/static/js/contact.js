/* contact.js — enquiry form interactions and AJAX submit */
(function () {
  "use strict";

  var form = document.getElementById("enquiryForm");
  var submitBtn = document.getElementById("enquirySubmit");
  var hint = document.querySelector("[data-form-hint]");
  var panel = document.getElementById("formPanel");

  if (!form) return;

  // Phone field: digits, spaces, plus and hyphen only.
  var phone = document.getElementById("id_phone");
  if (phone) {
    phone.addEventListener("input", function () {
      phone.value = phone.value.replace(/[^\d+\s-]/g, "").slice(0, 16);
    });
  }

  form.addEventListener("submit", function (event) {
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    event.preventDefault();

    var xhr = new XMLHttpRequest();
    xhr.open("POST", form.getAttribute("action"), true);
    xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
    xhr.setRequestHeader("X-CSRFToken", document.querySelector("[name=csrfmiddlewaretoken]").value);
    xhr.setRequestHeader("Accept", "application/json");
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Sending\u2026";
    }

    xhr.onload = function () {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = "Send Enquiry"; }
      var data = null;
      try { data = JSON.parse(xhr.responseText); } catch (e) { data = null; }

      if (xhr.status === 200 && data && data.ok) {
        if (panel) {
          panel.innerHTML =
            '<div class="contact-success">' +
              '<p class="eyebrow eyebrow--gold">Received with love</p>' +
              '<h2 class="section-title">Thank you! <em>We&rsquo;re on it.</em></h2>' +
              '<p class="contact-success-text">Your enquiry is safe with us. We&rsquo;ll call you back within a few hours to talk dates, venues and the little details that matter.</p>' +
              '<div class="contact-success-actions">' +
                '<a class="btn btn--gold btn--lg" href="' + (data.wa_link || "") + '" target="_blank" rel="noopener">Continue on WhatsApp</a>' +
                '<a class="btn btn--ghost btn--lg" href="/contact/">Send another enquiry</a>' +
              '</div>' +
            '</div>';
          panel.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      } else {
        if (hint) {
          var firstError = data && data.errors ? Object.keys(data.errors)[0] : null;
          hint.textContent = firstError
            ? "Please check the " + firstError.replace(/_/g, " ") + " field."
            : "Something went wrong — please try again or WhatsApp us.";
        }
      }
    };

    xhr.onerror = function () {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = "Send Enquiry"; }
      if (hint) hint.textContent = "Please check your connection and try again.";
    };

    xhr.send(new URLSearchParams(new FormData(form)).toString());
  });
})();