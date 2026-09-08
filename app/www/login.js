 /* =========================
    ELEMENTS
    ========================= */

const loginTab = document.getElementById("login-tab");
const signupTab = document.getElementById("signup-tab");

const loginForm = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");

const authTitle = document.getElementById("auth-title");
const authSubtitle = document.getElementById("auth-subtitle");

const roleOptions = document.querySelectorAll(".role-option");


/* =========================
   SELECTED ROLE
   ========================= */

// No role selected initially
let selectedRole = null;


/* =========================
   SHOW LOGIN
   ========================= */

loginTab.addEventListener("click", function () {

  loginTab.classList.add("active");
  signupTab.classList.remove("active");

  loginForm.classList.remove("hidden");
  signupForm.classList.add("hidden");

  authTitle.textContent = "Welcome Back";

  authSubtitle.textContent =
    "Log in to continue your health journey.";

  clearErrors();
});


/* =========================
   SHOW SIGN UP
   ========================= */

signupTab.addEventListener("click", function () {

  signupTab.classList.add("active");
  loginTab.classList.remove("active");

  signupForm.classList.remove("hidden");
  loginForm.classList.add("hidden");

  authTitle.textContent = "Create Your Account";

  authSubtitle.textContent =
    "Start your personalized health journey.";

  clearErrors();
});


/* =========================
   ROLE SELECTION
   ========================= */

roleOptions.forEach(function (option) {

  option.addEventListener("click", function () {

    // Store selected role
    selectedRole = option.dataset.role;

    // Store it as a data attribute for future backend use
    signupForm.dataset.selectedRole = selectedRole;


    // Remove selected state from both
    roleOptions.forEach(function (item) {
      item.classList.remove("selected");
    });


    // Highlight selected role
    option.classList.add("selected");


    // Remove role error
    document.getElementById(
      "signup-role-error"
    ).textContent = "";

  });

});


/* =========================
   EMAIL VALIDATION
   ========================= */

function isValidEmail(email) {

  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

}


/* =========================
   ERROR HANDLING
   ========================= */

function setError(id, message) {

  document.getElementById(id).textContent = message;

}


function clearErrors() {

  document
    .querySelectorAll(".error-message")
    .forEach(function (element) {

      element.textContent = "";

    });


  document
    .querySelectorAll(".form-success")
    .forEach(function (element) {

      element.textContent = "";

    });

}


/* =========================
   LOGIN VALIDATION
   ========================= */

loginForm.addEventListener("submit", function (event) {

  event.preventDefault();

  clearErrors();

  const email =
    document.getElementById("login-email").value.trim();

  const password =
    document.getElementById("login-password").value;

  let valid = true;


  // Email required
  if (!email) {

    setError(
      "login-email-error",
      "Email is required."
    );

    valid = false;

  }


  // Email format
  else if (!isValidEmail(email)) {

    setError(
      "login-email-error",
      "Please enter a valid email address."
    );

    valid = false;

  }


  // Password required
  if (!password) {

    setError(
      "login-password-error",
      "Password is required."
    );

    valid = false;

  }


  // Success
  if (valid) {

    const button = loginForm.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = "Signing in...";
    CycleCareAPI.login({ email, password })
      .then((data) => {
        CycleCareAPI.setSession(data);
        document.getElementById("login-success").textContent = "Signed in successfully.";
        window.location.href = data.user.role === "doctor" ? "doctor-dashboard.html" : "dashboard.html";
      })
      .catch((error) => setError("login-password-error", error.message))
      .finally(() => {
        button.disabled = false;
        button.textContent = "Login";
      });

  }

});


/* =========================
   SIGN UP VALIDATION
   ========================= */

signupForm.addEventListener("submit", function (event) {

  event.preventDefault();

  clearErrors();

  const name =
    document.getElementById("signup-name").value.trim();

  const email =
    document.getElementById("signup-email").value.trim();

  const password =
    document.getElementById("signup-password").value;

  const confirmPassword =
    document.getElementById(
      "signup-confirm-password"
    ).value;

  let valid = true;


  /* Role required */

  if (!selectedRole) {

    setError(
      "signup-role-error",
      "Please select whether you're signing up as a Patient or Doctor."
    );

    valid = false;

  }


  /* Name required */

  if (!name) {

    setError(
      "signup-name-error",
      "Name is required."
    );

    valid = false;

  }


  /* Email required */

  if (!email) {

    setError(
      "signup-email-error",
      "Email is required."
    );

    valid = false;

  }


  /* Email format */

  else if (!isValidEmail(email)) {

    setError(
      "signup-email-error",
      "Please enter a valid email address."
    );

    valid = false;

  }


  /* Password required */

  if (!password) {

    setError(
      "signup-password-error",
      "Password is required."
    );

    valid = false;

  }


  /* Confirm password */

  if (!confirmPassword) {

    setError(
      "signup-confirm-password-error",
      "Please confirm your password."
    );

    valid = false;

  }


  /* Password match */

  else if (password !== confirmPassword) {

    setError(
      "signup-confirm-password-error",
      "Passwords do not match."
    );

    valid = false;

  }


  /* Everything valid */

  if (valid) {

    const button = signupForm.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = "Creating account...";
    CycleCareAPI.register({
      email,
      password,
      full_name: name,
      role: selectedRole.toLowerCase()
    })
      .then((data) => {
        CycleCareAPI.setSession(data);
        localStorage.setItem("cyclecare_onboarding_role", selectedRole.toLowerCase());
        window.location.href = "onboarding.html";
      })
      .catch((error) => setError("signup-email-error", error.message))
      .finally(() => {
        button.disabled = false;
        button.textContent = "Create Account";
      });

  }

});