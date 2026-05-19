import { ScrollText, Users } from "lucide-react";

const leaderPortraits = {
  Solarians: "/assets/leader-blonde.png",
  Elyrians: "/assets/leader-blonde.png",
  Khepri: "/assets/leader-blonde.png",
  Varku: "/assets/leader-boy.png",
  Nomads: "/assets/leader-boy.png",
};

export function AgentPanel({ civilization, agents, allAgents, relationships }) {
  if (!civilization) return null;
  const related = relationships.filter((rel) => {
    const a = allAgents.find((agent) => agent.id === rel.agent_a);
    const b = allAgents.find((agent) => agent.id === rel.agent_b);
    return a?.faction === civilization.name || b?.faction === civilization.name;
  });

  return (
    <section className="intel-panel">
      <div className="intel-header" style={{ "--civ": civilization.color }}>
        <div className="leader-frame">
          <img src={leaderPortraits[civilization.name] ?? "/assets/leader-boy.png"} alt={`${civilization.name} leader`} />
        </div>
        <div>
          <span>Faction Council</span>
          <h2>{civilization.name}</h2>
          <p>{civilization.trait} / {civilization.doctrine}</p>
        </div>
        <strong>{civilization.current_strategy.replaceAll("_", " ")}</strong>
      </div>

      <div className="intel-section">
        <h3><ScrollText size={14} /> Memory</h3>
        <div className="memory-scroll">
          {(civilization.memories ?? []).length ? civilization.memories.slice(-5).reverse().map((memory) => (
            <article key={memory.id}>
              <span>{memory.type}</span>
              <p>{memory.description}</p>
            </article>
          )) : <p className="empty-note">No defining memory yet. Trigger a world event.</p>}
        </div>
      </div>

      <div className="intel-section">
        <h3><Users size={14} /> People</h3>
        <div className="unit-list">
          {agents.map((agent) => (
            <div key={agent.id}>
              <strong>{agent.name}</strong>
              <span>{agent.goal.replaceAll("_", " ")}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="intel-section">
        <h3>Diplomatic Heat</h3>
        {related.slice(0, 4).map((rel) => (
          <div className="diplomacy-row" key={`${rel.agent_a}-${rel.agent_b}`}>
            <span>{rel.alliance_status}</span>
            <meter min="0" max="100" value={rel.trust_score} />
            <small>conflict {rel.conflict_score}</small>
          </div>
        ))}
      </div>
    </section>
  );
}
