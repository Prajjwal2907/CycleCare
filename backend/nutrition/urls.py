from django.urls import path
from .views import CravingAlternativeView, CravingHistoryView

urlpatterns = [
    # Craving -> Healthier alternative
    path('craving/', CravingAlternativeView.as_view(), name='craving-alternative'),
    path('craving/history/', CravingHistoryView.as_view(), name='craving-history'),
]
