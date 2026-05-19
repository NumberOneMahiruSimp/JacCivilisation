from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


class JacDecisionEngine:
    """Small bridge that lets the Python API delegate intent decisions to Jac."""

    def __init__(self, jac_file: Path | None = None, timeout: float = 15.0):
        self.jac_file = jac_file or Path(__file__).resolve().parents[1] / "simulation.jac"
        self.timeout = timeout
        self.available = self.jac_file.exists()
        self.last_error: str | None = None

    def decide_agents(self, payload: dict[str, Any]) -> dict[str, dict[str, str]]:
        result = self._run({**payload, "mode": "agents"})
        return {
            item["agent_id"]: item
            for item in result.get("decisions", [])
            if isinstance(item, dict) and item.get("agent_id")
        }

    def decide_event_strategies(self, payload: dict[str, Any]) -> dict[str, dict[str, str]]:
        result = self._run({**payload, "mode": "event"})
        return {
            item["civ_id"]: item
            for item in result.get("strategies", [])
            if isinstance(item, dict) and item.get("civ_id")
        }

    def decide_civilizations(self, payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        result = self._run({**payload, "mode": "civilizations"})
        return {
            item["civ_id"]: item
            for item in result.get("decisions", [])
            if isinstance(item, dict) and item.get("civ_id")
        }

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.available,
            "file": str(self.jac_file),
            "last_error": self.last_error,
        }

    def _run(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.available:
            return {"source": "python", "error": "simulation.jac not found"}

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump(payload, handle)
            input_path = Path(handle.name)

        try:
            completed = subprocess.run(
                [sys.executable, "-m", "jaclang", "run", str(self.jac_file), str(input_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            self.last_error = None
            lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
            return json.loads(lines[-1]) if lines else {"source": "jac", "error": "empty Jac output"}
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as exc:
            self.last_error = str(exc)
            return {"source": "python", "error": self.last_error}
        finally:
            input_path.unlink(missing_ok=True)
