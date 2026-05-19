from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .simulation import CivilizationSimulation


app = FastAPI(title="Jac Agent Civilization Simulator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
runtime = CivilizationSimulation(agent_count=10, seed=42)


class StartRequest(BaseModel):
    agent_count: int = Field(default=10, ge=2, le=30)
    seed: int | None = None
    width: int = Field(default=12, ge=6, le=30)
    height: int = Field(default=10, ge=6, le=30)


class DisasterRequest(BaseModel):
    type: str = "famine"
    x: int | None = None
    y: int | None = None
    radius: int = Field(default=3, ge=1, le=8)


class WorldEventRequest(BaseModel):
    type: str = Field(default="meteor", min_length=2)
    x: int | None = None
    y: int | None = None
    radius: int = Field(default=3, ge=1, le=8)


class CommandRequest(BaseModel):
    text: str = Field(min_length=2, max_length=240)


@app.get("/")
def root() -> dict:
    return {"name": "Jac Agent Civilization Simulator", "status": "ready"}


@app.post("/simulation/start")
def start_simulation(request: StartRequest) -> dict:
    global runtime
    runtime = CivilizationSimulation(
        agent_count=request.agent_count,
        seed=request.seed,
        width=request.width,
        height=request.height,
    )
    return runtime.snapshot()


@app.post("/simulation/pause")
def pause_simulation() -> dict:
    return runtime.pause()


@app.post("/simulation/resume")
def resume_simulation() -> dict:
    return runtime.resume()


@app.post("/simulation/tick")
def tick_simulation() -> dict:
    return runtime.tick()


@app.get("/simulation/state")
def simulation_state() -> dict:
    return runtime.snapshot()


@app.get("/agents/{agent_id}")
def agent_detail(agent_id: str) -> dict:
    detail = runtime.agent_detail(agent_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return detail


@app.post("/events/trigger")
def trigger_event(request: DisasterRequest) -> dict:
    return runtime.trigger_disaster(request.type, request.x, request.y, request.radius).to_dict()


@app.post("/events/god")
def trigger_god_event(request: WorldEventRequest) -> dict:
    return runtime.trigger_world_event(request.type, request.x, request.y, request.radius).to_dict()


@app.post("/commands")
def issue_command(request: CommandRequest) -> dict:
    return runtime.apply_command(request.text)


@app.post("/demo/run")
def run_demo_mode() -> dict:
    return runtime.run_demo_mode()


@app.get("/reasoning/logs")
def reasoning_logs() -> list[dict]:
    return runtime.snapshot()["reasoning_logs"]
