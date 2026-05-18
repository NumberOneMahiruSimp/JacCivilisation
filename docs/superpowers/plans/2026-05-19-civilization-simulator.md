# Civilization Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable local-first agent civilization simulator MVP with a FastAPI backend and React dashboard.

**Architecture:** Keep simulation logic in plain Python so it is deterministic and testable. Put FastAPI at the edge for control/state endpoints, and put React components behind a small API client that can show demo state while the backend boots.

**Tech Stack:** Python 3, FastAPI, pytest, React, Vite, CSS modules/plain CSS, Ollama HTTP API fallback.

---

### Task 1: Backend Simulation Core

**Files:**
- Create: `backend/app/models.py`
- Create: `backend/app/simulation.py`
- Create: `backend/app/llm.py`
- Create: `backend/tests/test_simulation.py`

- [x] Write tests for initialization, ticking, disasters, memories, relationships, and fallback reasoning.
- [x] Run tests and confirm they fail because implementation is missing.
- [x] Implement the minimal simulation engine.
- [x] Run tests and confirm they pass.

### Task 2: FastAPI API

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/tests/test_api.py`

- [x] Write API tests for start, state, agent detail, trigger disaster, and reasoning logs.
- [x] Implement API routes backed by an in-memory simulation runtime.
- [x] Run API tests.

### Task 3: React Dashboard

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/components/WorldMap.jsx`
- Create: `frontend/src/components/AgentPanel.jsx`
- Create: `frontend/src/components/AllianceGraph.jsx`
- Create: `frontend/src/components/EventTimeline.jsx`
- Create: `frontend/src/components/ReasoningLog.jsx`
- Create: `frontend/src/components/Controls.jsx`
- Create: `frontend/src/lib/api.js`

- [x] Build the primary dashboard screen from the generated concept.
- [x] Wire controls to backend endpoints.
- [x] Add demo fallback state for UI resilience.
- [x] Run production build.

### Task 4: Project Docs and Verification

**Files:**
- Create: `README.md`
- Create: `.gitignore`

- [x] Document local setup and run commands.
- [x] Verify backend tests.
- [x] Verify frontend build.
- [x] Start dev servers for handoff when possible.

