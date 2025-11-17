# uavledger/urls.py

from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Ethereum status endpoint
    path("eth/status/", views.eth_status, name="eth_status"),

    # Log a mission flight to the blockchain
    path(
        "api/missions/<str:mission_id>/log",
        views.log_mission,
        name="log_mission",
    ),

    # Read a mission flight from the blockchain
    path(
        "api/missions/<str:mission_id>/log/details",
        views.get_mission,
        name="get_mission",
    ),
]
