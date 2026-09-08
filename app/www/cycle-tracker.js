document.addEventListener("DOMContentLoaded", function () {
  
  // Elements
  const form = document.getElementById("cycle-form");
  const startDateInput = document.getElementById("start-date");
  const endDateInput = document.getElementById("end-date");
  const flowOptions = document.querySelectorAll(".flow-option");
  const symptomTags = document.querySelectorAll(".symptom-tag");
  
  const durationDisplay = document.getElementById("cycle-duration");
  const nextCycleDisplay = document.getElementById("next-cycle-days");

  // State Variables
  let selectedFlow = null;
  let selectedSymptoms = new Set();

  /* =========================
     FLOW INTENSITY LOGIC
     ========================= */
  flowOptions.forEach(function (option) {
    option.addEventListener("click", function () {
      // Deselect all
      flowOptions.forEach(item => item.classList.remove("selected"));
      
      // Select current
      option.classList.add("selected");
      selectedFlow = option.dataset.flow;
    });
  });

  /* =========================
     SYMPTOM TAGS LOGIC
     ========================= */
  symptomTags.forEach(function (tag) {
    tag.addEventListener("click", function () {
      const symptom = tag.dataset.symptom;
      
      if (selectedSymptoms.has(symptom)) {
        selectedSymptoms.delete(symptom);
        tag.classList.remove("selected");
      } else {
        selectedSymptoms.add(symptom);
        tag.classList.add("selected");
      }
    });
  });

  /* =========================
     DURATION CALCULATION
     ========================= */
  function calculateSummary() {
    const startVal = startDateInput.value;
    const endVal = endDateInput.value;

    if (startVal && endVal) {
      const startDate = new Date(startVal);
      const endDate = new Date(endVal);

      // Only calculate if end date is on or after start date
      if (endDate >= startDate) {
        // Calculate difference in time, then convert to days (inclusive)
        const diffTime = Math.abs(endDate - startDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
        
        durationDisplay.textContent = diffDays;
        
        nextCycleDisplay.textContent = "...";
        CycleCareAPI.cycleSummary()
          .then((summary) => {
            nextCycleDisplay.textContent = summary.days_until_next_cycle ?? "--";
          })
          .catch(() => { nextCycleDisplay.textContent = "--"; });
        return;
      }
    }
    
    // Reset if invalid or incomplete
    durationDisplay.textContent = "--";
    nextCycleDisplay.textContent = "--";
  }

  startDateInput.addEventListener("change", calculateSummary);
  endDateInput.addEventListener("change", calculateSummary);

  /* =========================
     FORM VALIDATION
     ========================= */
  function setError(id, message) {
    document.getElementById(id).textContent = message;
  }

  function clearErrors() {
    document.querySelectorAll(".error-message").forEach(el => el.textContent = "");
    document.getElementById("form-success").textContent = "";
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    clearErrors();

    const startDate = startDateInput.value;
    const endDate = endDateInput.value;
    let isValid = true;

    // Start Date Required
    if (!startDate) {
      setError("start-date-error", "Start date is required.");
      isValid = false;
    }

    // End Date Required & Chronology Check
    if (!endDate) {
      setError("end-date-error", "End date is required.");
      isValid = false;
    } else if (startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      
      if (end < start) {
        setError("end-date-error", "End date cannot be earlier than the start date.");
        isValid = false;
      }
    }

    // Success State
    if (isValid) {
      const button = form.querySelector('button[type="submit"]');
      button.disabled = true;
      button.textContent = "Saving...";
      CycleCareAPI.createCycle({
        start_date: startDate,
        end_date: endDate,
        flow_intensity: (selectedFlow || "Normal").toLowerCase(),
        symptoms: Array.from(selectedSymptoms).map((symptom) => symptom.toLowerCase())
      })
        .then((entry) => {
          durationDisplay.textContent = entry.cycle_duration;
          document.getElementById("form-success").textContent = "Cycle entry saved.";
          return CycleCareAPI.cycleSummary();
        })
        .then((summary) => { nextCycleDisplay.textContent = summary.days_until_next_cycle ?? "--"; })
        .catch((error) => setError("end-date-error", error.message))
        .finally(() => {
          button.disabled = false;
          button.textContent = "Save Entry";
        });
    }
  });

  if (CycleCareAPI.isAuthenticated()) {
    CycleCareAPI.cycleSummary().then((summary) => {
      nextCycleDisplay.textContent = summary.days_until_next_cycle ?? "--";
    }).catch(() => {});
  }
});