"""
Mock stadium + operational data.

In production this would come from turnstile scanners, CCTV/computer-vision
crowd counters, transit APIs, and the tournament CMS. For the hackathon we
simulate live values so the GenAI layer has real, changing signal to reason
over instead of static copy.
"""

import random

STADIUM_NAME = "MetLife Stadium — FIFA World Cup 2026"

GATES = [
    {"id": "A", "name": "Gate A — North Plaza", "capacity": 9000, "notes": "Nearest to NJ Transit rail platform"},
    {"id": "B", "name": "Gate B — East Concourse", "capacity": 7500, "notes": "Accessible entrance, ramp + lift access"},
    {"id": "C", "name": "Gate C — South Plaza", "capacity": 9000, "notes": "Nearest to main parking lots"},
    {"id": "D", "name": "Gate D — West Concourse", "capacity": 6000, "notes": "Nearest to shuttle bus drop-off"},
    {"id": "E", "name": "Gate E — Media/VIP", "capacity": 3000, "notes": "Lower footfall, general fans may use as overflow"},
]

TRANSIT_OPTIONS = [
    "NJ Transit Meadowlands Rail — direct service from Secaucus Junction, ~9 min ride, runs every 7 min on match days",
    "Coach USA shuttle buses from Port Authority Bus Terminal, Manhattan — $5 round trip, 30 min ride",
    "Designated rideshare (Uber/Lyft) pickup/drop-off zone at Lot F (10 min walk to Gate C)",
    "Bike valet parking at Gate D — free, first-come first-served, 200 bike capacity",
    "EV charging stations available in Lots E and G (Level 2 + DC Fast Charge, free on match days)",
    "NJ Transit bus routes 160, 161, 163, 164, 165, 168 from NYC Port Authority to MetLife",
    "NY Waterway ferry + shuttle combo from Manhattan Midtown West — 45 min total",
]

ACCESSIBILITY_SERVICES = [
    "Wheelchair loan and accessible seating — Guest Services at Gate B (free, ID required)",
    "Sensory room (low light, low noise) for neurodivergent fans — near Section 105, capacity 15",
    "ASL interpreters available on request at Guest Services, 2 hours notice preferred",
    "Companion/service animal relief areas near Gates B and D",
    "Accessible shuttle from designated ADA parking (Lot A) to Gate B, runs every 5 min",
    "Audio-descriptive commentary headsets available at Guest Services Gate B (free, ID required)",
    "Braille wayfinding signage at all gates and major concourse intersections",
    "Elevators at Gates B and D for upper-level accessible seating",
]

SUSTAINABILITY_INITIATIVES = [
    "Reusable cup program — return bins at every concession stand, $2 refund per cup returned",
    "Single-stream recycling and compost bins throughout the concourse, clearly color-coded",
    "Public transit + bike valet discounts: 10% off matchday food/drink with transit proof",
    "Solar-assisted lighting in parking Lots E and G — 100% renewable for lot lighting",
    "Digital-only tickets and programs to cut paper waste — QR codes at all entry gates",
    "Water refill stations at every gate — bring your own bottle, skip the line",
    "Carbon offset kiosk at Gate A — donate to plant a tree for your match-day travel",
]

FOOD_AND_BEVERAGE = [
    "Main concessions: hot dogs, burgers, pizza, nachos, pretzels — all gates",
    "Halal food cart — Section 117 and Section 233",
    "Kosher stand — Section 111",
    "Vegetarian/Vegan options — 'Green Plate' stand near Gate D, full vegan menu",
    "Gluten-free options available at all main concession stands (ask staff)",
    "International food court — Section 201: Brazilian, Argentine, Mexican, Japanese, Indian",
    "Premium dining — MetLife Club Level (ticket required), full-service restaurant",
    "Water and soft drinks at all stands; beer/wine at designated stands (21+ ID required)",
    "Allergen info cards available at every food stand — ask any vendor",
]

PROHIBITED_ITEMS = [
    "Bags larger than 12\" x 6\" x 12\" (clear bag policy — clear plastic or one-gallon zip-lock preferred)",
    "Outside food and beverages (one sealed water bottle under 20 oz permitted)",
    "Umbrellas, selfie sticks, tripods, professional cameras (lens > 6 inches)",
    "Fireworks, smoke bombs, flares, laser pointers",
    "Weapons of any kind including pocket knives",
    "Drones and remote-controlled devices",
    "Noisemakers: air horns, vuvuzelas, whistles",
    "Banners/flags larger than 2m × 1.5m or attached to poles",
]

EMERGENCY_INFO = [
    "Emergency exits marked in red at every concourse section",
    "AED (defibrillator) locations: Gates A, C, E, and Sections 112, 224, 336",
    "First Aid stations: Gate B (main), Section 201 (upper level)",
    "Security Chief contact: radio channel 7 or any steward can relay",
    "Severe weather shelter: lower concourse — follow staff directions",
    "Lost child meeting point: Guest Services at Gate B",
]


def get_live_crowd_snapshot():
    """Simulate a live occupancy read for each gate (percent of capacity)."""
    snapshot = []
    for gate in GATES:
        # Bias a couple of gates toward congestion so the demo has a clear story.
        bias = 0.55 if gate["id"] in ("A", "C") else 0.25
        occupancy_pct = min(100, round(random.uniform(bias * 100, (bias + 0.4) * 100)))
        if occupancy_pct >= 85:
            status = "critical"
        elif occupancy_pct >= 60:
            status = "busy"
        else:
            status = "clear"
        snapshot.append({
            "id": gate["id"],
            "name": gate["name"],
            "occupancy_pct": occupancy_pct,
            "status": status,
            "notes": gate["notes"],
        })
    return snapshot


def stadium_context_block() -> str:
    """A compact, structured context block injected into chat prompts.

    This stands in for a retrieval step (e.g. a vector DB over the fan
    handbook) — for a 3-hour build we inject curated context directly,
    which keeps latency low and is a defensible scope cut to call out
    to judges.
    """
    lines = [f"Stadium: {STADIUM_NAME}", "Total Capacity: 82,500", ""]

    lines.append("Gates:")
    for g in GATES:
        lines.append(f"- {g['id']}: {g['name']} (capacity {g['capacity']}) — {g['notes']}")

    lines.append("\nTransport options:")
    lines += [f"- {t}" for t in TRANSIT_OPTIONS]

    lines.append("\nAccessibility services:")
    lines += [f"- {a}" for a in ACCESSIBILITY_SERVICES]

    lines.append("\nSustainability initiatives:")
    lines += [f"- {s}" for s in SUSTAINABILITY_INITIATIVES]

    lines.append("\nFood & Beverage:")
    lines += [f"- {f}" for f in FOOD_AND_BEVERAGE]

    lines.append("\nProhibited items:")
    lines += [f"- {p}" for p in PROHIBITED_ITEMS]

    lines.append("\nEmergency information:")
    lines += [f"- {e}" for e in EMERGENCY_INFO]

    return "\n".join(lines)
