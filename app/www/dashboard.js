document.addEventListener("DOMContentLoaded", async function () {
  const user = CycleCareAPI.getUser();
  const welcome = document.querySelector(".dashboard-welcome");
  if (welcome && user) welcome.textContent = `Welcome back, ${(user.full_name || user.email || "there").split(" ")[0]}`;

  try {
    const summary = await CycleCareAPI.cycleSummary();
    const cycleValue = document.querySelector(".dash-card .dash-card__value");
    if (cycleValue) cycleValue.innerHTML = `Next predicted: <strong>${summary.days_until_next_cycle ?? "--"} days</strong>`;
  } catch (_) {}

  try {
    const [sleep, exercise] = await Promise.all([CycleCareAPI.sleepTrends(), CycleCareAPI.exerciseTrends()]);
    const sleepCard = document.querySelector('[data-connect="sleep"]')?.closest(".dash-card");
    const exerciseCard = document.querySelector('[data-connect="exercise"]')?.closest(".dash-card");
    const sleepRows = CycleCareAPI.unwrap(sleep);
    const exerciseRows = CycleCareAPI.unwrap(exercise);
    if (sleepRows.length && sleepCard) {
      sleepCard.querySelector(".dash-card__status").textContent = sleepRows[0].formatted_total_sleep;
      sleepCard.classList.remove("dash-card--not-connected");
    }
    if (exerciseRows.length && exerciseCard) {
      exerciseCard.querySelector(".dash-card__status").textContent = `${exerciseRows[0].duration_minutes} min activity`;
      exerciseCard.classList.remove("dash-card--not-connected");
    }
  } catch (_) {}

  document.querySelectorAll(".dash-card__connect-btn").forEach((button) => {
    button.addEventListener("click", async function () {
      const card = button.closest(".dash-card");
      button.disabled = true;
      button.textContent = "Connecting...";
      try {
        const result = await CycleCareAPI.wearableConnect("health_connect");
        window.open(result.authorization_url, "_blank", "noopener");
        card.querySelector(".dash-card__status").textContent = "Authorization started";
      } catch (error) {
        card.querySelector(".dash-card__status").textContent = error.message;
      } finally {
        button.disabled = false;
        button.textContent = "Connect Wearable";
      }
    });
  });
});
