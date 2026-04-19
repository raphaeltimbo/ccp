from django.urls import path
from . import views

app_name = "evaluation"

urlpatterns = [
    path("", views.performance, name="performance"),
    path("straight-through/", views.straight_through, name="straight_through"),
]
