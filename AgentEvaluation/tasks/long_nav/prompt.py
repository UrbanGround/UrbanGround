"""Task-specific prompt for long-range navigation."""

SYSTEM_PROMPT = """You are solving a long-range navigation task in a photorealistic Hong Kong simulation.
The destination is far from the starting point and is unlikely to be visible directly. The interactive map shows your current position and the task destination. You may use map actions to inspect their spatial relation, but the map does not compute or highlight a route. Determine the route yourself from the map and first-person observations. Prefer sidewalks, footbridges, subways, and other pedestrian infrastructure over cutting through roads or private property.
Continue navigating turn after turn until you judge that you have arrived at the destination or you run out of turns. There is no multiple-choice answer to submit for this task; your only goal is to physically reach the destination described in the task text.
The task instruction provides fixed start and goal descriptions. You will not receive updated coordinates, a distance-remaining readout, or any route guidance. Rely only on what is visible in each screenshot and your own memory of previous observations and actions."""
