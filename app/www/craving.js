/* =========================================================
   NOURISH CRAVING ALTERNATIVE LOGIC
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

  const cravingInput = document.getElementById("craving-input");
  const findBtn = document.getElementById("find-alternative-btn");
  const resultCard = document.getElementById("result-card");
  const resultTitle = document.getElementById("result-title");
  const resultDesc = document.getElementById("result-desc");
  const dietTag = document.getElementById("diet-tag");

  // --- UI Update Handling ---
  findBtn.addEventListener("click", async function () {
    const cravingValue = cravingInput.value;

    if (!cravingValue) {
      return; // Do nothing if input is empty
    }

    // Set Loading State
    findBtn.textContent = "Finding...";
    findBtn.classList.add("btn-submitting");
    resultCard.classList.add("hidden");

    try {
      const response = await CycleCareAPI.craving(cravingValue);
      const alternative = response.alternative;
      resultTitle.textContent = alternative.name;
      resultDesc.textContent = alternative.description;
      dietTag.textContent = alternative.dietTag;
      resultCard.classList.remove("hidden");
    } catch (error) {
      resultDesc.textContent = error.message;
      resultCard.classList.remove("hidden");
    } finally {
      findBtn.textContent = "Find Alternative";
      findBtn.classList.remove("btn-submitting");
    }
  });

});