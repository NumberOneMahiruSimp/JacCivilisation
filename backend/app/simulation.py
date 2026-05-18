from __future__ import annotations

import random
from itertools import combinations

from .llm import StrategicReasoner
from .models import Agent, Civilization, Event, Memory, ReasoningLog, Relationship, World


NAMES = ["Mira", "Tovan", "Sera", "Kade", "Lio", "Anya", "Riven", "Noor", "Ilya", "Vega", "Sol", "Mako"]
PERSONALITIES = ["diplomatic", "bold", "cautious", "generous", "pragmatic", "curious"]
FACTIONS = ["Ember", "Vale", "Northstar"]
CIV_BLUEPRINTS = [
    ("civ-solarians", "Solarians", "tech-focused", "Progress through invention", "#f5b642"),
    ("civ-varku", "Varku", "militaristic", "Security through conquest", "#d55344"),
    ("civ-elyrians", "Elyrians", "diplomatic", "Survival through treaties", "#55b68b"),
    ("civ-nomads", "Nomads", "adaptive migrants", "Movement is life", "#4e9fd9"),
    ("civ-khepri", "Khepri", "religion-driven", "Meaning before empire", "#9b72d9"),
]


class CivilizationSimulation:
    def __init__(self, agent_count: int = 10, width: int = 12, height: int = 10, seed: int | None = None):
        self.random = random.Random(seed)
        self.reasoner = StrategicReasoner()
        self.world = World(
            width=width,
            height=height,
            tick=0,
            civilizations=self._make_civilizations(width, height),
            agents=[],
            resources=self._make_resources(width, height),
            terrain=self._make_terrain(width, height),
            cities=[],
            relationships=[],
        )
        self.world.agents = self._make_agents(max(2, min(agent_count, 30)), width, height)
        self.world.cities = self._make_cities()
        self.world.relationships = [
            Relationship(agent_a=a.id, agent_b=b.id) for a, b in combinations(self.world.agents, 2)
        ]

    def _make_civilizations(self, width: int, height: int) -> list[Civilization]:
        anchors = [(1, 1), (width - 2, 2), (width // 2, height // 2), (2, height - 2), (width - 3, height - 2)]
        civilizations = []
        for idx, (id_, name, trait, doctrine, color) in enumerate(CIV_BLUEPRINTS):
            x, y = anchors[idx]
            civilizations.append(
                Civilization(
                    id=id_,
                    name=name,
                    trait=trait,
                    doctrine=doctrine,
                    color=color,
                    capital_x=x,
                    capital_y=y,
                    population=self.random.randint(720, 1320),
                    stability=self.random.randint(58, 86),
                    technology=self.random.randint(28, 68),
                    faith=self.random.randint(25, 80),
                )
            )
        return civilizations

    def _make_agents(self, count: int, width: int, height: int) -> list[Agent]:
        agents = []
        for idx in range(count):
            civ = self.world.civilizations[idx % len(self.world.civilizations)]
            agents.append(
                Agent(
                    id=f"agent-{idx + 1}",
                    name=NAMES[idx % len(NAMES)],
                    x=min(width - 1, max(0, civ.capital_x + self.random.choice([-1, 0, 1]))),
                    y=min(height - 1, max(0, civ.capital_y + self.random.choice([-1, 0, 1]))),
                    health=self.random.randint(74, 100),
                    hunger=self.random.randint(20, 70),
                    strength=self.random.randint(35, 90),
                    personality=PERSONALITIES[idx % len(PERSONALITIES)],
                    faction=civ.name,
                )
            )
        return agents

    def _make_resources(self, width: int, height: int) -> list[dict]:
        resources = []
        for idx in range(34):
            resources.append(
                {
                    "id": f"res-{idx + 1}",
                    "type": "food" if idx % 4 else "ore",
                    "x": self.random.randrange(width),
                    "y": self.random.randrange(height),
                    "amount": self.random.randint(1, 5),
                }
            )
        return resources

    def _make_terrain(self, width: int, height: int) -> list[dict]:
        terrain = []
        for y in range(height):
            for x in range(width):
                roll = (x * 13 + y * 7 + self.random.randint(0, 8)) % 11
                terrain_type = "forest" if roll in {0, 4} else "water" if roll == 2 else "mountain" if roll == 7 else "plains"
                terrain.append({"x": x, "y": y, "type": terrain_type, "heat": 0, "plague": 0, "flood": 0, "prosperity": 0})
        return terrain

    def _make_cities(self) -> list[dict]:
        cities = []
        for civ in self.world.civilizations:
            cities.append(
                {
                    "id": f"city-{civ.id}",
                    "name": f"{civ.name} Prime",
                    "civ_id": civ.id,
                    "x": civ.capital_x,
                    "y": civ.capital_y,
                    "population": civ.population // 4,
                    "status": "stable",
                }
            )
        return cities

    def tick(self) -> dict:
        if self.world.paused:
            return self.snapshot()
        self.world.tick += 1
        self._decay_effects()
        for agent in self.world.agents:
            agent.hunger = min(100, agent.hunger + self.random.randint(4, 9))
            if agent.hunger > 96:
                agent.health = max(0, agent.health - 4)
            self._choose_and_apply_action(agent)
        self._maybe_social_reasoning()
        return self.snapshot()

    def _choose_and_apply_action(self, agent: Agent) -> None:
        disaster = self._nearby_disaster(agent)
        recent_disaster_memory = any(memory.type == "disaster" and self.world.tick - memory.timestamp <= 1 for memory in agent.memories)
        hungry_ally = self._nearby_hungry_ally(agent)
        nearest_food = self._nearest_resource(agent, "food")

        if disaster or recent_disaster_memory:
            agent.goal = "avoid_disaster"
            if disaster:
                self._move_away(agent, disaster.x, disaster.y)
                self._remember(agent, "disaster", f"Moved away from {disaster.type} near ({disaster.x}, {disaster.y}).", None, 7)
            else:
                self._wander(agent)
            agent.last_reasoning = "Rules: recent disaster memory raised evacuation priority."
        elif agent.hunger > 80 and nearest_food:
            agent.goal = "find_food"
            self._move_toward(agent, nearest_food["x"], nearest_food["y"])
            self._collect_if_here(agent)
            agent.last_reasoning = "Rules: hunger exceeded 80, nearest food became the top goal."
        elif hungry_ally and agent.inventory.get("food", 0) > 0:
            agent.goal = "support_ally"
            self._share_food(agent, hungry_ally)
        else:
            agent.goal = self.random.choice(["explore", "trade", "rest", "invent"])
            if agent.goal == "explore":
                self._wander(agent)
            elif agent.goal == "rest":
                agent.health = min(100, agent.health + 2)
            agent.last_reasoning = f"Rules: no urgent threat, selected {agent.goal}."
            self._log_rules(agent, agent.last_reasoning, agent.goal)

    def _nearby_disaster(self, agent: Agent) -> Event | None:
        for event in reversed(self.world.events):
            if event.type in {"famine", "storm", "disease"} and abs(agent.x - event.x) + abs(agent.y - event.y) <= event.severity:
                return event
        return None

    def _nearby_hungry_ally(self, agent: Agent) -> Agent | None:
        for other in self.world.agents:
            if other.id == agent.id or other.hunger < 88:
                continue
            rel = self.relationship_between(agent.id, other.id)
            close = abs(agent.x - other.x) + abs(agent.y - other.y) <= 1
            if close and rel.trust_score >= 45:
                return other
        return None

    def _nearest_resource(self, agent: Agent, resource_type: str) -> dict | None:
        candidates = [res for res in self.world.resources if res["type"] == resource_type and res["amount"] > 0]
        if not candidates:
            return None
        return min(candidates, key=lambda res: abs(agent.x - res["x"]) + abs(agent.y - res["y"]))

    def _move_toward(self, agent: Agent, x: int, y: int) -> None:
        agent.x += 0 if agent.x == x else 1 if x > agent.x else -1
        agent.y += 0 if agent.y == y else 1 if y > agent.y else -1

    def _move_away(self, agent: Agent, x: int, y: int) -> None:
        agent.x = min(self.world.width - 1, max(0, agent.x + (1 if agent.x >= x else -1)))
        agent.y = min(self.world.height - 1, max(0, agent.y + (1 if agent.y >= y else -1)))

    def _wander(self, agent: Agent) -> None:
        agent.x = min(self.world.width - 1, max(0, agent.x + self.random.choice([-1, 0, 1])))
        agent.y = min(self.world.height - 1, max(0, agent.y + self.random.choice([-1, 0, 1])))

    def _collect_if_here(self, agent: Agent) -> None:
        for res in list(self.world.resources):
            if res["type"] == "food" and res["x"] == agent.x and res["y"] == agent.y and res["amount"] > 0:
                res["amount"] -= 1
                agent.inventory["food"] += 1
                agent.hunger = max(0, agent.hunger - 28)
                self._remember(agent, "resource", f"{agent.name} found food at ({agent.x}, {agent.y}).", None, 5)
                self._log_rules(agent, "Rules: collected food on current tile.", "find_food")
                if res["amount"] <= 0:
                    self.world.resources.remove(res)
                return

    def _share_food(self, giver: Agent, receiver: Agent) -> None:
        giver.inventory["food"] -= 1
        receiver.inventory["food"] += 1
        receiver.hunger = max(0, receiver.hunger - 22)
        rel = self.relationship_between(giver.id, receiver.id)
        rel.trust_score = min(100, rel.trust_score + 12)
        rel.alliance_status = "allied" if rel.trust_score >= 70 else rel.alliance_status
        rel.last_interaction = f"{giver.name} shared food with {receiver.name}."
        self._remember(giver, "trade", rel.last_interaction, receiver.id, 6)
        self._remember(receiver, "trade", rel.last_interaction, giver.id, 7)
        giver.last_reasoning = "Rules: nearby ally was starving and food was available to share."
        self._log_rules(giver, giver.last_reasoning, "support_ally")

    def _maybe_social_reasoning(self) -> None:
        if self.world.tick % 5 != 0 and not any(event.created_tick == self.world.tick for event in self.world.events):
            return
        agent = max(self.world.agents, key=lambda item: item.hunger)
        context = f"tick={self.world.tick}; hunger={agent.hunger}; memories={[m.description for m in agent.memories[-2:]]}"
        result = self.reasoner.reason(agent.name, context, "negotiate food support")
        agent.goal = "negotiate"
        agent.last_reasoning = result["summary"]
        self.world.reasoning_logs.append(
            ReasoningLog(
                id=f"reason-{len(self.world.reasoning_logs) + 1}",
                agent_id=agent.id,
                source=result["source"],
                prompt_context=context,
                output_summary=result["summary"],
                action_taken=result["action"],
                created_tick=self.world.tick,
            )
        )

    def trigger_disaster(self, disaster_type: str = "famine", x: int | None = None, y: int | None = None, radius: int = 3) -> Event:
        x = self.world.width // 2 if x is None else x
        y = self.world.height // 2 if y is None else y
        before = len(self.world.resources)
        self.world.resources = [
            res for res in self.world.resources if abs(res["x"] - x) + abs(res["y"] - y) > radius or res["type"] != "food"
        ]
        affected = [
            agent.id for agent in self.world.agents if abs(agent.x - x) + abs(agent.y - y) <= radius + 1
        ]
        if not affected and self.world.agents:
            nearest = min(self.world.agents, key=lambda agent: abs(agent.x - x) + abs(agent.y - y))
            affected = [nearest.id]
        event = Event(
            id=f"event-{len(self.world.events) + 1}",
            type=disaster_type,
            x=x,
            y=y,
            severity=radius,
            affected_agents=affected,
            created_tick=self.world.tick,
            summary=f"{disaster_type.title()} removed {before - len(self.world.resources)} food nodes near ({x}, {y}).",
        )
        self.world.events.append(event)
        for agent in self.world.agents:
            if agent.id in affected:
                agent.goal = "avoid_disaster"
                self._remember(agent, "disaster", event.summary, None, 9)
        self._maybe_social_reasoning()
        return event

    def trigger_world_event(self, event_type: str, x: int | None = None, y: int | None = None, radius: int = 3) -> Event:
        normalized = event_type.strip().lower().replace(" ", "_")
        if normalized in {"famine", "storm", "disease"}:
            normalized = {"disease": "plague", "storm": "climate_collapse"}.get(normalized, normalized)
        x = self.world.width // 2 if x is None else x
        y = self.world.height // 2 if y is None else y
        affected = [agent.id for agent in self.world.agents if abs(agent.x - x) + abs(agent.y - y) <= radius + 2]
        if not affected and self.world.agents:
            affected = [min(self.world.agents, key=lambda agent: abs(agent.x - x) + abs(agent.y - y)).id]

        event = Event(
            id=f"event-{len(self.world.events) + 1}",
            type=normalized,
            x=x,
            y=y,
            severity=radius,
            affected_agents=affected,
            created_tick=self.world.tick,
            summary=self._event_summary(normalized, x, y, radius),
        )
        self.world.events.append(event)
        self._apply_terrain_effects(normalized, x, y, radius)
        self._apply_civilization_reactions(event)
        self._apply_agent_reactions(event)
        self._add_cinematic_effects(normalized, x, y, radius)
        self._add_news(normalized, event.summary)
        self._maybe_social_reasoning()
        return event

    def _event_summary(self, event_type: str, x: int, y: int, radius: int) -> str:
        summaries = {
            "war": f"Border war erupts across the central marches near ({x}, {y}).",
            "plague": f"A deadly plague spreads through cities within {radius} tiles of ({x}, {y}).",
            "meteor": f"Meteor strike impacts ({x}, {y}), scattering fires and refugees.",
            "ai_uprising": "Autonomous machine councils begin seizing command networks.",
            "resource_boom": f"New resource veins bloom around ({x}, {y}), igniting trade routes.",
            "religion": "A new revelation fractures old loyalties and inspires mass conversion.",
            "climate_collapse": f"Climate collapse floods and scorches regions near ({x}, {y}).",
            "alien_contact": "Alien contact shocks every doctrine and reorders diplomacy.",
            "technological_revolution": "A technological revolution accelerates invention and social unrest.",
            "famine": f"Famine removes food security near ({x}, {y}).",
            "nuclear_strike": f"Nuclear fire devastates the region around ({x}, {y}).",
        }
        return summaries.get(event_type, f"{event_type.replace('_', ' ').title()} changes the world near ({x}, {y}).")

    def _apply_terrain_effects(self, event_type: str, x: int, y: int, radius: int) -> None:
        for tile in self.world.terrain:
            distance = abs(tile["x"] - x) + abs(tile["y"] - y)
            if distance > radius:
                continue
            if event_type in {"meteor", "war", "nuclear_strike"}:
                tile["heat"] = max(tile["heat"], radius - distance + 2)
            if event_type == "plague":
                tile["plague"] = max(tile["plague"], radius - distance + 2)
            if event_type == "climate_collapse":
                tile["flood"] = max(tile["flood"], radius - distance + 1)
            if event_type == "resource_boom":
                tile["prosperity"] = max(tile["prosperity"], radius - distance + 2)
                self.world.resources.append(
                    {"id": f"boom-{len(self.world.resources) + 1}", "type": "ore", "x": tile["x"], "y": tile["y"], "amount": 4}
                )
        for city in self.world.cities:
            if abs(city["x"] - x) + abs(city["y"] - y) <= radius:
                city["status"] = {
                    "plague": "quarantined",
                    "meteor": "burning",
                    "war": "besieged",
                    "climate_collapse": "flooded",
                    "nuclear_strike": "ruined",
                }.get(event_type, "mobilized")
                if event_type in {"plague", "meteor", "war", "nuclear_strike"}:
                    city["population"] = max(80, int(city["population"] * 0.82))

    def _apply_civilization_reactions(self, event: Event) -> None:
        for civ in self.world.civilizations:
            if event.type == "plague":
                strategy = {
                    "tech-focused": "invent_vaccine",
                    "militaristic": "invade_for_medicine",
                    "diplomatic": "negotiate_aid",
                    "adaptive migrants": "migrate",
                    "religion-driven": "quarantine",
                }.get(civ.trait, "quarantine")
                civ.population = max(200, int(civ.population * 0.94))
                civ.stability = max(0, civ.stability - 8)
            elif event.type == "meteor":
                strategy = "migrate" if civ.trait == "adaptive migrants" else "rebuild" if civ.trait != "militaristic" else "secure_crater"
                civ.stability = max(0, civ.stability - 10)
            elif event.type == "war":
                strategy = "invade" if civ.trait == "militaristic" else "negotiate_ceasefire" if civ.trait == "diplomatic" else "fortify"
                civ.stability = max(0, civ.stability - 6)
            elif event.type == "resource_boom":
                strategy = "expand_trade"
                civ.stability = min(100, civ.stability + 5)
            elif event.type == "religion":
                strategy = "declare_divine_sign" if civ.trait == "religion-driven" else "contain_ideology"
                civ.faith = min(100, civ.faith + 12)
            elif event.type in {"ai_uprising", "alien_contact", "technological_revolution"}:
                strategy = "invent" if civ.trait == "tech-focused" else "evolve_culture"
                civ.technology = min(100, civ.technology + 10)
            else:
                strategy = "adapt"
            civ.current_strategy = strategy
            self._remember_civ(civ, event.type, f"{civ.name} chose {strategy.replace('_', ' ')} after {event.summary}", 8)

    def _apply_agent_reactions(self, event: Event) -> None:
        for agent in self.world.agents:
            civ = self._civ_for_agent(agent)
            if event.type == "plague":
                agent.goal = "avoid_disaster" if civ.trait in {"religion-driven", "diplomatic"} else "migrate"
                agent.health = max(0, agent.health - self.random.randint(3, 9))
            elif event.type == "meteor":
                agent.goal = "migrate" if agent.id in event.affected_agents else "invent"
                if agent.id in event.affected_agents:
                    self._move_away(agent, event.x, event.y)
            elif event.type == "war":
                agent.goal = "avoid_conflict" if civ.trait != "militaristic" else "negotiate"
            elif event.type in {"resource_boom", "technological_revolution", "ai_uprising", "alien_contact"}:
                agent.goal = "invent"
            else:
                agent.goal = "evolve_culture"
            if agent.id in event.affected_agents:
                self._remember(agent, event.type, event.summary, None, 9)

    def _add_cinematic_effects(self, event_type: str, x: int, y: int, radius: int) -> None:
        effect_map = {
            "plague": ["red_fog", "quarantine_border", "panic_pulse"],
            "meteor": ["screen_shake", "meteor_crater", "fire_spread", "refugee_flow"],
            "war": ["battle_flash", "alliance_lines", "smoke_column"],
            "resource_boom": ["gold_pulse", "trade_route"],
            "religion": ["faith_wave", "culture_split"],
            "climate_collapse": ["flood_zone", "storm_clouds"],
            "alien_contact": ["sky_beam", "signal_ring"],
            "ai_uprising": ["machine_glitch", "red_grid"],
            "technological_revolution": ["blueprint_burst", "invention_sparks"],
            "nuclear_strike": ["screen_shake", "white_flash", "fallout"],
        }
        for effect_type in effect_map.get(event_type, ["world_pulse"]):
            self.world.effects.append(
                {"id": f"effect-{len(self.world.effects) + 1}", "type": effect_type, "x": x, "y": y, "radius": radius, "ttl": 8}
            )

    def _add_news(self, event_type: str, summary: str) -> None:
        headline = {
            "plague": "Global plague alert: quarantine borders rise overnight",
            "meteor": "Meteor impact sends refugees across the southern roads",
            "war": "Border war ignites as alliances fracture",
            "resource_boom": "Resource boom sparks a race for new trade routes",
            "religion": "New faith movement splits old cultural blocs",
            "climate_collapse": "Climate collapse redraws habitable territory",
            "alien_contact": "Alien contact forces emergency world council",
            "ai_uprising": "AI uprising disrupts command networks",
            "technological_revolution": "Technological revolution accelerates invention",
            "nuclear_strike": "Nuclear strike leaves a forbidden zone",
        }.get(event_type, f"{event_type.replace('_', ' ').title()} reshapes the world")
        self.world.news.append(
            {"id": f"news-{len(self.world.news) + 1}", "tick": self.world.tick, "headline": headline, "body": summary}
        )

    def _decay_effects(self) -> None:
        for effect in self.world.effects:
            effect["ttl"] -= 1
        self.world.effects = [effect for effect in self.world.effects if effect["ttl"] > 0]
        for tile in self.world.terrain:
            for key in ("heat", "plague", "flood", "prosperity"):
                tile[key] = max(0, tile[key] - 1)

    def _civ_for_agent(self, agent: Agent) -> Civilization:
        return next((civ for civ in self.world.civilizations if civ.name == agent.faction), self.world.civilizations[0])

    def _remember_civ(self, civ: Civilization, type_: str, description: str, importance: int) -> None:
        civ.memories.append(
            Memory(
                id=f"mem-{civ.id}-{len(civ.memories) + 1}",
                agent_id=civ.id,
                type=type_,
                description=description,
                related_agent_id=None,
                importance=importance,
                timestamp=self.world.tick,
            )
        )

    def relationship_between(self, a: str, b: str) -> Relationship:
        for rel in self.world.relationships:
            if {rel.agent_a, rel.agent_b} == {a, b}:
                return rel
        rel = Relationship(agent_a=a, agent_b=b)
        self.world.relationships.append(rel)
        return rel

    def agent_detail(self, agent_id: str) -> dict | None:
        agent = next((item for item in self.world.agents if item.id == agent_id), None)
        if not agent:
            return None
        detail = agent.to_dict()
        detail["relationships"] = [
            rel.to_dict() for rel in self.world.relationships if agent_id in {rel.agent_a, rel.agent_b}
        ]
        return detail

    def _remember(self, agent: Agent, type_: str, description: str, related_agent_id: str | None, importance: int) -> None:
        agent.memories.append(
            Memory(
                id=f"mem-{agent.id}-{len(agent.memories) + 1}",
                agent_id=agent.id,
                type=type_,
                description=description,
                related_agent_id=related_agent_id,
                importance=importance,
                timestamp=self.world.tick,
            )
        )

    def _log_rules(self, agent: Agent, summary: str, action: str) -> None:
        self.world.reasoning_logs.append(
            ReasoningLog(
                id=f"reason-{len(self.world.reasoning_logs) + 1}",
                agent_id=agent.id,
                source="rules",
                prompt_context=f"tick={self.world.tick}; hunger={agent.hunger}; health={agent.health}",
                output_summary=summary,
                action_taken=action,
                created_tick=self.world.tick,
            )
        )

    def pause(self) -> dict:
        self.world.paused = True
        return self.snapshot()

    def resume(self) -> dict:
        self.world.paused = False
        return self.snapshot()

    def snapshot(self) -> dict:
        return {
            "width": self.world.width,
            "height": self.world.height,
            "tick": self.world.tick,
            "paused": self.world.paused,
            "civilizations": [civ.to_dict() for civ in self.world.civilizations],
            "agents": [agent.to_dict() for agent in self.world.agents],
            "resources": [res.copy() for res in self.world.resources],
            "terrain": [tile.copy() for tile in self.world.terrain],
            "cities": [city.copy() for city in self.world.cities],
            "relationships": [rel.to_dict() for rel in self.world.relationships],
            "effects": [effect.copy() for effect in self.world.effects[-40:]],
            "news": [item.copy() for item in self.world.news[-20:]],
            "events": [event.to_dict() for event in self.world.events[-20:]],
            "reasoning_logs": [log.to_dict() for log in self.world.reasoning_logs[-30:]],
        }
