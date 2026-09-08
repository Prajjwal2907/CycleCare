from rest_framework import permissions


class IsPatient(permissions.BasePermission):
    """
    Allows access only to authenticated users with the 'patient' role.
    """
    message = "Only patients are authorized to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'patient'
        )


class IsDoctor(permissions.BasePermission):
    """
    Allows access only to authenticated users with the 'doctor' role.
    """
    message = "Only verified doctors are authorized to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'doctor'
        )


class HasActiveConsent(permissions.BasePermission):
    """
    Enforces that a doctor has an explicit, active ConsentGrant from the patient
    before accessing any of the patient's tracked health data.
    Patients are always permitted to access their own records.
    """
    message = "Access denied. Active patient consent is required to view this health data."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.role == 'patient':
            return True

        if request.user.role == 'doctor':
            doctor_profile = getattr(request.user, 'doctor_profile', None)
            if not doctor_profile:
                return False

            # Check patient identifier from URL kwargs if present
            patient_id = (
                view.kwargs.get('patient_id') or
                view.kwargs.get('patient_pk') or
                view.kwargs.get('id') or
                view.kwargs.get('pk')
            )

            if patient_id is not None:
                from accounts.models import ConsentGrant, PatientProfile
                try:
                    # Check whether consent grant is active
                    has_consent = ConsentGrant.objects.filter(
                        patient_id=patient_id,
                        doctor=doctor_profile,
                        is_active=True
                    ).exists()
                    return has_consent
                except Exception:
                    return False

            # If no specific patient_id in URL, defer to has_object_permission or allow list
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        # Extract the target patient profile from object
        patient = None
        if hasattr(obj, 'patient'):
            patient = obj.patient
        elif hasattr(obj, 'patient_profile'):
            patient = obj.patient_profile
        elif obj.__class__.__name__ == 'PatientProfile':
            patient = obj

        if not patient:
            return False

        # Patient accessing their own data
        if request.user.role == 'patient':
            return patient.user_id == request.user.id

        # Doctor accessing patient data
        if request.user.role == 'doctor':
            doctor_profile = getattr(request.user, 'doctor_profile', None)
            if not doctor_profile:
                return False

            from accounts.models import ConsentGrant
            return ConsentGrant.objects.filter(
                patient=patient,
                doctor=doctor_profile,
                is_active=True
            ).exists()

        return False
