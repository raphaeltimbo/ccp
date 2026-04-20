from django.urls import path
from . import views

app_name = "evaluation"

urlpatterns = [
    path("", views.performance, name="performance"),
    path("straight-through/", views.straight_through, name="straight_through"),
    path("save/<str:app_type>/", views.save_state, name="save_state"),
    path("load/", views.load_state, name="load_state"),
]
