from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable


class StrategicReasoner:
    def __init__(
        self,
        model: str = "qwen2.5:3b",
        endpoint: str = "http://localhost:11434/api/generate",
        client: Callable[[dict], dict] | None = None,
    ):
        self.model = model
        self.endpoint = endpoint
        self.client = client or self._ollama_client

    def reason(self, agent_name: str, context: str, desired_action: str) -> dict[str, str]:
        prompt = (
            "You are a compact diplomacy engine for a local civilization simulation. "
            f"Agent: {agent_name}. Context: {context}. "
            f"Recommend a short action for: {desired_action}. Keep under 45 words."
        )
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        try:
            data = self.client(payload)
            text = str(data.get("response", "")).strip()
            if not text:
                raise RuntimeError("empty ollama response")
            return {"source": "ollama", "summary": text, "action": desired_action}
        except Exception:
            return {
                "source": "fallback",
                "summary": (
                    f"{agent_name} uses local rules to pursue '{desired_action}' "
                    "while preserving trust and survival after recent events."
                ),
                "action": desired_action,
            }

    def _ollama_client(self, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=2.5) as response:
            return json.loads(response.read().decode("utf-8"))

