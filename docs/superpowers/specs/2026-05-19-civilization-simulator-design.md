# Jac Agent Civilization Simulator Design

## Goal

Build a local-first hackathon MVP that simulates 10 autonomous civilization agents with visible movement, resources, memories, social relationships, disasters, and selective high-level reasoning through Ollama when available.

## Architecture

The backend is a Python FastAPI service with a plain-Python simulation core. The simulation core owns world state, ticks, agent decisions, memory, relationships, disaster effects, and reasoning logs. FastAPI exposes controls and state snapshots for the frontend.

The frontend is a React + Vite dashboard. It renders the product itself as the first screen: a world grid, controls, selected-agent inspector, alliance graph, reasoning log, and event timeline. It can run against the backend API, with typed client helpers isolated from presentation components.

## MVP Behavior

- Initialize a configurable grid world with 10 agents and food resources.
- Run deterministic ticks that update hunger, health, location, goals, inventory, memories, and relationships.
- Choose most actions with rule scoring: find food, flee danger, trade, support ally, negotiate, or rest.
- Trigger a disaster that depletes resources in an area and causes agents to migrate or change goals.
- Call Ollama only for selected diplomacy or strategy events. If Ollama is unavailable, generate a local rule-based fallback summary.
- Show whether each visible reasoning item came from rules, fallback, or Ollama.

## Data Boundaries

- `backend/app/models.py`: dataclasses and constants shared by the simulation and API.
- `backend/app/simulation.py`: deterministic world engine with no FastAPI dependency.
- `backend/app/llm.py`: Ollama wrapper and fallback reasoning.
- `backend/app/main.py`: API routes and in-memory runtime.
- `frontend/src/lib/api.js`: API client and demo fallback data.
- `frontend/src/components/*`: focused dashboard components.

## Testing

Backend unit tests cover world initialization, tick updates, disaster impact, memory creation, relationship changes, and LLM fallback. Frontend verification covers build success and browser smoke testing of the running app.

