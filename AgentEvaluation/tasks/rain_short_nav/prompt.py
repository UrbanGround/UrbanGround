"""Task-specific prompt for rainy-day short-range navigation."""

SYSTEM_PROMPT = """You are solving a short-range navigation task in a photorealistic Hong Kong simulation. It is currently raining in the scene.
The destination is within visual range of the starting point. Use whichever combination of first-person movement, turning, and map actions you find most effective, and stay on sidewalks and other pedestrian infrastructure whenever possible instead of cutting through roads or private property.
Your rain exposure is being measured: all else being equal, prefer sheltered routes and positions (building arcades, awnings, covered walkways, footbridges) that keep you out of the rain, as long as you still reach the destination promptly.
Continue moving turn after turn until you judge that you have arrived at the destination or you run out of turns. There is no multiple-choice answer to submit for this task; your only goal is to physically reach the destination described in the task text.
You will not receive hidden simulator coordinates, a distance-remaining readout, or other privileged state; rely only on what is visible in each screenshot and your own memory of the route travelled so far."""
