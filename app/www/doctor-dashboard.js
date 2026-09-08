document.addEventListener("DOMContentLoaded", async function () {
  const user = CycleCareAPI.getUser();
  const welcome = document.querySelector(".dashboard-welcome");
  const patientList = document.querySelector(".patient-list");
  if (welcome && user) welcome.textContent = `Welcome, Dr. ${(user.full_name || user.email || "Doctor").replace(/^Dr\. /, "")}`;

  try {
    const patients = CycleCareAPI.unwrap(await CycleCareAPI.doctorsPatients());
    patientList.innerHTML = patients.length ? patients.map((patient) => `<div class="patient-card">
      <div class="patient-summary"><div class="patient-info"><h3>${patient.full_name || patient.email}</h3><span class="status-badge status-badge--granted">Access Granted</span></div>
      <button type="button" class="auth-button action-btn" data-patient="${patient.id}">View Dashboard</button></div>
      <div class="patient-details details-grid hidden" id="details-${patient.id}"></div>
    </div>`).join("") : "<p>No patients have granted active consent.</p>";

    patientList.querySelectorAll(".action-btn[data-patient]").forEach((button) => {
      button.addEventListener("click", async function () {
        const details = document.getElementById(`details-${button.dataset.patient}`);
        const hidden = details.classList.contains("hidden");
        document.querySelectorAll(".patient-details").forEach((panel) => panel.classList.add("hidden"));
        patientList.querySelectorAll(".action-btn").forEach((item) => { item.textContent = "View Dashboard"; });
        if (!hidden) return;
        button.textContent = "Loading...";
        try {
          const dashboard = await CycleCareAPI.patientDashboard(button.dataset.patient);
          details.innerHTML = `<div class="inner-card"><h4>Cycle</h4><p>Average duration ${dashboard.cycle_summary.average_duration_days ?? 0} days; next predicted in ${dashboard.cycle_summary.days_until_next_cycle ?? "--"} days</p></div>
            <div class="inner-card"><h4>Sleep average</h4><p>${dashboard.sleep_summary.average_sleep_minutes ?? 0} minutes across ${dashboard.sleep_summary.days_tracked ?? 0} days</p></div>
            <div class="inner-card"><h4>Exercise average</h4><p>${dashboard.exercise_summary.average_activity_minutes ?? 0} minutes across ${dashboard.exercise_summary.activity_days ?? 0} days</p></div>`;
          details.classList.remove("hidden");
          button.textContent = "Hide Dashboard";
        } catch (error) {
          alert(error.message);
          button.textContent = "View Dashboard";
        }
      });
    });
  } catch (error) {
    patientList.innerHTML = `<p>${error.message}</p>`;
  }
});
