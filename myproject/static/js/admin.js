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
  });
})();