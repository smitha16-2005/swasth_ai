import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def find_nearby_facilities(
    latitude: float,
    longitude: float,
    risk_level: str,
    radius_meters: int = 5000
) -> list:

    if risk_level == "RED":
        radius_meters = 15000
    elif risk_level == "YELLOW":
        radius_meters = 10000
    else:
        radius_meters = 5000

    # Broader query — catches more facility types
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius_meters},{latitude},{longitude});
      node["amenity"="clinic"](around:{radius_meters},{latitude},{longitude});
      node["amenity"="doctors"](around:{radius_meters},{latitude},{longitude});
      node["healthcare"="hospital"](around:{radius_meters},{latitude},{longitude});
      way["amenity"="hospital"](around:{radius_meters},{latitude},{longitude});
      way["amenity"="clinic"](around:{radius_meters},{latitude},{longitude});
      way["healthcare"="hospital"](around:{radius_meters},{latitude},{longitude});
    );
    out body center;
    """

    try:
        response = requests.post(OVERPASS_URL, data=query, timeout=30)
        data = response.json()
        elements = data.get("elements", [])
    except Exception as e:
        print(f"Overpass error: {e}")
        return get_fallback_facilities(risk_level)

    if not elements:
        return get_fallback_facilities(risk_level)

    facilities = []
    for element in elements[:3]:
        tags = element.get("tags", {})

        if element["type"] == "node":
            lat = element.get("lat")
            lng = element.get("lon")
        else:
            lat = element.get("center", {}).get("lat")
            lng = element.get("center", {}).get("lon")

        if not lat or not lng:
            continue

        name = (
            tags.get("name") or
            tags.get("name:en") or
            tags.get("operator") or
            "Medical Facility"
        )

        facility = {
            "name": name,
            "address": (
                tags.get("addr:full") or
                tags.get("addr:street") or
                tags.get("addr:city") or
                "See map for directions"
            ),
            "phone": (
                tags.get("phone") or
                tags.get("contact:phone") or
                "104"
            ),
            "type": tags.get("amenity") or tags.get("healthcare", "clinic"),
            "location": {"lat": lat, "lng": lng},
            "google_maps_url": f"https://maps.google.com/?q={lat},{lng}"
        }
        facilities.append(facility)

    return facilities if facilities else get_fallback_facilities(risk_level)


def get_fallback_facilities(risk_level: str) -> list:
    """
    Returns national helpline info when no facilities found.
    Always gives the user something actionable.
    """
    return [
        {
            "name": "National Health Helpline",
            "address": "Call from anywhere in India",
            "phone": "104",
            "type": "helpline",
            "location": {"lat": 0, "lng": 0},
            "google_maps_url": ""
        },
        {
            "name": "Emergency Ambulance",
            "address": "Call from anywhere in India",
            "phone": "108",
            "type": "ambulance",
            "location": {"lat": 0, "lng": 0},
            "google_maps_url": ""
        }
    ]


def format_facility_message(facilities: list, risk_level: str) -> str:
    if risk_level == "RED":
        message = "🔴 EMERGENCY — Go to nearest hospital NOW:\n\n"
    elif risk_level == "YELLOW":
        message = "🟡 Visit a clinic within 24 hours:\n\n"
    else:
        message = "🟢 Nearest medical facilities:\n\n"

    for i, f in enumerate(facilities, 1):
        message += f"{i}. {f['name']}\n"
        message += f"   📍 {f['address']}\n"
        message += f"   📞 {f['phone']}\n"
        if f['google_maps_url']:
            message += f"   🗺️  {f['google_maps_url']}\n"
        message += "\n"

    message += "📞 National Health Helpline: 104\n"
    message += "🚑 Emergency Ambulance: 108"
    return message
