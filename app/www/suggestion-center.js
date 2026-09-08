document.addEventListener("DOMContentLoaded", async function () {
  const list = document.getElementById("ai-suggestions");
  const patientSelect = document.getElementById("patient-select");
  const sendBtn = document.getElementById("send-suggestion-btn");
  const textarea = document.getElementById("custom-suggestion-text");
  const sentSection = document.getElementById("sent-section");
  const sentList = document.getElementById("sent-list");

  async function loadPatients() {
    const patients = CycleCareAPI.unwrap(await CycleCareAPI.doctorsPatients());
    patientSelect.innerHTML = patients.map((patient) => `<option value="${patient.id}">${patient.full_name || patient.email}</option>`).join("");
    return patients;
  }

  async function loadSuggestions() {
    const suggestions = CycleCareAPI.unwrap(await CycleCareAPI.pendingSuggestions());
    list.innerHTML = suggestions.length ? suggestions.map((suggestion) => `<article class="suggestion-card" data-id="${suggestion.id}">
      <div class="suggestion-header"><p class="suggestion-text">${suggestion.text}</p><span class="badge-approved">Pending Review</span></div>
      <div class="suggestion-actions"><button type="button" class="auth-button btn-forest btn-action btn-approve">Approve</button><button type="button" class="auth-button btn-outline-grey btn-action btn-dismiss">Dismiss</button></div>
    </article>`).join("") : "<p>No pending suggestions.</p>";
    list.querySelectorAll(".suggestion-card").forEach((card) => {
      card.querySelector(".btn-approve").addEventListener("click", () => review(card, "approved"));
      card.querySelector(".btn-dismiss").addEventListener("click", () => review(card, "rejected"));
    });
  }

  async function review(card, status) {
    const button = card.querySelector(status === "approved" ? ".btn-approve" : ".btn-dismiss");
    button.disabled = true;
    try {
      await CycleCareAPI.reviewSuggestion(card.dataset.id, { status });
      card.remove();
    } catch (error) {
      alert(error.message);
      button.disabled = false;
    }
  }

  try {
    await loadPatients();
    await loadSuggestions();
  } catch (error) {
    list.innerHTML = `<p>${error.message}</p>`;
  }

  sendBtn.addEventListener("click", async function () {
    const text = textarea.value.trim();
    const patientId = patientSelect.value;
    if (!text || !patientId) return;
    sendBtn.disabled = true;
    sendBtn.textContent = "Sending...";
    try {
      const result = await CycleCareAPI.createSuggestion({ patient_id: Number(patientId), category: "lifestyle", text });
      sentSection.classList.remove("hidden");
      const card = document.createElement("article");
      card.className = "sent-card";
      card.textContent = result.suggestion.text;
      sentList.prepend(card);
      textarea.value = "";
    } catch (error) {
      alert(error.message);
    } finally {
      sendBtn.disabled = false;
      sendBtn.textContent = "Send to Patient";
    }
  });
});
