from rest_framework.routers import DefaultRouter
from .views import EventViewSet
from django.urls import path, include

router = DefaultRouter()

router.register("", EventViewSet, basename="events")

urlpatterns = [
    path("", include(router.urls)),

]

app_name = "events"
