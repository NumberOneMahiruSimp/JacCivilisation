from app.llm import StrategicReasoner
from app.simulation import CivilizationSimulation


def test_world_initializes_with_agents_resources_and_relationships():
    sim = CivilizationSimulation(agent_count=10, seed=7)

    snapshot = sim.snapshot()

    assert len(snapshot["agents"]) == 10
    assert len(snapshot["civilizations"]) == 5
    assert {civ["trait"] for civ in snapshot["civilizations"]} >= {"tech-focused", "militaristic", "diplomatic"}
    assert len(snapshot["resources"]) >= 25
    assert snapshot["tick"] == 0
    assert any(rel["alliance_status"] == "neutral" for rel in snapshot["relationships"])


def test_tick_makes_hungry_agents_seek_and_collect_food():
    sim = CivilizationSimulation(agent_count=2, seed=3)
    agent = sim.world.agents[0]
    agent.hunger = 92
    agent.x = 1
    agent.y = 1
    sim.world.resources = [{"id": "food-test", "type": "food", "x": 2, "y": 1, "amount": 4}]

    sim.tick()

    assert agent.goal in {"find_food", "trade"}
    assert agent.inventory["food"] >= 1
    assert agent.hunger < 92
    assert any("found food" in memory.description for memory in agent.memories)
    assert any(log.source == "jac" for log in sim.world.reasoning_logs)


def test_disaster_depletes_food_and_changes_agent_goals():
    sim = CivilizationSimulation(agent_count=4, seed=11)
    before = len(sim.world.resources)

    event = sim.trigger_disaster("famine", x=4, y=4, radius=3)
    sim.tick()

    after = len(sim.world.resources)
    assert event.type == "famine"
    assert after < before
    assert any(agent.goal in {"avoid_disaster", "find_food"} for agent in sim.world.agents)
    assert any(item.type == "famine" for item in sim.world.events)


def test_god_event_creates_cinematic_effects_news_and_trait_reactions():
    sim = CivilizationSimulation(agent_count=10, seed=23)

    event = sim.trigger_world_event("plague", x=5, y=4, radius=4)
    snapshot = sim.snapshot()

    assert event.type == "plague"
    assert any(effect["type"] == "red_fog" for effect in snapshot["effects"])
    assert any("plague" in item["headline"].lower() for item in snapshot["news"])
    assert any(civ["current_strategy"] in {"quarantine", "invade_for_medicine", "negotiate_aid"} for civ in snapshot["civilizations"])
    assert any("jac:" in memory["description"].lower() and "plague" in memory["description"].lower() for civ in snapshot["civilizations"] for memory in civ["memories"])


def test_snapshot_reports_active_jac_runtime():
    sim = CivilizationSimulation(agent_count=2, seed=41)
    snapshot = sim.tick()

    assert snapshot["jac_runtime"]["enabled"] is True
    assert snapshot["jac_runtime"]["file"].endswith("simulation.jac")


def test_meteor_event_shakes_world_and_creates_refugee_movement():
    sim = CivilizationSimulation(agent_count=10, seed=31)

    sim.trigger_world_event("meteor", x=6, y=5, radius=3)
    snapshot = sim.tick()

    assert any(effect["type"] == "meteor_crater" for effect in snapshot["effects"])
    assert any(effect["type"] == "screen_shake" for effect in snapshot["effects"])
    assert any(agent["goal"] in {"migrate", "avoid_disaster", "invent"} for agent in snapshot["agents"])


def test_war_and_plague_update_live_casualty_metrics_and_collapse_removes_agents():
    sim = CivilizationSimulation(agent_count=10, seed=51)
    target = sim.world.civilizations[0]
    target.population = 18

    sim.trigger_world_event("war", x=target.capital_x, y=target.capital_y, radius=5)
    snapshot = sim.snapshot()

    fallen = next(civ for civ in snapshot["civilizations"] if civ["id"] == target.id)
    assert fallen["status"] == "collapsed"
    assert fallen["deaths"] > 0
    assert snapshot["metrics"]["deaths"] > 0
    assert snapshot["metrics"]["kills"] > 0
    assert all(agent["faction"] != target.name for agent in snapshot["agents"])
    assert all(city["civ_id"] != target.id for city in snapshot["cities"])


def test_nuclear_strike_counts_deaths_without_crediting_combat_kills():
    sim = CivilizationSimulation(agent_count=10, seed=54)

    sim.trigger_world_event("nuclear_strike", x=6, y=5, radius=5)
    snapshot = sim.snapshot()

    assert snapshot["metrics"]["deaths"] > 0
    assert snapshot["metrics"]["kills"] == 0
    assert all(civ["kills"] == 0 for civ in snapshot["civilizations"])


def test_god_war_credits_nearest_attacker_not_default_varku():
    sim = CivilizationSimulation(agent_count=10, seed=55)
    solarians = next(civ for civ in sim.world.civilizations if civ.name == "Solarians")
    varku = next(civ for civ in sim.world.civilizations if civ.name == "Varku")

    sim.trigger_world_event("war", x=solarians.capital_x, y=solarians.capital_y, radius=3)
    snapshot = sim.snapshot()
    order = next(order for order in snapshot["orders"] if order["type"] == "war")

    assert order["source"] == "Solarians"
    assert varku.kills == 0
    assert solarians.kills > 0


def test_commanded_war_order_advances_attackers_toward_target():
    sim = CivilizationSimulation(agent_count=10, seed=61)
    result = sim.apply_command("Varku attack Elyrians")
    before = next(agent for agent in sim.world.agents if agent.faction == "Varku")
    distance_before = abs(before.x - sim.world.civilizations[2].capital_x) + abs(before.y - sim.world.civilizations[2].capital_y)

    sim.tick()
    after = next(agent for agent in sim.world.agents if agent.id == before.id)
    distance_after = abs(after.x - sim.world.civilizations[2].capital_x) + abs(after.y - sim.world.civilizations[2].capital_y)

    assert result["type"] == "war_order"
    assert result["message"] == "Command understood -> Jac walker triggered -> World updated"
    assert sim.world.orders[0]["progress"] > 0
    assert distance_after <= distance_before
    assert any(trace["walker"] == "decide_strategy" for trace in sim.snapshot()["jac_traces"])


def test_natural_commands_update_trade_migration_tech_and_casualties():
    sim = CivilizationSimulation(agent_count=10, seed=71)
    trade = sim.apply_command("Solarians trade with Khepri")
    migrate = sim.apply_command("make Khepri migrate north")
    before_tech = next(civ for civ in sim.world.civilizations if civ.name == "Solarians").technology
    tech = sim.apply_command("give Solarians tech boost")
    attacker = next(civ for civ in sim.world.civilizations if civ.name == "Nomads")
    target = next(civ for civ in sim.world.civilizations if civ.name == "Khepri")
    sim.apply_command("Nomads attack Khepri")
    order = next(order for order in sim.world.orders if order.get("type") == "war" and order.get("source") == "Nomads")
    order["progress"] = 65
    sim.tick()

    assert trade["type"] == "trade"
    assert migrate["type"] == "migration"
    assert tech["type"] == "tech_boost"
    assert next(civ for civ in sim.world.civilizations if civ.name == "Solarians").technology > before_tech
    assert attacker.kills > 0
    assert target.deaths > 0


def test_relationships_can_strengthen_after_support_or_trade():
    sim = CivilizationSimulation(agent_count=2, seed=19)
    a, b = sim.world.agents[:2]
    a.x = b.x = 5
    a.y = b.y = 5
    a.inventory["food"] = 3
    b.hunger = 96

    sim.tick()

    rel = sim.relationship_between(a.id, b.id)
    assert rel.trust_score > 50
    assert rel.alliance_status in {"neutral", "allied"}


def test_reasoner_falls_back_when_ollama_client_fails():
    def failing_client(_payload):
        raise RuntimeError("ollama offline")

    reasoner = StrategicReasoner(client=failing_client)
    result = reasoner.reason(
        agent_name="Mira",
        context="Mira is hungry near an ally after a famine.",
        desired_action="negotiate food support",
    )

    assert result["source"] == "fallback"
    assert "Mira" in result["summary"]
    assert "negotiate food support" in result["action"]
