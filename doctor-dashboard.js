/* =========================================================
   NOURISH DOCTOR DASHBOARD LOGIC
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

  const actionButtons = document.querySelectorAll(".action-btn[data-patient]");

  actionButtons.forEach(function (button) {
    button.addEventListener("click", function () {

      const patientId = button.dataset.patient;
      const details = document.getElementById("details-" + patientId);

      if (!details) return;

      const isHidden = details.classList.contains("hidden");

      // Close any other open detail panels
      document.querySelectorAll(".patient-details").forEach(function (panel) {
        panel.classList.add("hidden");
      });

      if (isHidden) {
        details.classList.remove("hidden");
        button.textContent = "Hide Dashboard";
      } else {
        button.textContent = "View Dashboard";
      }

      // Reset other buttons' text
      actionButtons.forEach(function (btn) {
        if (btn !== button) {
          btn.textContent = "View Dashboard";
        }
      });

    });
  });

});
