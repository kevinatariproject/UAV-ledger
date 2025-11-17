from django.contrib import admin
from django.urls import path

from .views import chain_info_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/chain-info/", chain_info_view, name="chain-info"),
]
