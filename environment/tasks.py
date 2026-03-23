"""
Task definitions: each task has an instruction template and default parameters.
"""

TASKS = {
    "flight_search": {
        "instruction": (
            "Search for a one-way flight from {origin} to {destination} "
            "on {date} for {passengers} adult(s) on the travel site."
        ),
        "default_params": {
            "origin": "Boston",
            "destination": "Chicago",
            "date": "2026-04-15",
            "passengers": "2",
        },
    },
    "product_search": {
        "instruction": (
            "Search for '{product}' on the shopping site, sort by "
            "{sort_order}, and add the first result to cart."
        ),
        "default_params": {
            "product": "wireless headphones",
            "sort_order": "price low to high",
        },
    },
    "restaurant_reservation": {
        "instruction": (
            "Reserve a table for {party_size} at a restaurant in "
            "{city} on {date} at {time}."
        ),
        "default_params": {
            "party_size": "4",
            "city": "New York",
            "date": "2026-05-01",
            "time": "7:00 PM",
        },
    },
}