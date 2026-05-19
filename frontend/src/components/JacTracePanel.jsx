import { Cpu } from "lucide-react";

export function JacTracePanel({ traces = [] }) {
  const latest = traces.slice(-4).reverse();

  return (
    <section className="panel trace-panel">
      <div className="panel-header">
        <h2>Jac Agent Trace</h2>
        <p>Live walker decisions powering civilization behavior.</p>
      </div>
      <div className="trace-list">
        {latest.length ? latest.map((trace) => (
          <article className="trace-card" key={trace.id ?? `${trace.civilization}-${trace.tick}`}>
            <header>
              <Cpu size={14} />
              <strong>{trace.walker ?? "decide_strategy"}</strong>
              <span>t{trace.tick}</span>
            </header>
            <div className="trace-civ">{trace.civilization}</div>
            <dl>
              {Object.entries(trace.inputs ?? {}).slice(0, 6).map(([key, value]) => (
                <div key={key}>
                  <dt>{key.replaceAll("_", " ")}</dt>
                  <dd>{String(value || "none")}</dd>
                </div>
              ))}
            </dl>
            <b>{trace.decision}</b>
            <p>{trace.reason}</p>
          </article>
        )) : (
          <p className="empty-note">Tick the world or issue a command to see Jac decisions.</p>
        )}
      </div>
    </section>
  );
}
