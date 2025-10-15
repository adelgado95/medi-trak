from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from apps.api.views import PatientViewSet, RecordViewSet

router = routers.DefaultRouter()
router.register(r'patients', PatientViewSet)
router.register(r'records', RecordViewSet, basename='record')

urlpatterns = [
    path('', include(router.urls)),
]