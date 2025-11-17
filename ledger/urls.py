# ledger/urls.py
from django.urls import path
from .views import health, EmitView, VerifyView

urlpatterns = [
    path("health/", health, name="health"),
    path("emit/", EmitView.as_view(), name="emit"),
    path("verify/", VerifyView.as_view(), name="verify"),
]
