/* =========================================================
   NOURISH MANAGE DOCTOR ACCESS LOGIC
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {
  
    // --- Toggle Switch Logic ---
    const toggles = document.querySelectorAll(".access-toggle");
  
    toggles.forEach(function (toggle) {
      toggle.addEventListener("change", function () {
        
        const isChecked = toggle.checked;
        const doctorCard = toggle.closest(".doctor-card");
        const doctorName = doctorCard.dataset.doctorName;
        
        const labelEl = document.getElementById(toggle.dataset.targetLabel);
        const msgEl = document.getElementById(toggle.dataset.targetMsg);
        
        if (isChecked) {
          labelEl.textContent = "Access Granted";
          msgEl.textContent = `Dr. ${doctorName} can now view your tracked health data.`;
          msgEl.classList.remove("revoked");
        } else {
          labelEl.textContent = "No Access";
          msgEl.textContent = `Dr. ${doctorName} no longer has access to your data.`;
          msgEl.classList.add("revoked");
        }
      });
    });
  
    // --- Add Doctor Inline Form Logic ---
    const showAddBtn = document.getElementById("show-add-doctor-btn");
    const addDoctorForm = document.getElementById("add-doctor-form");
    const submitDoctorBtn = document.getElementById("submit-doctor-btn");
    const doctorInput = document.getElementById("doctor-code");
  
    showAddBtn.addEventListener("click", function () {
      showAddBtn.classList.add("hidden");
      addDoctorForm.classList.remove("hidden");
      addDoctorForm.classList.add("visible");
      doctorInput.focus();
    });
  
    submitDoctorBtn.addEventListener("click", function () {
      if (doctorInput.value.trim() !== "") {
        submitDoctorBtn.textContent = "Request Sent!";
        submitDoctorBtn.classList.add("btn-submitting");
        
        setTimeout(function() {
          doctorInput.value = "";
          submitDoctorBtn.textContent = "Send Request";
          
          submitDoctorBtn.classList.remove("btn-submitting");
          addDoctorForm.classList.remove("visible");
          addDoctorForm.classList.add("hidden");
          showAddBtn.classList.remove("hidden");
          
        }, 1500);
      }
    });
  
  });