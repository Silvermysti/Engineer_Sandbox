"""
config.py — Global configurations and constants for Engineer Sandbox.
"""

OLLAMA_BASE_URL = "http://localhost:11434"
# 'mistral' is recommended for a balance of speed and reasoning on local CPU
MODEL_NAME = "mistral" 

JSON_RETRY_LIMIT = 3
WEAKNESS_THRESHOLD = 70.0
STRENGTH_THRESHOLD = 85.0

SCENARIO_TYPES = [
    "Conflict Resolution",
    "Deadline Pressure",
    "Mentorship/Leadership",
    "Strategic Decisions",
    "Politics/Navigation",
    "Ethical Dilemmas",
    "Team Dynamics"
]
