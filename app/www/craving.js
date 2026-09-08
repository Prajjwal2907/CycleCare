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

  /**
   * Evaluates the craving text and returns a healthier alternative object.
   * 
   * // TODO: replace with real API/model call, keep same return shape
   * 
   * @param {string} cravingText 
   * @returns {Promise<{name: string, description: string, dietTag: string}>}
   */
  async function getAlternative(cravingText) {
    const input = cravingText.toLowerCase().trim();

    // Simulate network delay to mimic an API response
    await new Promise(resolve => setTimeout(resolve, 800));

    if (input.includes("pizza")) {
      return {
        name: "Cauliflower Crust Veggie Pizza",
        description: "A lighter take on pizza loaded with bell peppers, onions, and a sprinkle of part-skim mozzarella.",
        dietTag: "Vegetarian Friendly"
      };
    } 
    
    if (input.includes("chocolate")) {
      return {
        name: "Dark Chocolate Energy Bites",
        description: "Rolled oats, almond butter, and 70% dark chocolate chips rolled into satisfying bite-sized treats.",
        dietTag: "Vegan"
      };
    } 
    
    if (input.includes("fries")) {
      return {
        name: "Baked Sweet Potato Fries",
        description: "Wedges of sweet potato lightly tossed in olive oil and paprika, baked until crispy.",
        dietTag: "Vegan & Gluten-Free"
      };
    } 
    
    if (input.includes("burger")) {
      return {
        name: "Grilled Paneer/Chicken Burger",
        description: "A lean grilled patty with fresh lettuce, tomato, and a yogurt-based sauce on a whole grain bun.",
        dietTag: "High Protein"
      };
    } 
    
    // Fallback response for unmapped items
    return {
      name: "Nutrient-Dense Power Bowl",
      description: "A customized bowl of quinoa, fresh greens, roasted vegetables, and a light tahini dressing.",
      dietTag: "Balanced Meal"
    };
  }

  // --- UI Update Handling ---
  findBtn.addEventListener("click", async function () {
    const cravingValue = cravingInput.value;

    if (!cravingValue) {
      return; // Do nothing if input is empty
    }

    // Set Loading State (Using the existing .btn-submitting class from style2.css)
    findBtn.textContent = "Finding...";
    findBtn.classList.add("btn-submitting");
    resultCard.classList.add("hidden");

    // Fetch Alternative via isolated logic
    const alternative = await getAlternative(cravingValue);

    // Populate the DOM
    resultTitle.textContent = alternative.name;
    resultDesc.textContent = alternative.description;
    dietTag.textContent = alternative.dietTag;

    // Reset Button State and Reveal Card
    findBtn.textContent = "Find Alternative";
    findBtn.classList.remove("btn-submitting");
    resultCard.classList.remove("hidden");
  });

});