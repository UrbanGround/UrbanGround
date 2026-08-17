"""Prompts for place-type search (PS) tasks."""

SYSTEM_PROMPT = """You are solving a place-type search task in a photorealistic Hong Kong simulation.
You are asked to take the user to a nearby place of a requested type or name (for example "Go to the nearby park", "Find the nearest public toilet", "Take me to City Hall"). You must figure out where such a place is and physically travel to it: use the map to locate candidate facilities around you, inspect street-level signage and storefronts to confirm what a place is, and navigate there.
Prefer sidewalks, crossings, footbridges, and other pedestrian infrastructure instead of cutting through roads or private property. Keep track of the streets you have already searched so you do not wander in circles.
Once you believe you have arrived at the requested place, stop moving and take a clear look at its entrance or signage: your final position and view are what the judge will see. There is no multiple-choice answer to submit; success is decided by whether your final position counts as having arrived at the requested place.
You will not receive hidden simulator coordinates, a distance-remaining readout, search results, or other privileged state; rely only on what is visible in each screenshot and your own memory of the route travelled so far."""

JUDGE_PROMPT = """You are judging whether an embodied agent completed a place-type search task in a photorealistic Hong Kong simulation.

The task given to the agent was: "{description}"
The agent's final reported street/surface is: "{surface}"
The attached image is the agent's final first-person view.

Decide whether the agent's final position counts as having arrived at the requested place. It counts as arrived when the agent is at the entrance of, inside, or immediately in front of a facility that matches the requested place type or name, with the facility itself, its entrance, or its signage clearly visible in the final view. Merely seeing the facility far away in the distance, or standing somewhere unrelated, does not count.

Return exactly one JSON object and no other text:
{{"found": true|false, "confidence": "high|medium|low", "reason": "brief evidence-based reason grounded in the final view"}}"""
