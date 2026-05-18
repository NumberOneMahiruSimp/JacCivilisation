from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_start_and_state_endpoints_return_world_snapshot():
    started = client.post("/simulation/start", json={"agent_count": 10, "seed": 5})
    assert started.status_code == 200

    state = client.get("/simulation/state")
    assert state.status_code == 200
    payload = state.json()
    assert payload["tick"] == 0
    assert len(payload["agents"]) == 10


def test_tick_and_agent_detail_endpoint():
    client.post("/simulation/start", json={"agent_count": 3, "seed": 9})
    ticked = client.post("/simulation/tick")
    assert ticked.status_code == 200

    agent_id = ticked.json()["agents"][0]["id"]
    detail = client.get(f"/agents/{agent_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == agent_id
    assert "memories" in detail.json()


def test_trigger_disaster_and_reasoning_logs():
    client.post("/simulation/start", json={"agent_count": 5, "seed": 2})
    disaster = client.post("/events/trigger", json={"type": "famine", "x": 4, "y": 4, "radius": 3})
    assert disaster.status_code == 200
    assert disaster.json()["type"] == "famine"

    logs = client.get("/reasoning/logs")
    assert logs.status_code == 200
    assert isinstance(logs.json(), list)


def test_trigger_god_event_returns_live_cinematic_state():
    client.post("/simulation/start", json={"agent_count": 10, "seed": 14})
    event = client.post("/events/god", json={"type": "meteor", "x": 6, "y": 5, "radius": 3})
    assert event.status_code == 200
    assert event.json()["type"] == "meteor"

    state = client.get("/simulation/state").json()
    assert any(effect["type"] == "meteor_crater" for effect in state["effects"])
    assert any("Meteor" in item["headline"] for item in state["news"])
