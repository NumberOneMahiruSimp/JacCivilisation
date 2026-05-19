import { Anchor, Biohazard, Castle, Cloud, Flame, Skull, Sparkles, Waves } from "lucide-react";

const factionGlyphs = {
  Solarians: "S",
  Varku: "V",
  Elyrians: "E",
  Nomads: "N",
  Khepri: "K",
};

const factionPortraits = {
  Solarians: "/assets/players/region-gold.png",
  Elyrians: "/assets/players/region-gold.png",
  Khepri: "/assets/players/1779180757429.png",
  Varku: "/assets/players/region-iron.png",
  Nomads: "/assets/players/1779180774520.png",
};

const cityAnchors = {
  Solara: [34, 25],
  "Varku Hold": [32, 66],
  Elyria: [67, 65],
  "Nomad Wells": [70, 35],
  "Khepri Temple": [82, 41],
};

const fallbackAnchors = [
  [34, 25],
  [32, 66],
  [67, 65],
  [70, 35],
  [82, 41],
];

export function WorldMap({ state, selectedCivId, onSelectCiv }) {
  const livingCivs = (state.civilizations ?? []).filter((civ) => civ.status !== "collapsed" && civ.population > 0);
  const civById = new Map(livingCivs.map((civ) => [civ.id, civ]));
  const livingFactionNames = new Set(livingCivs.map((civ) => civ.name));
  const cities = (state.cities ?? []).filter((city) => civById.has(city.civ_id));
  const agents = (state.agents ?? []).filter((agent) => livingFactionNames.has(agent.faction));
  const effects = state.effects ?? [];
  const orders = state.orders ?? [];
  const width = state.width || 13;
  const height = state.height || 10;

  const placedCities = cities.map((city, index) => {
    const civ = civById.get(city.civ_id);
    const known = cityAnchors[city.name];
    const generated = [
      ((city.x + 0.5) / width) * 76 + 12,
      ((city.y + 0.5) / height) * 68 + 14,
    ];
    const [left, top] = known ?? fallbackAnchors[index % fallbackAnchors.length] ?? generated;
    return { city, civ, left, top };
  });

  const placedAgents = agents.slice(0, 14).map((agent, index) => {
    const civ = livingCivs.find((item) => item.name === agent.faction);
    const nearest = placedCities.find((item) => item.civ?.name === agent.faction);
    const left = (nearest?.left ?? 20) + ((index % 3) - 1) * 4 + Math.sin(index) * 2;
    const top = (nearest?.top ?? 20) + ((index % 2) ? 8 : -7);
    return { id: agent.id, agent, civ, left, top, kind: "agent", mood: movementMood(agent.goal) };
  });

  const crowdAgents = placedCities.flatMap(({ civ, city, left, top }, cityIndex) => {
    const count = Math.max(1, Math.min(3, Math.round((civ?.population ?? city.population ?? 400) / 500)));
    return Array.from({ length: count }, (_, index) => ({
      id: `${city.id}-crowd-${index}`,
      agent: { name: `${civ?.name ?? "Civilian"} citizen`, goal: city.status === "quarantined" ? "quarantine" : city.status === "besieged" ? "defend" : "trade" },
      civ,
      left: left + (index - 1) * 3.4 + cityIndex * 0.4,
      top: top + 9 + (index % 2) * 3,
      kind: "civilian",
      mood: city.status === "quarantined" ? "quarantine" : city.status === "besieged" ? "war" : "trade",
    }));
  });

  const refugeeAgents = effects.slice(-4).flatMap((effect, effectIndex) => (
    Array.from({ length: effect.type.includes("fog") || effect.type.includes("meteor") || effect.type.includes("fallout") ? 2 : 1 }, (_, index) => ({
      id: `${effect.id}-refugee-${index}`,
      agent: { name: "Refugee", goal: "flee crisis" },
      civ: null,
      left: 18 + ((effect.x ?? effectIndex) / width) * 70 + 4 + index * 3,
      top: 16 + ((effect.y ?? effectIndex) / height) * 66 + 7 + index * 2,
      kind: "refugee",
      mood: "migrate",
    }))
  ));

  const livingPeople = [...crowdAgents, ...placedAgents, ...refugeeAgents].slice(0, 24);
  const orderRoutes = orders
    .map((order) => {
      const source = placedCities.find((item) => item.city.civ_id === order.source_civ_id);
      const target = placedCities.find((item) => item.city.civ_id === order.target_civ_id);
      return source && target ? { ...order, source, target } : null;
    })
    .filter(Boolean);
  const diplomacyRoutes = relationshipRoutes(state.relationships ?? [], agents, placedCities);

  return (
    <section className="living-map-panel">
      <div className="map-canvas" aria-label="Animated pixel world map">
        <img className="painted-world-map" src="/assets/reference-world-map.png" alt="Pixel civilization world map" />

        <svg className="route-layer" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          {diplomacyRoutes.map((route) => (
            <path
              className={route.status === "allied" ? "allied" : "hostile"}
              d={curvePath(route.from.left, route.from.top, route.to.left, route.to.top)}
              key={route.id}
            />
          ))}
          {orderRoutes.map((route) => (
            <g className={`order-route ${route.type}`} key={route.id}>
              <path d={curvePath(route.source.left, route.source.top, route.target.left, route.target.top)} />
              <circle cx={route.source.left + ((route.target.left - route.source.left) * (route.progress ?? 0)) / 100} cy={route.source.top + ((route.target.top - route.source.top) * (route.progress ?? 0)) / 100} r="1.4" />
              {route.type === "trade" && (
                <circle className="trade-particle" cx={route.target.left + ((route.source.left - route.target.left) * (route.progress ?? 0)) / 100} cy={route.target.top + ((route.source.top - route.target.top) * (route.progress ?? 0)) / 100} r="1" />
              )}
            </g>
          ))}
        </svg>

        <div className="weather-layer" aria-hidden="true">
          <Cloud className="cloud cloud-a" size={42} />
          <Cloud className="cloud cloud-b" size={34} />
          <Cloud className="cloud cloud-c" size={28} />
          <span className="map-shadow shadow-a" />
          <span className="map-shadow shadow-b" />
        </div>

        {effects.slice(-8).map((effect, index) => (
          <span
            className={`world-effect ${effect.type}`}
            key={effect.id}
            style={{
              left: `${18 + ((effect.x ?? index) / width) * 70}%`,
              top: `${16 + ((effect.y ?? index) / height) * 66}%`,
            }}
          >
            {effect.type.includes("fog") || effect.type.includes("plague") ? <Biohazard size={18} /> : effect.type.includes("flood") ? <Waves size={18} /> : <Flame size={18} />}
            <span className="effect-particles" aria-hidden="true">
              {Array.from({ length: 7 }, (_, particleIndex) => (
                <i key={particleIndex} style={{ "--p": particleIndex }} />
              ))}
            </span>
          </span>
        ))}

        {placedCities.map(({ city, civ, left, top }) => (
          <button
            className={`map-city ${selectedCivId === city.civ_id ? "selected" : ""} ${city.status}`}
            key={city.id}
            onClick={() => civ && onSelectCiv(civ.id)}
            style={{ "--civ": civ?.color ?? "#d9b66a", left: `${left}%`, top: `${top}%` }}
            title={`${city.name}: ${city.status}`}
          >
            <Castle size={17} />
            <span>{factionGlyphs[civ?.name] ?? "C"}</span>
            <strong>{civ?.name ?? city.name}</strong>
          </button>
        ))}

        {livingPeople.map(({ id, agent, civ, left, top, kind, mood }) => (
          <span
            className={`map-unit ${kind} ${mood}`}
            key={id}
            style={{ "--civ": civ?.color ?? "#d9b66a", left: `${left}%`, top: `${top}%`, "--delay": `${(id.length % 5) * 130}ms` }}
            title={`${agent.name}: ${agent.goal?.replaceAll("_", " ")}`}
          >
            <img src={factionPortraits[civ?.name] ?? "/assets/players/region-iron.png"} alt="" />
          </span>
        ))}

        {orderRoutes.filter((route) => route.type === "war").flatMap((route) => [0, 1, 2].map((index) => {
          const progress = Math.min(100, (route.progress ?? 0) + index * 12);
          const left = route.source.left + ((route.target.left - route.source.left) * progress) / 100;
          const top = route.source.top + ((route.target.top - route.source.top) * progress) / 100;
          return (
            <span
              className="map-unit invasion war"
              key={`${route.id}-march-${index}`}
              style={{ "--civ": route.source.civ?.color ?? "#d9b66a", left: `${left}%`, top: `${top}%`, "--delay": `${index * 150}ms` }}
              title={`${route.source.civ?.name} attacking ${route.target.civ?.name}`}
            >
              <img src={factionPortraits[route.source.civ?.name] ?? "/assets/players/region-iron.png"} alt="" />
            </span>
          );
        }))}

        {orderRoutes.filter((route) => route.type === "war").flatMap((route) => [0, 1].map((index) => (
          <span
            className="map-unit defender war"
            key={`${route.id}-defender-${index}`}
            style={{ "--civ": route.target.civ?.color ?? "#d9b66a", left: `${route.target.left + (index ? 4 : -4)}%`, top: `${route.target.top + 7 + index * 2}%`, "--delay": `${index * 180}ms` }}
            title={`${route.target.civ?.name} defending against ${route.source.civ?.name}`}
          >
            <img src={factionPortraits[route.target.civ?.name] ?? "/assets/players/region-iron.png"} alt="" />
          </span>
        )))}

        <div className="world-ambience" aria-hidden="true">
          <span className="torch torch-a" />
          <span className="torch torch-b" />
          <span className="boat boat-a"><Anchor size={15} /></span>
          <span className="boat boat-b"><Anchor size={15} /></span>
          <span className="ruin-shadow"><Skull size={18} /></span>
          <span className="magic-glow"><Sparkles size={18} /></span>
        </div>
      </div>

      <div className="map-legend">
        <span><Castle size={13} /> Settlements</span>
        <span><Anchor size={13} /> Routes</span>
        <span><Flame size={13} /> Events</span>
        <span><Biohazard size={13} /> Crisis memory</span>
      </div>
      <div className="route-key" aria-label="Route arrow meaning">
        <span><i className="key-line war" /> Red arrow: war or invasion</span>
        <span><i className="key-line ally" /> Green line: alliance or trade</span>
        <span><i className="key-line diplomacy" /> Gold dashes: diplomacy tension</span>
        <span><i className="key-dot" /> Moving circle: order progress</span>
        <span><i className="key-ring" /> Pulsing circle: disaster zone</span>
      </div>
    </section>
  );
}

function relationshipRoutes(relationships, agents, placedCities) {
  const routes = new Map();
  for (const rel of relationships) {
    if (!["allied", "enemy", "strained"].includes(rel.alliance_status)) continue;
    const a = agents.find((agent) => agent.id === rel.agent_a);
    const b = agents.find((agent) => agent.id === rel.agent_b);
    if (!a || !b || a.faction === b.faction) continue;
    const from = placedCities.find((city) => city.civ?.name === a.faction);
    const to = placedCities.find((city) => city.civ?.name === b.faction);
    if (!from || !to) continue;
    const id = [a.faction, b.faction].sort().join("-");
    const status = rel.alliance_status === "allied" ? "allied" : "enemy";
    if (!routes.has(id) || status === "enemy") routes.set(id, { id, from, to, status });
  }
  return [...routes.values()].slice(0, 8);
}

function curvePath(x1, y1, x2, y2) {
  const midX = (x1 + x2) / 2;
  const midY = (y1 + y2) / 2 - 10;
  return `M ${x1} ${y1} Q ${midX} ${midY} ${x2} ${y2}`;
}

function movementMood(goal = "") {
  if (goal.includes("migrate") || goal.includes("flee")) return "migrate";
  if (goal.includes("invade") || goal.includes("defend") || goal.includes("war")) return "war";
  if (goal.includes("invent") || goal.includes("research")) return "invent";
  if (goal.includes("quarantine")) return "quarantine";
  return "trade";
}
