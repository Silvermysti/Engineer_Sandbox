"""agents/agent_factory.py — Instantiates the cast."""
from agents.models import ScenarioSpec
from agents.cast_agent import CastAgent

def create_cast(spec: ScenarioSpec) -> list[CastAgent]:
    """Takes the generator's scenario spec and returns active agent instances."""
    return [CastAgent(agent_spec) for agent_spec in spec.cast]
