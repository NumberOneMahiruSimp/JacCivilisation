const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8001";

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API ${path} failed with ${response.status}`);
  }
  return response.json();
}

const civs = [
  ["civ-solarians", "Solarians", "tech-focused", "Progress through invention", "#f5b642", 1, 1],
  ["civ-varku", "Varku", "militaristic", "Security through conquest", "#d55344", 11, 2],
  ["civ-elyrians", "Elyrians", "diplomatic", "Survival through treaties", "#55b68b", 6, 5],
  ["civ-nomads", "Nomads", "adaptive migrants", "Movement is life", "#4e9fd9", 2, 8],
  ["civ-khepri", "Khepri", "religion-driven", "Meaning before empire", "#9b72d9", 10, 8],
];

export function createDemoState() {
  const civilizations = civs.map(([id, name, trait, doctrine, color, capital_x, capital_y], index) => ({
    id,
    name,
    trait,
    doctrine,
    color,
    capital_x,
    capital_y,
    population: 900 + index * 120,
    stability: 72 - index * 3,
    technology: 42 + index * 8,
    faith: 36 + index * 9,
    kills: 0,
    deaths: 0,
    recent_deaths: 0,
    status: "alive",
    alive: true,
    current_strategy: "expand",
    memories: [],
  }));

  const agents = civilizations.flatMap((civ, index) => [
    makeAgent(index * 2 + 1, civ, civ.capital_x, civ.capital_y, "migrate"),
    makeAgent(index * 2 + 2, civ, Math.max(0, civ.capital_x - 1), Math.min(9, civ.capital_y + 1), "invent"),
  ]);

  return {
    width: 13,
    height: 10,
    tick: 0,
    paused: false,
    civilizations,
    agents,
    terrain: Array.from({ length: 130 }, (_, index) => {
      const x = index % 13;
      const y = Math.floor(index / 13);
      const type = (x + y) % 7 === 0 ? "water" : (x * y) % 11 === 0 ? "mountain" : (x + y) % 3 === 0 ? "forest" : "plains";
      return { x, y, type, heat: 0, plague: 0, flood: 0, prosperity: 0 };
    }),
    cities: civilizations.map((civ) => ({
      id: `city-${civ.id}`,
      name: `${civ.name} Prime`,
      civ_id: civ.id,
      x: civ.capital_x,
      y: civ.capital_y,
      population: Math.round(civ.population / 4),
      status: "stable",
    })),
    resources: Array.from({ length: 34 }, (_, index) => ({
      id: `res-${index}`,
      type: index % 4 === 0 ? "ore" : "food",
      x: (index * 3 + 2) % 13,
      y: (index * 5 + 1) % 10,
      amount: (index % 4) + 1,
    })),
    effects: [],
    relationships: [],
    events: [],
    news: [],
    reasoning_logs: [],
    jac_traces: [],
    jac_runtime: { enabled: false, file: "demo", last_error: null },
    metrics: { deaths: 0, kills: 0, last_casualties: 0, alive_civilizations: 5, collapsed_civilizations: 0 },
  };
}

function makeAgent(num, civ, x, y, goal) {
  return {
    id: `agent-${num}`,
    name: `${civ.name.slice(0, 4)} Envoy ${num}`,
    x,
    y,
    health: 82,
    hunger: 40 + num * 3,
    strength: 55 + num,
    personality: civ.trait,
    faction: civ.name,
    goal,
    inventory: { food: 1, ore: 0 },
    memories: [],
    last_reasoning: `${civ.name} follows ${civ.doctrine.toLowerCase()}.`,
  };
}
