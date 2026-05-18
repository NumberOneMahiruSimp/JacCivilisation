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
    assert any("plague" in memory["description"].lower() for civ in snapshot["civilizations"] for memory in civ["memories"])


def test_meteor_event_shakes_world_and_creates_refugee_movement():
    sim = CivilizationSimulation(agent_count=10, seed=31)

    sim.trigger_world_event("meteor", x=6, y=5, radius=3)
    snapshot = sim.tick()

    assert any(effect["type"] == "meteor_crater" for effect in snapshot["effects"])
    assert any(effect["type"] == "screen_shake" for effect in snapshot["effects"])
    assert any(agent["goal"] in {"migrate", "avoid_disaster", "invent"} for agent in snapshot["agents"])


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
