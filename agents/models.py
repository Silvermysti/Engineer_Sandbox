"""
agents/models.py — Pydantic models for the entire simulation.

Every piece of structured data that flows between agents, the game loop,
and the database is validated here.
"""

from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator

class Visibility(str, Enum):
    FULL    = "full"
    PARTIAL = "partial"
    SUMMARY = "summary"
    HIDDEN  = "hidden"

class EventType(str, Enum):
    PLAYER_DECISION      = "player_decision"
    AGENT_CONVERSATION   = "agent_conversation"
    DIRECT_MESSAGE       = "direct_message"
    GROUP_MEETING        = "group_meeting"
    SIDE_ACTION          = "side_action"
    ESCALATION           = "escalation"
    TENSION              = "tension"
    ANNOUNCEMENT         = "announcement"
    SCENARIO_END         = "scenario_end"

class Outcome(str, Enum):
    RESOLVED = "resolved"
    FAILED   = "failed"
    TIMEOUT  = "timeout"

class RelationshipSpec(BaseModel):
    trust: float = Field(0.5, ge=0.0, le=1.0, description="Initial trust level 0–1")
    dynamic: str = Field("neutral", description="e.g. 'mutual_respect', 'rivalry', 'patronizing'")
    history: str = Field("", description="Brief history note")

class AgentSpec(BaseModel):
    agent_id: str = Field(..., description="Unique slug, e.g. 'boss_sarah'")
    name: str
    role: str = Field(..., description="e.g. 'Engineering Manager'")

    directness: float     = Field(0.5, ge=0, le=1)
    empathy: float        = Field(0.5, ge=0, le=1)
    risk_aversion: float  = Field(0.5, ge=0, le=1)
    political_savvy: float= Field(0.5, ge=0, le=1)
    conflict_aversion: float = Field(0.5, ge=0, le=1)

    values: list[str]             = Field(default_factory=list)
    goals_in_scenario: list[str]  = Field(default_factory=list)
    constraints: list[str]        = Field(default_factory=list)

    relationships: dict[str, RelationshipSpec] = Field(default_factory=dict)
    color: str = Field("white")

    @field_validator("agent_id")
    @classmethod
    def _slug(cls, v: str) -> str:
        return v.strip().lower().replace(" ", "_")

class ScheduledEvent(BaseModel):
    name: str
    when: str        = Field(..., description="Human-readable, e.g. 'Tuesday 5pm'")
    importance: int  = Field(3, ge=1, le=5)
    flexibility: float = Field(0.5, ge=0, le=1)
    affected_agents: list[str]  = Field(default_factory=list)
    external: bool   = Field(False)
    description: str = Field("")
    consequences_if_missed: dict[str, Any] = Field(default_factory=dict)

class ScenarioSpec(BaseModel):
    title: str
    scenario_type: str
    description: str   = Field(..., description="Rich context paragraph shown to player")
    player_role: str   = Field("Tech Lead")
    stakes: list[str]  = Field(default_factory=list)

    cast: list[AgentSpec]
    scheduled_events: list[ScheduledEvent] = Field(default_factory=list)
    decision_options: list[str]
    opening_hook: str = Field("")
    time_pressure_baseline: float = Field(0.4, ge=0, le=1)

    @field_validator("cast")
    @classmethod
    def _min_cast(cls, v: list) -> list:
        if len(v) < 1:
            raise ValueError("Scenario must have at least one cast agent")
        return v

    @field_validator("decision_options")
    @classmethod
    def _min_options(cls, v: list) -> list:
        if len(v) < 2:
            raise ValueError("Need at least 2 decision options")
        return v

class AgentReaction(BaseModel):
    agent_id: str
    should_react: bool = True
    target: str = Field("player")
    message: str = Field("")
    reasoning: str = Field("")
    spawns_event: bool   = False
    event_type: str      = Field("agent_conversation")
    event_urgency: str   = Field("normal")
    new_emotional_state: str = Field("")
    player_satisfaction: float = Field(3.0, ge=1, le=5)

class DimensionScore(BaseModel):
    score: float = Field(..., ge=0, le=100)
    reasoning: str = Field("")

class ScoreReport(BaseModel):
    scenario_id: int
    overall_score: float
    immediate_outcome:  DimensionScore
    team_health:        DimensionScore
    long_term_impact:   DimensionScore
    learning_value:     DimensionScore
    integrity:          DimensionScore
    agent_satisfaction: DimensionScore
    key_decision:       str = Field("")
    missed_opportunity: str = Field("")
    pattern_detected:   str = Field("")
    generator_note:     str = Field("")
    agent_feedback: dict[str, dict[str, Any]] = Field(default_factory=dict)
