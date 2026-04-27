"""
agents/scenario_generator.py — Scenario Generator Agent.
"""
import json
import random
from typing import Any
from agents.models import AgentSpec, RelationshipSpec, ScenarioSpec, ScheduledEvent
from config import JSON_RETRY_LIMIT, SCENARIO_TYPES, WEAKNESS_THRESHOLD, STRENGTH_THRESHOLD
from storage.database import (
    get_performance_profile,
    get_player_profile,
    get_recent_scenario_types,
)
from utils.json_parser import extract_json
from utils.ollama_client import generate, OllamaError

SYSTEM_PROMPT = """\
You are the Scenario Generator for a workplace simulation game called Engineer Sandbox.
Your task is to create a single, realistic scenario for a software engineering team.
You MUST respond with ONLY valid JSON — no prose, no markdown fences, no explanation.
The JSON must exactly match the schema described in the user prompt."""

def _build_generator_prompt(perf: dict[str, dict], player_profile: dict, recent_types: list[str], scenario_number: int) -> str:
    weak  = [t for t, d in perf.items() if d["avg_score"] < WEAKNESS_THRESHOLD]
    strong= [t for t, d in perf.items() if d["avg_score"] >= STRENGTH_THRESHOLD]
    no_data_types = [t for t in SCENARIO_TYPES if t not in perf]
    
    avoid = set(recent_types[:2])
    candidates = [t for t in (no_data_types + weak) if t not in avoid]
    if not candidates: candidates = [t for t in SCENARIO_TYPES if t not in avoid]
    if not candidates: candidates = SCENARIO_TYPES[:]
    target_type = random.choice(candidates)

    perf_lines = []
    for t, d in perf.items():
        trend = "↑" if len(d["last_5"]) >= 2 and d["last_5"][0] > d["last_5"][-1] else "↓"
        perf_lines.append(f"  - {t}: avg={d['avg_score']} ({d['count']} runs) {trend}")
    perf_summary = "\n".join(perf_lines) if perf_lines else "  (no history yet — first scenario)"

    rep = player_profile.get("reputation_json") or {}
    patterns = player_profile.get("decision_patterns") or []
    player_role = player_profile.get("player_role", "Tech Lead")
    
    difficulty = "beginner" if scenario_number <= 3 else ("intermediate" if scenario_number <= 8 else "advanced")
    color_pool = ["bold magenta", "bold yellow", "bold green", "bold cyan", "bold red", "bold white"]

    return f"""You are generating scenario #{scenario_number} for a software engineering workplace simulation.
=== PLAYER PROFILE ===
Role: {player_role}
Reputation: {json.dumps(rep)}
Detected patterns: {json.dumps(patterns)}

=== PERFORMANCE HISTORY ===
{perf_summary}

=== GENERATION DIRECTIVE ===
Target scenario type: {target_type}
Difficulty level: {difficulty}
Recently played types (avoid repeating): {recent_types[:2]}
Weak areas to address: {weak}
Strong areas: {strong}

=== REQUIRED JSON SCHEMA ===
Return ONLY this JSON object:
{{
  "title": "Short punchy scenario title",
  "scenario_type": "{target_type}",
  "description": "2-3 paragraph rich scene-setting.",
  "player_role": "{player_role}",
  "stakes": ["stake1", "stake2"],
  "opening_hook": "One dramatic sentence.",
  "time_pressure_baseline": 0.5,
  "cast": [
    {{
      "agent_id": "unique_slug",
      "name": "First Last",
      "role": "Their job title",
      "directness": 0.7, "empathy": 0.5, "risk_aversion": 0.4,
      "political_savvy": 0.6, "conflict_aversion": 0.3,
      "values": ["value1"], "goals_in_scenario": ["goal1"], "constraints": ["constraint1"],
      "color": "bold magenta",
      "relationships": {{
        "player": {{"trust": 0.7, "dynamic": "mutual_respect", "history": "Brief note"}}
      }}
    }}
  ],
  "scheduled_events": [],
  "decision_options": ["Option A", "Option B", "Option C"]
}}
Rules: Use realistic names. agent_id must be lowercase slug. Color options: {color_pool}"""

def _fallback_scenario() -> ScenarioSpec:
    return ScenarioSpec(
        title="The Stalled PR", scenario_type="Conflict Resolution",
        description="Alex, your promising junior dev, submitted a PR three days ago. You haven't reviewed it. Now it's blocking the team.",
        player_role="Tech Lead", stakes=["team morale", "delivery timeline"],
        opening_hook="Three pings. Same PR. Clock ticking.", time_pressure_baseline=0.5,
        cast=[
            AgentSpec(
                agent_id="junior_alex", name="Alex Rivera", role="Junior Developer",
                directness=0.4, empathy=0.8, risk_aversion=0.7, political_savvy=0.3, conflict_aversion=0.7,
                values=["learning", "belonging"], goals_in_scenario=["Get PR merged"], constraints=["Worried about job"],
                color="bold green",
                relationships={"player": RelationshipSpec(trust=0.70, dynamic="hopeful", history="First big PR")}
            )
        ],
        scheduled_events=[],
        decision_options=["Review the PR right now", "Send a quick Slack message: 'On it'", "Ask someone else to review"]
    )

class ScenarioGenerator:
    async def generate(self, scenario_number: int = 1) -> ScenarioSpec:
        perf = get_performance_profile()
        player_profile = get_player_profile()
        recent_types = get_recent_scenario_types(5)
        prompt = _build_generator_prompt(perf, player_profile, recent_types, scenario_number)

        for attempt in range(1, JSON_RETRY_LIMIT + 1):
            try:
                raw = await generate(prompt=prompt, system=SYSTEM_PROMPT, temperature=0.8)
                data = extract_json(raw)
                return self._parse_spec(data)
            except (OllamaError, ValueError, Exception) as e:
                if attempt == JSON_RETRY_LIMIT:
                    print(f"\n[generator] All {JSON_RETRY_LIMIT} attempts failed ({e}). Using fallback scenario.")
                    return _fallback_scenario()
                prompt += "\n\nIMPORTANT: Return ONLY the raw JSON object."
        return _fallback_scenario()

    def _parse_spec(self, data: dict) -> ScenarioSpec:
        cast = [self._parse_agent(a) for a in data.get("cast", [])]
        events = [self._parse_event(e) for e in data.get("scheduled_events", [])]
        return ScenarioSpec(
            title=data.get("title", "Untitled"), scenario_type=data.get("scenario_type", "Conflict Resolution"),
            description=data.get("description", ""), player_role=data.get("player_role", "Tech Lead"),
            stakes=data.get("stakes", []), opening_hook=data.get("opening_hook", ""),
            time_pressure_baseline=float(data.get("time_pressure_baseline", 0.5)),
            cast=cast, scheduled_events=events,
            decision_options=data.get("decision_options", ["Address it", "Ignore it"])
        )

    def _parse_agent(self, a: dict) -> AgentSpec:
        rels = {}
        for other_id, rel_data in (a.get("relationships") or {}).items():
            if isinstance(rel_data, dict):
                rels[other_id] = RelationshipSpec(
                    trust=float(rel_data.get("trust", 0.5)), dynamic=rel_data.get("dynamic", "neutral"), history=rel_data.get("history", "")
                )
        return AgentSpec(
            agent_id=a.get("agent_id", "agent"), name=a.get("name", "Unknown"), role=a.get("role", "Team Member"),
            directness=float(a.get("directness", 0.5)), empathy=float(a.get("empathy", 0.5)),
            risk_aversion=float(a.get("risk_aversion", 0.5)), political_savvy=float(a.get("political_savvy", 0.5)),
            conflict_aversion=float(a.get("conflict_aversion", 0.5)),
            values=a.get("values", []), goals_in_scenario=a.get("goals_in_scenario", []), constraints=a.get("constraints", []),
            color=a.get("color", "white"), relationships=rels
        )

    def _parse_event(self, e: dict) -> ScheduledEvent:
        return ScheduledEvent(name=e.get("name", "Unnamed Event"), when=e.get("when", "TBD"))
