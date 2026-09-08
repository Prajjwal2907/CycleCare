document.addEventListener("DOMContentLoaded", async function () {
  const doctorList = document.querySelector(".doctor-list");
  const showAddBtn = document.getElementById("show-add-doctor-btn");
  const addDoctorForm = document.getElementById("add-doctor-form");
  const submitDoctorBtn = document.getElementById("submit-doctor-btn");
  const doctorInput = document.getElementById("doctor-code");

  function render(grants) {
    doctorList.innerHTML = grants.length ? grants.map((grant) => {
      const name = grant.doctor_name || grant.doctor?.user?.full_name || grant.doctor?.user?.email || "Doctor";
      const code = grant.doctor_code || grant.doctor?.doctor_code || "";
      const active = grant.is_active;
      return `<div class="doctor-card" data-grant-id="${grant.id}" data-doctor-code="${code}">
        <div class="doctor-header"><div class="doctor-info"><h3>${name}</h3><p>${active ? "Active consent" : "Revoked consent"}</p></div>
        <div class="toggle-wrapper"><span class="toggle-label">${active ? "Access Granted" : "No Access"}</span>
        <label class="switch"><input type="checkbox" class="access-toggle" ${active ? "checked" : ""}><span class="slider"></span></label></div></div>
        <p class="access-status-text ${active ? "" : "revoked"}">${active ? "This doctor can view your tracked health data." : "Access has been revoked."}</p>
      </div>`;
    }).join("") : "<p>No doctors connected yet.</p>";

    doctorList.querySelectorAll(".access-toggle").forEach((toggle) => {
      toggle.addEventListener("change", async function () {
        const card = toggle.closest(".doctor-card");
        toggle.disabled = true;
        try {
          if (toggle.checked) await CycleCareAPI.grantConsent({ doctor_code: card.dataset.doctorCode });
          else await CycleCareAPI.revokeConsent({ grant_id: card.dataset.grantId });
          render(CycleCareAPI.unwrap(await CycleCareAPI.consents()));
        } catch (error) {
          toggle.checked = !toggle.checked;
          alert(error.message);
          toggle.disabled = false;
        }
      });
    });
  }

  try {
    render(CycleCareAPI.unwrap(await CycleCareAPI.consents()));
  } catch (error) {
    doctorList.innerHTML = `<p>${error.message}</p>`;
  }

  showAddBtn.addEventListener("click", function () {
    showAddBtn.classList.add("hidden");
    addDoctorForm.classList.remove("hidden");
    addDoctorForm.classList.add("visible");
    doctorInput.focus();
  });

  submitDoctorBtn.addEventListener("click", async function () {
    const code = doctorInput.value.trim();
    if (!code) return;
    submitDoctorBtn.disabled = true;
    submitDoctorBtn.textContent = "Saving...";
    try {
      await CycleCareAPI.grantConsent({ doctor_code: code });
      doctorInput.value = "";
      addDoctorForm.classList.add("hidden");
      showAddBtn.classList.remove("hidden");
      render(CycleCareAPI.unwrap(await CycleCareAPI.consents()));
    } catch (error) {
      alert(error.message);
    } finally {
      submitDoctorBtn.disabled = false;
      submitDoctorBtn.textContent = "Send Request";
    }
  });
});
