import { AlertTriangle, ArrowRight } from "lucide-react";

export function EventTimeline({ events }) {
  return (
    <section className="panel timeline-panel">
      <div className="panel-header">
        <div>
          <h2>Timeline Replay</h2>
          <p>World shocks, splits, negotiations, and collapses</p>
        </div>
      </div>
      <div className="timeline">
        {events.slice(-8).reverse().map((event) => (
          <article className="timeline-item" key={event.id}>
            <div className={`event-icon ${event.type}`}>
              {["plague", "meteor", "war", "nuclear_strike"].includes(event.type) ? <AlertTriangle size={14} /> : <ArrowRight size={14} />}
            </div>
            <div>
              <strong>Tick {event.created_tick} / {event.type.replaceAll("_", " ")}</strong>
              <p>{event.summary}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
