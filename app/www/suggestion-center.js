/* =========================================================
   NOURISH SUGGESTION CENTER LOGIC
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {
    
  // --- AI Suggestion Cards Logic ---
  const approveButtons = document.querySelectorAll(".btn-approve");
  const dismissButtons = document.querySelectorAll(".btn-dismiss");

  // Handle Approve
  approveButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const card = button.closest(".suggestion-card");
      if (card) {
        // Toggling this class handles the badge reveal and button disabling via CSS
        card.classList.add("is-approved");
      }
    });
  });

  // Handle Dismiss
  dismissButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const card = button.closest(".suggestion-card");
      if (card) {
        // Toggling this class completely hides the card via CSS display: none
        card.classList.add("is-dismissed");
      }
    });
  });


  // --- Custom Suggestion Logic ---
  const sendBtn = document.getElementById("send-suggestion-btn");
  const textarea = document.getElementById("custom-suggestion-text");
  const sentSection = document.getElementById("sent-section");
  const sentList = document.getElementById("sent-list");

  sendBtn.addEventListener("click", function () {
    const textValue = textarea.value.trim();

    if (textValue !== "") {
      // 1. Reveal the sent section if it's hidden
      sentSection.classList.remove("hidden");

      // 2. Create the new card element
      const card = document.createElement("article");
      card.classList.add("sent-card");

      const textNode = document.createElement("p");
      textNode.textContent = textValue;

      // 3. Assemble and prepend (so newest is on top)
      card.appendChild(textNode);
      sentList.prepend(card);

      // 4. Clear the textarea
      textarea.value = "";
    }
  });

});