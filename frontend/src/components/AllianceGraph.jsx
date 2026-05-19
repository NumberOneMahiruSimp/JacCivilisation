import { Activity, Brain, HeartPulse, Shield, Skull, Swords, Users } from "lucide-react";

export function AllianceGraph({ agents, relationships, selectedFaction, civilizations = [], metrics = {} }) {
  const maxPopulation = Math.max(...civilizations.map((civ) => civ.population), 1);
  const visibleRelationships = relationships
    .filter((rel) => rel.alliance_status !== "neutral" || rel.trust_score > 64 || rel.conflict_score > 35)
    .slice(0, 5);

  return (
    <section className="panel graph-panel">
      <div className="panel-header">
        <div>
          <h2>World Data</h2>
          <p>Population, stability, technology, and diplomacy</p>
        </div>
      </div>

      <div className="metrics-stage">
        <div className="war-ledger">
          <LedgerItem icon={Skull} label="Deaths" value={metrics.deaths ?? 0} />
          <LedgerItem icon={Swords} label="Kills" value={metrics.kills ?? 0} />
          <LedgerItem icon={Activity} label="Recent" value={metrics.last_casualties ?? 0} />
        </div>

        <div className="metrics-bars">
          {civilizations.map((civ) => (
            <article className={`${selectedFaction === civ.name ? "focus" : ""} ${civ.status === "collapsed" ? "collapsed" : ""}`} key={civ.id} style={{ "--civ": civ.color }}>
              <header>
                <strong>{civ.name}</strong>
                <span>{civ.status === "collapsed" ? "Fallen" : civ.population.toLocaleString()}</span>
              </header>
              <Metric icon={Users} label="Population" value={civ.population} max={maxPopulation} />
              <Metric icon={Shield} label="Stability" value={civ.stability} max={100} />
              <Metric icon={Brain} label="Tech" value={civ.technology} max={100} />
              <Metric icon={HeartPulse} label="Faith" value={civ.faith} max={100} />
              <Metric icon={Swords} label="Kills" value={civ.kills ?? 0} max={Math.max(...civilizations.map((item) => item.kills ?? 0), 1)} />
              <Metric icon={Skull} label="Deaths" value={civ.deaths ?? 0} max={Math.max(...civilizations.map((item) => item.deaths ?? 0), 1)} />
            </article>
          ))}
        </div>

        <div className="diplomacy-list">
          <h3><Activity size={13} /> Diplomacy</h3>
          {visibleRelationships.map((rel) => (
            <DiplomacyRow key={`${rel.agent_a}-${rel.agent_b}`} rel={rel} agents={agents} selectedFaction={selectedFaction} />
          ))}
        </div>
      </div>
    </section>
  );
}

function LedgerItem({ icon: Icon, label, value }) {
  return (
    <article>
      <Icon size={14} />
      <span>{label}</span>
      <strong>{Number(value).toLocaleString()}</strong>
    </article>
  );
}

function Metric({ icon: Icon, label, value, max }) {
  const percent = Math.max(4, Math.min(100, Math.round((value / max) * 100)));
  return (
    <div className="metric-line">
      <Icon size={12} />
      <span>{label}</span>
      <i><b style={{ width: `${percent}%` }} /></i>
    </div>
  );
}

function DiplomacyRow({ rel, agents, selectedFaction }) {
  const a = agents.find((agent) => agent.id === rel.agent_a);
  const b = agents.find((agent) => agent.id === rel.agent_b);
  const status = rel.alliance_status === "allied" ? "allied" : rel.conflict_score > 35 ? "strained" : "neutral";

  return (
    <article className={`diplomacy-card ${status} ${selectedFaction === a?.faction || selectedFaction === b?.faction ? "focus" : ""}`}>
      <div>
        <strong>{a?.faction ?? "Faction"}</strong>
        <span>{status}</span>
        <strong>{b?.faction ?? "Faction"}</strong>
      </div>
      <meter min="0" max="100" value={rel.trust_score} />
      <small>Trust {rel.trust_score} / Conflict {rel.conflict_score}</small>
    </article>
  );
}
