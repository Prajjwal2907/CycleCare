/* =========================================================
   NOURISH ONBOARDING PAGE
   ========================================================= */


/* ---------------------------------------------------------
   ROLE
   --------------------------------------------------------- */

// This value will eventually come from login/signup.
//
// For now:
// "Patient" = patient onboarding
// "Doctor"  = doctor onboarding

const userRole = "Patient";


/* ---------------------------------------------------------
   ELEMENTS
   --------------------------------------------------------- */

const onboardingForm =
  document.getElementById("onboarding-form");

const patientFields =
  document.getElementById("onboarding-patient-fields");

const doctorFields =
  document.getElementById("onboarding-doctor-fields");

const dietOptions =
  document.querySelectorAll(
    ".onboarding-diet-option"
  );

const unitButtons =
  document.querySelectorAll(
    ".onboarding-unit-button"
  );


/* ---------------------------------------------------------
   SELECTED DIET
   --------------------------------------------------------- */

let selectedDiet = null;


/* ---------------------------------------------------------
   ERROR HANDLING
   --------------------------------------------------------- */

function setOnboardingError(id, message) {
  const element = document.getElementById(id);

  if (element) {
    element.textContent = message;
  }
}


function clearOnboardingErrors() {

  document
    .querySelectorAll(
      "#onboarding-form .error-message"
    )
    .forEach(function (element) {

      element.textContent = "";

    });

}


/* ---------------------------------------------------------
   EMPTY FIELD CHECK
   --------------------------------------------------------- */

function isOnboardingEmpty(id) {

  const element =
    document.getElementById(id);

  return !element.value.trim();

}


/* ---------------------------------------------------------
   SHOW CORRECT ROLE FIELDS
   --------------------------------------------------------- */

function showOnboardingRoleFields() {

  if (userRole === "Doctor") {

    doctorFields.classList.remove("hidden");

    patientFields.classList.add("hidden");

  } else {

    patientFields.classList.remove("hidden");

    doctorFields.classList.add("hidden");

  }

}


/* ---------------------------------------------------------
   UNIT SELECTION
   --------------------------------------------------------- */

unitButtons.forEach(function (button) {

  button.addEventListener("click", function () {

    const group =
      button.dataset.onboardingUnitGroup;


    /*
      Only change the buttons belonging
      to the same unit group.
    */

    document
      .querySelectorAll(
        '[data-onboarding-unit-group="' +
        group +
        '"]'
      )
      .forEach(function (item) {

        item.classList.remove(
          "onboarding-unit-selected"
        );

      });


    button.classList.add(
      "onboarding-unit-selected"
    );

  });

});


/* ---------------------------------------------------------
   DIETARY PREFERENCE
   --------------------------------------------------------- */

dietOptions.forEach(function (option) {

  option.addEventListener("click", function () {

    selectedDiet =
      option.dataset.onboardingDiet;


    /* Remove selection from every option */

    dietOptions.forEach(function (item) {

      item.classList.remove(
        "onboarding-diet-selected"
      );

    });


    /* Select clicked option */

    option.classList.add(
      "onboarding-diet-selected"
    );


    /* Remove dietary error */

    setOnboardingError(
      "onboarding-diet-error",
      ""
    );

  });

});


/* ---------------------------------------------------------
   FORM SUBMIT
   --------------------------------------------------------- */

onboardingForm.addEventListener(
  "submit",
  function (event) {

    event.preventDefault();

    clearOnboardingErrors();

    let valid = true;


    /* -----------------------------------------------------
       FULL NAME
       ----------------------------------------------------- */

    if (
      isOnboardingEmpty(
        "onboarding-full-name"
      )
    ) {

      setOnboardingError(
        "onboarding-full-name-error",
        "Full name is required."
      );

      valid = false;

    }


    /* -----------------------------------------------------
       AGE
       ----------------------------------------------------- */

    if (
      isOnboardingEmpty(
        "onboarding-age"
      )
    ) {

      setOnboardingError(
        "onboarding-age-error",
        "Age is required."
      );

      valid = false;

    }


    /* -----------------------------------------------------
       DOCTOR
       ----------------------------------------------------- */

    if (userRole === "Doctor") {

      /* Specialization */

      if (
        isOnboardingEmpty(
          "onboarding-specialization"
        )
      ) {

        setOnboardingError(
          "onboarding-specialization-error",
          "Specialization is required."
        );

        valid = false;

      }


      /* Experience */

      if (
        isOnboardingEmpty(
          "onboarding-experience"
        )
      ) {

        setOnboardingError(
          "onboarding-experience-error",
          "Years of experience is required."
        );

        valid = false;

      }

    }


    /* -----------------------------------------------------
       PATIENT
       ----------------------------------------------------- */

    else {

      /* Weight */

      if (
        isOnboardingEmpty(
          "onboarding-weight"
        )
      ) {

        setOnboardingError(
          "onboarding-weight-error",
          "Weight is required."
        );

        valid = false;

      }


      /* Height */

      if (
        isOnboardingEmpty(
          "onboarding-height"
        )
      ) {

        setOnboardingError(
          "onboarding-height-error",
          "Height is required."
        );

        valid = false;

      }


      /* Dietary preference */

      if (!selectedDiet) {

        setOnboardingError(
          "onboarding-diet-error",
          "Please select a dietary preference."
        );

        valid = false;

      }

    }


    /* -----------------------------------------------------
   SUCCESS
   ----------------------------------------------------- */

    if (valid) {

      if (userRole === "Doctor") {

        window.location.href =
          "doctor-dashboard.html";

      } else {

        window.location.href =
          "dashboard.html";

      }
    }
  }
);


/* ---------------------------------------------------------
   INITIALIZE
   --------------------------------------------------------- */

showOnboardingRoleFields();