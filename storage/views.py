from django.shortcuts import render, get_object_or_404
from .utils import list_flight_ids, list_versions

def flights_page(request):
    flights = list_flight_ids()
    return render(request, "flights.html", {"flights": flights})

def flight_versions_page(request, flight_id: str):
    key, versions = list_versions(flight_id)
    context = {
        "flight_id": flight_id,
        "key": key,
        "versions": versions,  # last_modified is a datetime; template can format it
    }
    return render(request, "versions.html", context)

def home(request):
    return render(request, "base.html")
