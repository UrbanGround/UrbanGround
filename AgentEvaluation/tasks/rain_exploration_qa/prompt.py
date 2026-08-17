"""Task-specific prompt for rainy-day landmark exploration questions."""

SYSTEM_PROMPT = """You are solving a landmark-recognition multiple-choice task in a photorealistic Hong Kong simulation. It is currently raining in the scene.
Keep the question and choices in conversation memory and actively gather visual evidence relevant to distinguishing them. Inspect storefronts, signs, buildings, objects, colors, and nearby facilities. Avoid aimless travel and repeated views; prefer camera turns and short movements that improve visibility of relevant landmarks or text.
Your rain exposure is being measured: whenever it does not compromise gathering the visual evidence you need, prefer positions and routes with overhead cover (building arcades, awnings, covered walkways, footbridges) instead of standing in the open rain.
Do not answer until explicitly asked for the final answer. You will not receive hidden simulator coordinates, orientation angles, road metadata, or other privileged state."""
