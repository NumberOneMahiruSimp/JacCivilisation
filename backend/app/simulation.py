from __future__ import annotations

import random
from itertools import combinations

from .jac_engine import JacDecisionEngine
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
        self.jac_engine = JacDecisionEngine()
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
        for civ in self.world.civilizations:
            civ.recent_deaths = 0
        self.world.last_casualties = 0
        self._decay_effects()
        self._apply_ongoing_crisis_losses()
        for agent in self.world.agents:
            agent.hunger = min(100, agent.hunger + self.random.randint(4, 9))
            if agent.hunger > 96:
                agent.health = max(0, agent.health - 4)
        jac_decisions = self.jac_engine.decide_agents(
            {
                "world": {"tick": self.world.tick, "width": self.world.width, "height": self.world.height},
                "agents": [self._jac_agent_context(agent) for agent in self.world.agents],
            }
        )
        for agent in self.world.agents:
            self._choose_and_apply_action(agent, jac_decisions.get(agent.id))
        self._advance_orders()
        self._apply_jac_civilization_decisions()
        self._maybe_social_reasoning()
        return self.snapshot()

    def _choose_and_apply_action(self, agent: Agent, jac_decision: dict | None = None) -> None:
        disaster = self._nearby_disaster(agent)
        recent_disaster_memory = any(memory.type == "disaster" and self.world.tick - memory.timestamp <= 1 for memory in agent.memories)
        hungry_ally = self._nearby_hungry_ally(agent)
        nearest_food = self._nearest_resource(agent, "food")
        jac_goal = jac_decision.get("goal") if jac_decision else None
        jac_reason = jac_decision.get("reason") if jac_decision else None
        source = "jac" if jac_goal else "rules"

        if (jac_goal == "avoid_disaster" or not jac_goal) and (disaster or recent_disaster_memory):
            agent.goal = "avoid_disaster"
            if disaster:
                self._move_away(agent, disaster.x, disaster.y)
                self._remember(agent, "disaster", f"Moved away from {disaster.type} near ({disaster.x}, {disaster.y}).", None, 7)
            else:
                self._wander(agent)
            agent.last_reasoning = jac_reason or "Rules: recent disaster memory raised evacuation priority."
            self._log_rules(agent, agent.last_reasoning, agent.goal, source)
        elif (jac_goal == "find_food" or not jac_goal) and agent.hunger > 80 and nearest_food:
            agent.goal = "find_food"
            self._move_toward(agent, nearest_food["x"], nearest_food["y"])
            self._collect_if_here(agent)
            agent.last_reasoning = jac_reason or "Rules: hunger exceeded 80, nearest food became the top goal."
            self._log_rules(agent, agent.last_reasoning, agent.goal, source)
        elif (jac_goal == "support_ally" or not jac_goal) and hungry_ally and agent.inventory.get("food", 0) > 0:
            agent.goal = "support_ally"
            self._share_food(agent, hungry_ally)
        else:
            agent.goal = jac_goal if jac_goal in {"explore", "trade", "rest", "invent", "patrol", "evolve_culture"} else self.random.choice(["explore", "trade", "rest", "invent"])
            if agent.goal == "explore":
                self._wander(agent)
            elif agent.goal == "patrol":
                self._wander(agent)
                agent.strength = min(100, agent.strength + 1)
            elif agent.goal == "rest":
                agent.health = min(100, agent.health + 2)
            elif agent.goal == "evolve_culture":
                agent.health = min(100, agent.health + 1)
            agent.last_reasoning = jac_reason or f"Rules: no urgent threat, selected {agent.goal}."
            self._log_rules(agent, agent.last_reasoning, agent.goal, source)

    def _jac_agent_context(self, agent: Agent) -> dict:
        disaster = self._nearby_disaster(agent)
        hungry_ally = self._nearby_hungry_ally(agent)
        nearest_food = self._nearest_resource(agent, "food")
        civ = self._civ_for_agent(agent)
        return {
            "id": agent.id,
            "name": agent.name,
            "hunger": agent.hunger,
            "health": agent.health,
            "strength": agent.strength,
            "inventory": agent.inventory.copy(),
            "faction": agent.faction,
            "civ_trait": civ.trait,
            "nearby_disaster": disaster.to_dict() if disaster else None,
            "nearby_hungry_ally": hungry_ally is not None,
            "nearest_food": nearest_food.copy() if nearest_food else None,
        }

    def _nearby_disaster(self, agent: Agent) -> Event | None:
        for event in reversed(self.world.events):
            if event.type in {"famine", "storm", "disease", "plague", "meteor", "war", "nuclear_strike", "climate_collapse"} and abs(agent.x - event.x) + abs(agent.y - event.y) <= event.severity + 1:
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
        if normalized == "war":
            attacker, target = self._war_pair_near(x, y)
            if attacker and target:
                self._create_war_order(attacker, target, "God Mode war")
        self._apply_terrain_effects(normalized, x, y, radius)
        self._apply_civilization_reactions(event)
        self._apply_agent_reactions(event)
        self._add_cinematic_effects(normalized, x, y, radius)
        self._add_news(normalized, event.summary)
        self._maybe_social_reasoning()
        return event

    def apply_command(self, text: str) -> dict:
        command = " ".join(text.strip().split())
        lowered = command.lower()
        civs = {civ.name.lower(): civ for civ in self.world.civilizations if civ.status == "alive"}
        mentioned = [civ for name, civ in civs.items() if name in lowered]
        command_message = "Command understood -> Jac walker triggered -> World updated"

        def finish(type_: str, extra: dict | None = None) -> dict:
            self._apply_jac_civilization_decisions(trigger=f"command:{type_}")
            payload = {"ok": True, "type": type_, "message": command_message, "state": self.snapshot()}
            if extra:
                payload.update(extra)
            return payload

        if any(word in lowered for word in ("attack", "war", "invade", "fight")) and len(mentioned) >= 2:
            order = self._create_war_order(mentioned[0], mentioned[1], command)
            self._add_news("war", f"Command accepted: {mentioned[0].name} marches on {mentioned[1].name}.")
            return finish("war_order", {"order": order})
        if "trade" in lowered and len(mentioned) >= 2:
            order = self._create_trade_order(mentioned[0], mentioned[1], command)
            self._add_news("resource_boom", f"Command accepted: {mentioned[0].name} opens trade with {mentioned[1].name}.")
            return finish("trade", {"order": order})
        if any(word in lowered for word in ("ally", "alliance", "peace", "truce")) and len(mentioned) >= 2:
            self._create_alliance(mentioned[0], mentioned[1], command)
            self._add_news("alliance", f"Command accepted: {mentioned[0].name} and {mentioned[1].name} form a green route.")
            return finish("alliance")
        if "plague" in lowered and mentioned:
            civ = mentioned[0]
            self.trigger_world_event("plague", civ.capital_x, civ.capital_y, 4)
            return finish("plague")
        if "meteor" in lowered:
            x, y = self._coordinates_from_command(lowered, mentioned)
            self.trigger_world_event("meteor", x, y, 3)
            return finish("meteor")
        if "nuclear" in lowered and mentioned:
            civ = mentioned[0]
            self.trigger_world_event("nuclear_strike", civ.capital_x, civ.capital_y, 4)
            return finish("nuclear_strike")
        if any(word in lowered for word in ("stop war", "ceasefire", "stop fighting")):
            self._declare_ceasefire(mentioned[0] if mentioned else None, mentioned[1] if len(mentioned) > 1 else None)
            self._add_news("ceasefire", "Command accepted: active war routes are standing down.")
            return finish("ceasefire")
        if "migrate" in lowered and mentioned:
            direction = next((word for word in ("north", "south", "east", "west") if word in lowered), "north")
            self._migrate_civilization(mentioned[0], direction)
            self._add_news("migration", f"Command accepted: {mentioned[0].name} begins moving {direction}.")
            return finish("migration")
        if "tech boost" in lowered and mentioned or ("give" in lowered and "tech" in lowered and mentioned):
            civ = mentioned[0]
            civ.technology = min(100, civ.technology + 18)
            civ.current_strategy = "research"
            self._remember_civ(civ, "technology", f"Command granted a technology boost to {civ.name}.", 7)
            self._add_news("technological_revolution", f"Command accepted: {civ.name} receives a rapid technology boost.")
            return finish("tech_boost")

        self._add_news("command", f"Command heard but no matching order was found: {command}")
        return {"ok": False, "type": "unknown", "message": "Try: 'Varku attack Khepri', 'Khepri ally Solarians', 'meteor desert', or 'give Solarians tech boost'.", "state": self.snapshot()}

    def _create_war_order(self, attacker: Civilization, target: Civilization, command: str) -> dict:
        existing = self._active_order("war", attacker.id, target.id)
        if existing:
            existing["progress"] = max(int(existing.get("progress", 0)), 8)
            return existing
        order = {
            "id": f"order-{len(self.world.orders) + 1}",
            "type": "war",
            "status": "active",
            "source_civ_id": attacker.id,
            "target_civ_id": target.id,
            "source": attacker.name,
            "target": target.name,
            "progress": 0,
            "created_tick": self.world.tick,
            "command": command,
        }
        self.world.orders.append(order)
        attacker.current_strategy = "invade"
        target.current_strategy = "defend"
        self._mark_faction_relationship(attacker.name, target.name, "enemy", trust=-18, conflict=42)
        for agent in self.world.agents:
            if agent.faction == attacker.name:
                agent.goal = "invade"
                self._move_toward(agent, target.capital_x, target.capital_y)
            elif agent.faction == target.name:
                agent.goal = "avoid_conflict"
        self._apply_population_loss(target, self.random.randint(4, 9), "war", attacker, remember=False)
        target.stability = max(0, target.stability - 2)
        self._remember_civ(attacker, "war", f"{attacker.name} declared war on {target.name}.", 8)
        self._remember_civ(target, "war", f"{target.name} prepares defenses against {attacker.name}.", 8)
        return order

    def _create_alliance(self, a: Civilization, b: Civilization, command: str) -> None:
        if self._active_order("alliance", a.id, b.id) or self._active_order("alliance", b.id, a.id):
            return
        self._mark_faction_relationship(a.name, b.name, "allied", trust=28, conflict=-24)
        self.world.orders.append(
            {
                "id": f"order-{len(self.world.orders) + 1}",
                "type": "alliance",
                "status": "active",
                "source_civ_id": a.id,
                "target_civ_id": b.id,
                "source": a.name,
                "target": b.name,
                "progress": 100,
                "created_tick": self.world.tick,
                "command": command,
            }
        )
        self._remember_civ(a, "alliance", f"{a.name} formed an alliance with {b.name}.", 7)
        self._remember_civ(b, "alliance", f"{b.name} formed an alliance with {a.name}.", 7)

    def _create_trade_order(self, a: Civilization, b: Civilization, command: str) -> dict:
        existing = self._active_order("trade", a.id, b.id) or self._active_order("trade", b.id, a.id)
        if existing:
            return existing
        self._mark_faction_relationship(a.name, b.name, "allied", trust=16, conflict=-12)
        a.stability = min(100, a.stability + 3)
        b.stability = min(100, b.stability + 3)
        order = {
            "id": f"order-{len(self.world.orders) + 1}",
            "type": "trade",
            "status": "active",
            "source_civ_id": a.id,
            "target_civ_id": b.id,
            "source": a.name,
            "target": b.name,
            "progress": 100,
            "created_tick": self.world.tick,
            "command": command,
        }
        self.world.orders.append(order)
        self._remember_civ(a, "trade", f"{a.name} opened a trade route with {b.name}.", 6)
        self._remember_civ(b, "trade", f"{b.name} opened a trade route with {a.name}.", 6)
        return order

    def _active_order(self, type_: str, source_id: str, target_id: str | None = None) -> dict | None:
        for order in reversed(self.world.orders):
            if order.get("status") != "active" or order.get("type") != type_:
                continue
            if order.get("source_civ_id") != source_id:
                continue
            if target_id is None or order.get("target_civ_id") == target_id:
                return order
        return None

    def _mark_faction_relationship(self, faction_a: str, faction_b: str, status: str, trust: int = 0, conflict: int = 0) -> None:
        a_agents = [agent for agent in self.world.agents if agent.faction == faction_a]
        b_agents = [agent for agent in self.world.agents if agent.faction == faction_b]
        for a in a_agents:
            for b in b_agents:
                rel = self.relationship_between(a.id, b.id)
                rel.alliance_status = status
                rel.trust_score = max(0, min(100, rel.trust_score + trust))
                rel.conflict_score = max(0, min(100, rel.conflict_score + conflict))
                rel.last_interaction = f"{faction_a} and {faction_b}: {status} by command."

    def _nearest_civ(self, x: int, y: int, exclude: str | None = None) -> Civilization | None:
        candidates = [civ for civ in self.world.civilizations if civ.status == "alive" and civ.id != exclude]
        if not candidates:
            return None
        return min(candidates, key=lambda civ: abs(civ.capital_x - x) + abs(civ.capital_y - y))

    def _advance_orders(self) -> None:
        for order in self.world.orders:
            if order.get("status") != "active":
                continue
            if order.get("type") in {"alliance", "trade"}:
                order["progress"] = (int(order.get("progress", 0)) + 6) % 101
                continue
            if order.get("type") != "war":
                continue
            attacker = next((civ for civ in self.world.civilizations if civ.id == order.get("source_civ_id") and civ.status == "alive"), None)
            target = next((civ for civ in self.world.civilizations if civ.id == order.get("target_civ_id") and civ.status == "alive"), None)
            if not attacker or not target:
                order["status"] = "ended"
                continue
            order["progress"] = min(100, int(order.get("progress", 0)) + 12)
            for agent in self.world.agents:
                if agent.faction == attacker.name:
                    agent.goal = "invade"
                    self._move_toward(agent, target.capital_x, target.capital_y)
            if order["progress"] >= 65:
                self._apply_population_loss(target, max(8, self.random.randint(10, 24)), "war", attacker, remember=False)
            if order["progress"] >= 100:
                order["progress"] = 15

    def _apply_jac_civilization_decisions(self, trigger: str = "tick") -> None:
        live_civs = [civ for civ in self.world.civilizations if civ.status == "alive"]
        if not live_civs:
            return
        decisions = self.jac_engine.decide_civilizations(
            {
                "world": {
                    "tick": self.world.tick,
                    "trigger": trigger,
                    "active_events": [event.type for event in self.world.events[-3:]],
                },
                "civilizations": [self._jac_civilization_context(civ) for civ in live_civs],
            }
        )
        for civ in live_civs:
            decision = decisions.get(civ.id)
            if not decision:
                continue
            action = str(decision.get("action", "adapt")).lower()
            self._record_jac_trace(decision)
            civ.current_strategy = action
            if action == "attack":
                target = self._choose_attack_target(civ)
                if target:
                    self._create_war_order(civ, target, "Jac walker attack decision")
            elif action == "ally":
                partner = self._choose_partner(civ)
                if partner:
                    self._create_alliance(civ, partner, "Jac walker alliance decision")
            elif action == "trade":
                partner = self._choose_partner(civ)
                if partner:
                    self._create_trade_order(civ, partner, "Jac walker trade decision")
            elif action == "fortify":
                civ.stability = min(100, civ.stability + 2)
            elif action == "recover":
                civ.stability = min(100, civ.stability + 2)
                civ.population += max(1, civ.population // 200)
            elif action == "research":
                civ.technology = min(100, civ.technology + 2)
            elif action == "migrate":
                self._migrate_civilization(civ, "north")
            elif action == "declare_ceasefire":
                self._declare_ceasefire(civ, None)
            elif action == "adapt":
                civ.stability = min(100, civ.stability + 1)
            self.world.reasoning_logs.append(
                ReasoningLog(
                    id=f"reason-{len(self.world.reasoning_logs) + 1}",
                    agent_id=civ.id,
                    source="jac",
                    prompt_context=self._trace_context(decision.get("inputs", {})),
                    output_summary=decision.get("reason", f"{civ.name} chose {action}."),
                    action_taken=action,
                    created_tick=self.world.tick,
                )
            )

    def _jac_civilization_context(self, civ: Civilization) -> dict:
        nearby_enemy = self._nearby_enemy_for(civ)
        active_event = self.world.events[-1].type if self.world.events else ""
        threat = 0
        if nearby_enemy:
            threat += 45
        threat += min(40, civ.recent_deaths // 4)
        threat += sum(18 for order in self.world.orders if order.get("status") == "active" and order.get("type") == "war" and civ.id in {order.get("source_civ_id"), order.get("target_civ_id")})
        return {
            **civ.to_dict(),
            "nearby_enemy": nearby_enemy.name if nearby_enemy else "",
            "enemy_stability": nearby_enemy.stability if nearby_enemy else 100,
            "threat_level": min(100, threat),
            "trade_routes": len([order for order in self.world.orders if order.get("status") == "active" and order.get("type") == "trade" and civ.id in {order.get("source_civ_id"), order.get("target_civ_id")}]),
            "active_event": active_event,
        }

    def _record_jac_trace(self, trace: dict) -> None:
        trace = {
            "id": f"trace-{len(self.world.jac_traces) + 1}",
            "tick": self.world.tick,
            "walker": trace.get("walker", "decide_strategy"),
            "civilization": trace.get("civilization", trace.get("civ_id", "unknown")),
            "inputs": trace.get("inputs", {}),
            "decision": trace.get("decision", str(trace.get("action", "adapt")).upper()),
            "reason": trace.get("reason", "Jac returned a decision."),
        }
        self.world.jac_traces.append(trace)
        self.world.jac_traces = self.world.jac_traces[-40:]

    def _trace_context(self, inputs: dict) -> str:
        return "; ".join(f"{key}={value}" for key, value in inputs.items())

    def _nearby_enemy_for(self, civ: Civilization) -> Civilization | None:
        for order in reversed(self.world.orders):
            if order.get("status") != "active" or order.get("type") != "war":
                continue
            if order.get("source_civ_id") == civ.id:
                return next((item for item in self.world.civilizations if item.id == order.get("target_civ_id") and item.status == "alive"), None)
            if order.get("target_civ_id") == civ.id:
                return next((item for item in self.world.civilizations if item.id == order.get("source_civ_id") and item.status == "alive"), None)
        return None

    def _choose_attack_target(self, civ: Civilization) -> Civilization | None:
        nearby = self._nearby_enemy_for(civ)
        if nearby:
            return nearby
        candidates = [item for item in self.world.civilizations if item.status == "alive" and item.id != civ.id]
        return min(candidates, key=lambda item: (item.stability, item.population), default=None)

    def _choose_partner(self, civ: Civilization) -> Civilization | None:
        candidates = [item for item in self.world.civilizations if item.status == "alive" and item.id != civ.id]
        if not candidates:
            return None
        preferred = [item for item in candidates if not self._active_order("war", civ.id, item.id) and not self._active_order("war", item.id, civ.id)]
        return max(preferred or candidates, key=lambda item: item.stability + item.technology)

    def _declare_ceasefire(self, a: Civilization | None, b: Civilization | None) -> None:
        ids = {civ.id for civ in (a, b) if civ}
        for order in self.world.orders:
            if order.get("type") != "war" or order.get("status") != "active":
                continue
            order_ids = {order.get("source_civ_id"), order.get("target_civ_id")}
            if not ids or ids.issubset(order_ids) or ids.intersection(order_ids):
                order["status"] = "ended"
                source = next((civ for civ in self.world.civilizations if civ.id == order.get("source_civ_id")), None)
                target = next((civ for civ in self.world.civilizations if civ.id == order.get("target_civ_id")), None)
                if source and target:
                    self._mark_faction_relationship(source.name, target.name, "strained", trust=8, conflict=-26)
                    self._remember_civ(source, "ceasefire", f"{source.name} declared ceasefire with {target.name}.", 7)
                    self._remember_civ(target, "ceasefire", f"{target.name} declared ceasefire with {source.name}.", 7)

    def _migrate_civilization(self, civ: Civilization, direction: str) -> None:
        dx, dy = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0),
        }.get(direction, (0, -1))
        for agent in self.world.agents:
            if agent.faction == civ.name:
                agent.goal = "migrate"
                agent.x = min(self.world.width - 1, max(0, agent.x + dx))
                agent.y = min(self.world.height - 1, max(0, agent.y + dy))
        civ.stability = min(100, civ.stability + 1)
        self._remember_civ(civ, "migration", f"{civ.name} began migrating {direction}.", 6)

    def _coordinates_from_command(self, lowered: str, mentioned: list[Civilization]) -> tuple[int, int]:
        if mentioned:
            return mentioned[0].capital_x, mentioned[0].capital_y
        if "desert" in lowered:
            return self.world.width - 4, max(1, self.world.height // 3)
        if "north" in lowered:
            return self.world.width // 2, 1
        if "south" in lowered:
            return self.world.width // 2, self.world.height - 2
        return self.world.width // 2, self.world.height // 2

    def run_demo_mode(self) -> dict:
        solarians = next(civ for civ in self.world.civilizations if civ.name == "Solarians")
        khepri = next(civ for civ in self.world.civilizations if civ.name == "Khepri")
        varku = next(civ for civ in self.world.civilizations if civ.name == "Varku")
        elyrians = next(civ for civ in self.world.civilizations if civ.name == "Elyrians")
        self._add_news("demo", "Demo mode begins with peaceful civilizations watching the frontier.")
        self._create_alliance(solarians, khepri, "Demo alliance")
        self.trigger_world_event("resource_boom", solarians.capital_x + 1, solarians.capital_y + 1, 3)
        self._create_war_order(varku, elyrians, "Demo war")
        self.trigger_world_event("plague", elyrians.capital_x, elyrians.capital_y, 4)
        self._apply_jac_civilization_decisions(trigger="demo")
        self._add_news("demo", "Jac agent trace updated: judges can inspect why each civilization reacted.")
        return self.snapshot()

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
        jac_strategies = self.jac_engine.decide_event_strategies(
            {"event": event.to_dict(), "civilizations": [civ.to_dict() for civ in self.world.civilizations]}
        )
        for civ in self.world.civilizations:
            if civ.status == "collapsed":
                continue
            killer = self._active_war_killer_for(civ) if event.type == "war" else None
            affected = abs(civ.capital_x - event.x) + abs(civ.capital_y - event.y) <= event.severity + 3
            if event.type == "plague":
                strategy = {
                    "tech-focused": "invent_vaccine",
                    "militaristic": "invade_for_medicine",
                    "diplomatic": "negotiate_aid",
                    "adaptive migrants": "migrate",
                    "religion-driven": "quarantine",
                }.get(civ.trait, "quarantine")
                if affected:
                    self._apply_population_loss(civ, max(15, int(civ.population * 0.06)), "plague")
                civ.stability = max(0, civ.stability - 8)
            elif event.type == "meteor":
                strategy = "migrate" if civ.trait == "adaptive migrants" else "rebuild" if civ.trait != "militaristic" else "secure_crater"
                if affected:
                    self._apply_population_loss(civ, max(20, event.severity * 18), "meteor")
                civ.stability = max(0, civ.stability - 10)
            elif event.type == "war":
                strategy = "invade" if civ.trait == "militaristic" else "negotiate_ceasefire" if civ.trait == "diplomatic" else "fortify"
                if affected:
                    self._apply_population_loss(civ, max(10, event.severity * 12 + self.random.randint(0, 18)), "war", killer if killer and killer.id != civ.id else None)
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
                if event.type == "nuclear_strike" and affected:
                    self._apply_population_loss(civ, max(120, int(civ.population * 0.38)), "nuclear strike")
                elif event.type == "climate_collapse" and affected:
                    self._apply_population_loss(civ, max(12, event.severity * 10), "climate collapse")
            jac_strategy = jac_strategies.get(civ.id)
            if jac_strategy:
                strategy = jac_strategy.get("strategy", strategy)
                self._record_jac_trace(jac_strategy)
            civ.current_strategy = strategy
            source = "Jac" if jac_strategy else "Rules"
            self._remember_civ(civ, event.type, f"{source}: {civ.name} chose {strategy.replace('_', ' ')} after {event.summary}", 8)

    def _apply_ongoing_crisis_losses(self) -> None:
        damaging_effects = [
            effect for effect in self.world.effects if effect["type"] in {"red_fog", "fallout", "fire_spread", "battle_flash", "flood_zone"}
        ]
        if not damaging_effects:
            return
        for effect in damaging_effects:
            for civ in self.world.civilizations:
                if civ.status == "collapsed":
                    continue
                distance = abs(civ.capital_x - effect["x"]) + abs(civ.capital_y - effect["y"])
                if distance <= effect["radius"] + 2:
                    cause = {
                        "red_fog": "plague",
                        "fallout": "fallout",
                        "fire_spread": "fire",
                        "battle_flash": "war",
                        "flood_zone": "flood",
                    }.get(effect["type"], "crisis")
                    loss = max(1, min(18, effect["radius"] * 2 + self.random.randint(0, 4)))
                    killer = self._active_war_killer_for(civ) if cause == "war" else None
                    self._apply_population_loss(civ, loss, cause, killer if killer and killer.id != civ.id else None, remember=False)

    def _war_pair_near(self, x: int, y: int) -> tuple[Civilization | None, Civilization | None]:
        candidates = sorted(
            [civ for civ in self.world.civilizations if civ.status == "alive"],
            key=lambda civ: (abs(civ.capital_x - x) + abs(civ.capital_y - y), civ.id),
        )
        if len(candidates) < 2:
            return None, None
        return candidates[0], candidates[1]

    def _active_war_killer_for(self, target: Civilization) -> Civilization | None:
        for order in reversed(self.world.orders):
            if order.get("type") == "war" and order.get("status") == "active" and order.get("target_civ_id") == target.id:
                return next((civ for civ in self.world.civilizations if civ.id == order.get("source_civ_id") and civ.status == "alive"), None)
        return None

    def _apply_population_loss(self, civ: Civilization, amount: int, cause: str, killer: Civilization | None = None, remember: bool = True) -> int:
        if civ.status == "collapsed" or amount <= 0:
            return 0
        actual = min(civ.population, amount)
        civ.population -= actual
        civ.deaths += actual
        civ.recent_deaths += actual
        self.world.deaths += actual
        self.world.last_casualties += actual
        if killer:
            killer.kills += actual
            self.world.kills += actual
        if remember and actual:
            killer_text = f" by {killer.name}" if killer else ""
            self._remember_civ(civ, cause, f"{civ.name} lost {actual} people to {cause}{killer_text}.", 9)
        for city in self.world.cities:
            if city["civ_id"] == civ.id:
                city["population"] = max(0, min(city["population"], civ.population // 4))
        if civ.population <= 0:
            self._collapse_civilization(civ, cause)
        return actual

    def _collapse_civilization(self, civ: Civilization, cause: str) -> None:
        civ.population = 0
        civ.stability = 0
        civ.status = "collapsed"
        civ.current_strategy = "collapse"
        self._remember_civ(civ, "collapse", f"{civ.name} collapsed after {cause}.", 10)
        self.world.agents = [agent for agent in self.world.agents if agent.faction != civ.name]
        live_ids = {agent.id for agent in self.world.agents}
        self.world.relationships = [rel for rel in self.world.relationships if rel.agent_a in live_ids and rel.agent_b in live_ids]
        self.world.cities = [city for city in self.world.cities if city["civ_id"] != civ.id]
        self._add_news("collapse", f"{civ.name} has fallen. Its cities go silent and its people disappear from the map.")

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

    def _log_rules(self, agent: Agent, summary: str, action: str, source: str = "rules") -> None:
        self.world.reasoning_logs.append(
            ReasoningLog(
                id=f"reason-{len(self.world.reasoning_logs) + 1}",
                agent_id=agent.id,
                source=source,
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
            "orders": [order.copy() for order in self.world.orders[-20:] if order.get("status") == "active"],
            "news": [item.copy() for item in self.world.news[-20:]],
            "events": [event.to_dict() for event in self.world.events[-20:]],
            "reasoning_logs": [log.to_dict() for log in self.world.reasoning_logs[-30:]],
            "jac_traces": [trace.copy() for trace in self.world.jac_traces[-30:]],
            "jac_runtime": self.jac_engine.status(),
            "metrics": {
                "deaths": self.world.deaths,
                "kills": self.world.kills,
                "last_casualties": self.world.last_casualties,
                "alive_civilizations": len([civ for civ in self.world.civilizations if civ.status == "alive"]),
                "collapsed_civilizations": len([civ for civ in self.world.civilizations if civ.status == "collapsed"]),
            },
        }
