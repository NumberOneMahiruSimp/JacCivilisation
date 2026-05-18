export function AllianceGraph({ agents, relationships, selectedFaction }) {
  const visible = relationships
    .filter((rel) => rel.alliance_status !== "neutral" || rel.trust_score > 64 || rel.conflict_score > 35)
    .slice(0, 9);

  return (
    <section className="panel graph-panel">
      <div className="panel-header">
        <div>
          <h2>Alliance Graph</h2>
          <p>Trust, strain, and faction clusters</p>
        </div>
      </div>
      <div className="graph-stage">
        {visible.map((rel, index) => (
          <GraphLink key={`${rel.agent_a}-${rel.agent_b}`} rel={rel} index={index} agents={agents} selectedFaction={selectedFaction} />
        ))}
      </div>
    </section>
  );
}

function GraphLink({ rel, index, agents, selectedFaction }) {
  const a = agents.find((agent) => agent.id === rel.agent_a);
  const b = agents.find((agent) => agent.id === rel.agent_b);
  const top = 18 + (index % 5) * 31;
  const left = 18 + (index % 3) * 29;
  const status = rel.alliance_status === "allied" ? "allied" : rel.conflict_score > 35 ? "strained" : "neutral";

  return (
    <div className={`graph-link ${status}`} style={{ top: `${top}%`, left: `${left}%` }}>
      <span className={selectedFaction === a?.faction ? "focus" : ""}>{a?.faction?.[0] ?? "A"}</span>
      <i style={{ width: `${Math.max(34, rel.trust_score)}px` }} />
      <span className={selectedFaction === b?.faction ? "focus" : ""}>{b?.faction?.[0] ?? "B"}</span>
      <small>{rel.trust_score}</small>
    </div>
  );
}
