import { Bot, Cpu } from "lucide-react";

export function ReasoningLog({ logs, agents }) {
  return (
    <section className="panel reasoning-panel">
      <div className="panel-header">
        <div>
          <h2>AI Explanations</h2>
          <p>Why civilizations adapt, attack, migrate, or invent</p>
        </div>
      </div>
      <div className="log-list">
        {logs.slice(-7).reverse().map((log) => {
          const agent = agents.find((item) => item.id === log.agent_id);
          return (
            <article className="reason-card" key={log.id}>
              <div className={`source ${log.source}`}>
                {log.source === "rules" ? <Cpu size={14} /> : <Bot size={14} />}
                {log.source}
              </div>
              <h3>{agent?.name ?? log.agent_id}: {log.action_taken}</h3>
              <p>{log.output_summary}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
