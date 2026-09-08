/* =========================================================
   NOURISH PATIENT DASHBOARD LOGIC
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

  const connectButtons = document.querySelectorAll(".dash-card__connect-btn");

  connectButtons.forEach(function (button) {
    button.addEventListener("click", function () {

      const card = button.closest(".dash-card");
      const type = button.dataset.connect;

      // Placeholder: simulate a successful wearable connection
      button.textContent = "Connecting...";
      button.classList.add("btn-submitting");

      setTimeout(function () {
        card.classList.remove("dash-card--not-connected");

        const status = card.querySelector(".dash-card__status");
        if (status) {
          if (type === "sleep") {
            status.textContent = "7h 20m last night";
          } else if (type === "exercise") {
            status.textContent = "32 min activity today";
          }
        }

        button.remove();

        // TODO: replace with real Google Fit / Health Connect API call
      }, 1000);

    });
  });

});
