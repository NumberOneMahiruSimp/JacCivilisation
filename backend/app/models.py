from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Goal = Literal[
    "explore",
    "find_food",
    "trade",
    "support_ally",
    "avoid_conflict",
    "avoid_disaster",
    "migrate",
    "invent",
    "collapse",
    "evolve_culture",
    "negotiate",
    "rest",
]


@dataclass
class Memory:
    id: str
    agent_id: str
    type: str
    description: str
    related_agent_id: str | None
    importance: int
    timestamp: int

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Agent:
    id: str
    name: str
    x: int
    y: int
    health: int
    hunger: int
    strength: int
    personality: str
    faction: str
    goal: Goal = "explore"
    inventory: dict[str, int] = field(default_factory=lambda: {"food": 0, "ore": 0})
    memories: list[Memory] = field(default_factory=list)
    last_reasoning: str = "Rule scorer initialized."

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "health": self.health,
            "hunger": self.hunger,
            "strength": self.strength,
            "personality": self.personality,
            "faction": self.faction,
            "goal": self.goal,
            "inventory": self.inventory.copy(),
            "memories": [memory.to_dict() for memory in self.memories[-6:]],
            "last_reasoning": self.last_reasoning,
        }


@dataclass
class Relationship:
    agent_a: str
    agent_b: str
    trust_score: int = 50
    alliance_status: Literal["neutral", "allied", "strained", "enemy"] = "neutral"
    conflict_score: int = 0
    last_interaction: str = "No major interaction yet."

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Civilization:
    id: str
    name: str
    trait: str
    doctrine: str
    color: str
    capital_x: int
    capital_y: int
    population: int
    stability: int
    technology: int
    faith: int
    current_strategy: str = "expand"
    memories: list[Memory] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "trait": self.trait,
            "doctrine": self.doctrine,
            "color": self.color,
            "capital_x": self.capital_x,
            "capital_y": self.capital_y,
            "population": self.population,
            "stability": self.stability,
            "technology": self.technology,
            "faith": self.faith,
            "current_strategy": self.current_strategy,
            "memories": [memory.to_dict() for memory in self.memories[-8:]],
        }


@dataclass
class Event:
    id: str
    type: str
    x: int
    y: int
    severity: int
    affected_agents: list[str]
    created_tick: int
    summary: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class ReasoningLog:
    id: str
    agent_id: str
    source: Literal["rules", "fallback", "ollama"]
    prompt_context: str
    output_summary: str
    action_taken: str
    created_tick: int

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class World:
    width: int
    height: int
    tick: int
    agents: list[Agent]
    civilizations: list[Civilization]
    resources: list[dict]
    relationships: list[Relationship]
    terrain: list[dict] = field(default_factory=list)
    cities: list[dict] = field(default_factory=list)
    effects: list[dict] = field(default_factory=list)
    news: list[dict] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    reasoning_logs: list[ReasoningLog] = field(default_factory=list)
    paused: bool = False
