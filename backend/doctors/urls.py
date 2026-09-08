from django.urls import path
from .views import (
    DoctorPatientsListView,
    DoctorPatientDashboardView,
)

urlpatterns = [
    # Consented patients list
    path('patients/', DoctorPatientsListView.as_view(), name='doctor-consented-patients'),

    # Consolidated patient dashboard
    path('patients/<int:patient_id>/dashboard/', DoctorPatientDashboardView.as_view(), name='doctor-patient-dashboard'),
]
