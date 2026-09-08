from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CycleEntryViewSet, CycleSummaryView

router = DefaultRouter()
router.register(r'entries', CycleEntryViewSet, basename='cycle-entry')

urlpatterns = [
    path('summary/', CycleSummaryView.as_view(), name='cycle-summary'),
    path('', include(router.urls)),
]
