import { Anchor, Biohazard, Castle, Flame, Gem, Skull, Sparkles, Trees, Waves, Wheat } from "lucide-react";

const factionGlyphs = {
  Solarians: "☼",
  Varku: "⚔",
  Elyrians: "♕",
  Nomads: "◇",
  Khepri: "☥",
};

export function WorldMap({ state, selectedCivId, onSelectCiv }) {
  const civById = new Map((state.civilizations ?? []).map((civ) => [civ.id, civ]));
  const terrainByKey = new Map((state.terrain ?? []).map((tile) => [`${tile.x}-${tile.y}`, tile]));
  const cityByKey = new Map((state.cities ?? []).map((city) => [`${city.x}-${city.y}`, city]));
  const resourcesByKey = groupByPosition(state.resources ?? []);
  const agentsByKey = groupByPosition(state.agents ?? []);

  const cells = [];
  for (let y = 0; y < state.height; y += 1) {
    for (let x = 0; x < state.width; x += 1) {
      const key = `${x}-${y}`;
      const tile = terrainByKey.get(key) ?? { type: "plains", heat: 0, plague: 0, flood: 0, prosperity: 0 };
      const city = cityByKey.get(key);
      const cityCiv = city ? civById.get(city.civ_id) : null;
      const agents = agentsByKey.get(key) ?? [];
      const resources = resourcesByKey.get(key) ?? [];
      const effects = (state.effects ?? []).filter((effect) => Math.abs(effect.x - x) + Math.abs(effect.y - y) <= effect.radius);

      cells.push(
        <button
          className={`pixel-cell ${tile.type} ${tile.heat ? "heated" : ""} ${tile.plague ? "plagued" : ""} ${tile.flood ? "flooded" : ""} ${tile.prosperity ? "booming" : ""}`}
          key={key}
          onClick={() => cityCiv && onSelectCiv(cityCiv.id)}
          style={{ "--civ": cityCiv?.color ?? "#f0c15b" }}
          title={city ? `${city.name}: ${city.status}` : tile.type}
        >
          <TerrainIcon tile={tile} />
          {effects.map((effect) => <span className={`pixel-effect ${effect.type}`} key={effect.id} />)}
          {city && (
            <span className={`settlement ${city.status} ${selectedCivId === city.civ_id ? "selected" : ""}`}>
              <Castle size={18} />
              <b>{factionGlyphs[cityCiv?.name] ?? "◆"}</b>
            </span>
          )}
          <span className="resource-row">
            {resources.slice(0, 2).map((resource) => (
              <i className={resource.type} key={resource.id}>
                {resource.type === "food" ? <Wheat size={11} /> : <Gem size={11} />}
              </i>
            ))}
          </span>
          <span className="marching-units">
            {agents.slice(0, 3).map((agent, index) => {
              const civ = (state.civilizations ?? []).find((item) => item.name === agent.faction);
              return <i key={agent.id} style={{ "--civ": civ?.color ?? "#fff", "--delay": `${index * 180}ms` }} />;
            })}
          </span>
          {tile.plague > 0 && <Biohazard className="crisis-mark plague-mark" size={14} />}
          {tile.heat > 0 && <Flame className="crisis-mark fire-mark" size={14} />}
          {tile.flood > 0 && <Waves className="crisis-mark flood-mark" size={14} />}
        </button>
      );
    }
  }

  return (
    <section className="living-map-panel">
      <div className="parallax-sky">
        <span />
        <span />
        <span />
      </div>
      <div className="rain-layer" />
      <svg className="route-layer" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <path d="M12 24 C 25 15, 40 45, 52 52 S 78 66, 88 25" />
        <path d="M16 82 C 36 58, 48 76, 68 58 S 84 48, 91 80" />
        <path className="hostile" d="M82 24 C 70 32, 67 46, 52 52" />
      </svg>
      <div className="pixel-world-grid" style={{ "--cols": state.width }}>
        {cells}
      </div>
      <div className="world-ambience">
        <span className="torch torch-a" />
        <span className="torch torch-b" />
        <span className="boat boat-a"><Anchor size={14} /></span>
        <span className="boat boat-b"><Anchor size={14} /></span>
        <span className="ruin-shadow"><Skull size={18} /></span>
        <span className="magic-glow"><Sparkles size={18} /></span>
      </div>
      <div className="map-legend">
        <span><Castle size={13} /> Cities</span>
        <span><Trees size={13} /> Living terrain</span>
        <span><Waves size={13} /> Rivers</span>
        <span><Flame size={13} /> Crisis effects</span>
      </div>
    </section>
  );
}

function TerrainIcon({ tile }) {
  if (tile.type === "water") return <Waves className="terrain-icon water-icon" size={16} />;
  if (tile.type === "forest") return <Trees className="terrain-icon forest-icon" size={17} />;
  if (tile.type === "mountain") return <span className="mountain-icon">▲</span>;
  if (tile.type === "desert") return <span className="desert-icon">•</span>;
  return <span className="grass-pixels" />;
}

function groupByPosition(items) {
  const map = new Map();
  for (const item of items) {
    const key = `${item.x}-${item.y}`;
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(item);
  }
  return map;
}
