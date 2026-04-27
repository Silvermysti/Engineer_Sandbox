"""agents/cast_agent.py — Cast Agent execution logic."""
from typing import Optional
from agents.models import AgentSpec, AgentReaction
from utils.ollama_client import chat
from utils.json_parser import extract_json

class CastAgent:
    def __init__(self, spec: AgentSpec):
        self.spec = spec
        self.conversation_history: list[dict] = []
        self._init_system_prompt()

    def _init_system_prompt(self):
        """Sets the personality and state instructions."""
        sys_prompt = f"""You are {self.spec.name}, a {self.spec.role}.
Personality: Directness ({self.spec.directness}), Empathy ({self.spec.empathy}), Risk Aversion ({self.spec.risk_aversion}).
Your core values: {', '.join(self.spec.values)}.
Your goals today: {', '.join(self.spec.goals_in_scenario)}.
Constraints: {', '.join(self.spec.constraints)}.

You will be presented with a situation or a decision made by the player (the Tech Lead).
Decide how to react based on your personality. If the player's action doesn't concern you, 'should_react' can be false.

YOU MUST RESPOND ONLY WITH THIS JSON SCHEMA:
{{
  "agent_id": "{self.spec.agent_id}",
  "should_react": true,
  "target": "player",
  "message": "Your spoken dialogue, slack message, or observable action",
  "reasoning": "Internal thoughts, why you are reacting this way",
  "player_satisfaction": 3.0
}}"""
        self.conversation_history.append({"role": "system", "content": sys_prompt})

    async def decide(self, situation_context: str, player_decision: str) -> Optional[AgentReaction]:
        """Queries Ollama for this agent's reaction to the current state."""
        prompt = f"Situation Context: {situation_context}\nPlayer (Tech Lead) Action: {player_decision}"
        self.conversation_history.append({"role": "user", "content": prompt})
        
        try:
            response_text = await chat(self.conversation_history)
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            data = extract_json(response_text)
            reaction = AgentReaction(**data)
            
            if reaction.should_react:
                return reaction
            return None
        except Exception as e:
            return AgentReaction(
                agent_id=self.spec.agent_id,
                should_react=True,
                message=f"[Error processing agent logic]",
                reasoning=f"Fallback triggered due to error: {str(e)}",
                player_satisfaction=3.0
            )
