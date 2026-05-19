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
    kills: index === 1 ? 34 : 0,
    deaths: index * 7,
    recent_deaths: index === 2 ? 4 : 0,
    status: "alive",
    alive: true,
    current_strategy: ["invent_vaccine", "invade_for_medicine", "negotiate_aid", "migrate", "quarantine"][index],
    memories: [
      {
        id: `${id}-memory-1`,
        type: index === 1 ? "war" : "alliance",
        description: `${name} still remembers the Water War and its broken promises.`,
        importance: 8,
        timestamp: 31,
      },
    ],
  }));

  const agents = civilizations.flatMap((civ, index) => [
    makeAgent(index * 2 + 1, civ, civ.capital_x, civ.capital_y, "migrate"),
    makeAgent(index * 2 + 2, civ, Math.max(0, civ.capital_x - 1), Math.min(9, civ.capital_y + 1), "invent"),
  ]);

  return {
    width: 13,
    height: 10,
    tick: 88,
    paused: false,
    civilizations,
    agents,
    terrain: Array.from({ length: 130 }, (_, index) => {
      const x = index % 13;
      const y = Math.floor(index / 13);
      const type = (x + y) % 7 === 0 ? "water" : (x * y) % 11 === 0 ? "mountain" : (x + y) % 3 === 0 ? "forest" : "plains";
      return { x, y, type, heat: near(x, y, 6, 5) ? 2 : 0, plague: near(x, y, 5, 4) ? 3 : 0, flood: y > 7 ? 1 : 0, prosperity: near(x, y, 3, 3) ? 2 : 0 };
    }),
    cities: civilizations.map((civ) => ({
      id: `city-${civ.id}`,
      name: `${civ.name} Prime`,
      civ_id: civ.id,
      x: civ.capital_x,
      y: civ.capital_y,
      population: Math.round(civ.population / 4),
      status: civ.id === "civ-varku" ? "besieged" : civ.id === "civ-elyrians" ? "quarantined" : "stable",
    })),
    resources: Array.from({ length: 34 }, (_, index) => ({
      id: `res-${index}`,
      type: index % 4 === 0 ? "ore" : "food",
      x: (index * 3 + 2) % 13,
      y: (index * 5 + 1) % 10,
      amount: (index % 4) + 1,
    })),
    effects: [
      { id: "effect-1", type: "red_fog", x: 5, y: 4, radius: 4, ttl: 8 },
      { id: "effect-2", type: "meteor_crater", x: 6, y: 5, radius: 3, ttl: 8 },
      { id: "effect-3", type: "trade_route", x: 3, y: 3, radius: 3, ttl: 8 },
    ],
    relationships: [
      { agent_a: "agent-1", agent_b: "agent-5", trust_score: 78, alliance_status: "allied", conflict_score: 2, last_interaction: "Fusion exchange treaty." },
      { agent_a: "agent-3", agent_b: "agent-5", trust_score: 22, alliance_status: "enemy", conflict_score: 82, last_interaction: "Betrayal during the Water War." },
      { agent_a: "agent-7", agent_b: "agent-9", trust_score: 71, alliance_status: "allied", conflict_score: 5, last_interaction: "Refugee corridor opened." },
    ],
    events: [
      { id: "event-1", type: "plague", x: 5, y: 4, severity: 4, affected_agents: ["agent-5"], created_tick: 84, summary: "A deadly plague spreads globally." },
      { id: "event-2", type: "meteor", x: 6, y: 5, severity: 3, affected_agents: ["agent-6"], created_tick: 86, summary: "Meteor impact sends refugees south." },
    ],
    news: [
      { id: "news-1", tick: 86, headline: "Meteor impact sends refugees across the southern roads", body: "Nomad scouts report burning cities near the impact crater." },
      { id: "news-2", tick: 84, headline: "Global plague alert: quarantine borders rise overnight", body: "The Elyrians ask rivals for medicine while Varku prepares a raid." },
      { id: "news-3", tick: 82, headline: "Solarians discover early fusion lattice", body: "Technology markets surge while faith councils debate the omen." },
    ],
    reasoning_logs: [
      {
        id: "reason-1",
        agent_id: "agent-3",
        source: "fallback",
        prompt_context: "Food shortage, weak Elyrian borders, Varku troops mobilized.",
        output_summary: "Due to a 3-year food shortage and weakening borders, the Varku initiated expansion into Elyrian territory.",
        action_taken: "invade_for_medicine",
        created_tick: 87,
      },
      {
        id: "reason-2",
        agent_id: "agent-5",
        source: "rules",
        prompt_context: "Plague event and diplomatic trait.",
        output_summary: "The Elyrians negotiated aid because their diplomatic doctrine values survival through treaties.",
        action_taken: "negotiate_aid",
        created_tick: 85,
      },
    ],
    jac_traces: [
      {
        id: "trace-demo-1",
        tick: 88,
        walker: "decide_strategy",
        civilization: "Varku",
        inputs: { population: 1020, stability: 69, deaths: 7, nearby_enemy: "Elyrians", threat_level: 72 },
        decision: "ATTACK",
        reason: "Varku chose ATTACK because enemy stability is weak and military aggression is high.",
      },
    ],
    jac_runtime: { enabled: false, file: "demo", last_error: null },
    metrics: { deaths: 70, kills: 34, last_casualties: 4, alive_civilizations: 5, collapsed_civilizations: 0 },
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

function near(x, y, cx, cy) {
  return Math.abs(x - cx) + Math.abs(y - cy) <= 3;
}
