import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Biohazard,
  Brain,
  CloudLightning,
  FastForward,
  Flame,
  Landmark,
  Pause,
  Play,
  Radio,
  RefreshCw,
  Skull,
  Sparkles,
  Swords,
  Zap,
} from "lucide-react";
import { AgentPanel } from "./components/AgentPanel.jsx";
import { AllianceGraph } from "./components/AllianceGraph.jsx";
import { EventTimeline } from "./components/EventTimeline.jsx";
import { ReasoningLog } from "./components/ReasoningLog.jsx";
import { WorldMap } from "./components/WorldMap.jsx";
import { apiRequest, createDemoState } from "./lib/api.js";

const GOD_EVENTS = [
  { type: "war", label: "War", icon: Swords },
  { type: "plague", label: "Plague", icon: Biohazard },
  { type: "meteor", label: "Meteor", icon: Flame },
  { type: "ai_uprising", label: "AI Uprising", icon: Brain },
  { type: "resource_boom", label: "Resource Boom", icon: Sparkles },
  { type: "religion", label: "Religion", icon: Landmark },
  { type: "climate_collapse", label: "Climate Collapse", icon: CloudLightning },
  { type: "alien_contact", label: "Alien Contact", icon: Radio },
  { type: "technological_revolution", label: "Tech Revolution", icon: Zap },
  { type: "nuclear_strike", label: "Nuclear Strike", icon: Skull, danger: true },
];

const SPEEDS = [0, 1, 5, 20, 100];

export default function App() {
  const [state, setState] = useState(createDemoState);
  const [selectedCivId, setSelectedCivId] = useState("civ-solarians");
  const [apiOnline, setApiOnline] = useState(false);
  const [status, setStatus] = useState("Demo state loaded");
  const [speed, setSpeed] = useState(1);
  const [cinematic, setCinematic] = useState(null);

  const selectedCiv = useMemo(
    () => state.civilizations?.find((civ) => civ.id === selectedCivId) ?? state.civilizations?.[0],
    [selectedCivId, state.civilizations]
  );

  const selectedAgents = useMemo(
    () => state.agents.filter((agent) => agent.faction === selectedCiv?.name),
    [state.agents, selectedCiv]
  );

  const syncState = useCallback(async () => {
    try {
      const next = await apiRequest("/simulation/state");
      setState(next);
      setApiOnline(true);
      setStatus("Live world linked");
      if (!next.civilizations?.some((civ) => civ.id === selectedCivId)) {
        setSelectedCivId(next.civilizations?.[0]?.id ?? "");
      }
    } catch {
      setApiOnline(false);
      setStatus("Using local story seed");
    }
  }, [selectedCivId]);

  useEffect(() => {
    syncState();
  }, [syncState]);

  useEffect(() => {
    if (speed <= 0 || !apiOnline) return undefined;
    const delay = speed >= 100 ? 600 : speed >= 20 ? 900 : speed >= 5 ? 1400 : 2600;
    const timer = window.setInterval(async () => {
      try {
        setState(await apiRequest("/simulation/tick", { method: "POST" }));
      } catch {
        setApiOnline(false);
      }
    }, delay);
    return () => window.clearInterval(timer);
  }, [apiOnline, speed]);

  const runAction = async (label, request) => {
    try {
      const next = await request();
      setState(next);
      setApiOnline(true);
      setStatus(label);
    } catch (error) {
      setApiOnline(false);
      setStatus(`${label} unavailable: ${error.message}`);
    }
  };

  const triggerGodEvent = (eventType) => {
    const label = eventType.replaceAll("_", " ");
    setCinematic(eventType);
    window.setTimeout(() => setCinematic(null), 1800);
    return runAction(`${label} triggered`, async () => {
      await apiRequest("/events/god", {
        method: "POST",
        body: JSON.stringify({ type: eventType, x: 6, y: 5, radius: eventType === "nuclear_strike" ? 4 : 3 }),
      });
      return apiRequest("/simulation/state");
    });
  };

  const restart = () =>
    runAction("World restarted", () =>
      apiRequest("/simulation/start", {
        method: "POST",
        body: JSON.stringify({ agent_count: 10, seed: Date.now() % 999, width: 13, height: 10 }),
      })
    );

  const latestNews = state.news?.slice(-4).reverse() ?? [];

  return (
    <main className={`god-shell cinematic-${cinematic ?? "idle"}`}>
      {cinematic && <CinematicOverlay type={cinematic} />}

      <aside className="left-rail">
        <div className="brand-lockup">
          <Sparkles size={22} />
          <div>
            <strong>Jac Civilization</strong>
            <span>God Mode</span>
          </div>
        </div>

        <section className="rail-section">
          <div className="section-title">World Events</div>
          <div className="event-grid">
            {GOD_EVENTS.map(({ type, label, icon: Icon, danger }) => (
              <button className={`god-button ${danger ? "danger" : ""}`} key={type} onClick={() => triggerGodEvent(type)}>
                <Icon size={15} />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="rail-section">
          <div className="section-title">Time Speed</div>
          <div className="speed-row">
            {SPEEDS.map((value) => (
              <button className={speed === value ? "active" : ""} key={value} onClick={() => setSpeed(value)}>
                {value === 0 ? <Pause size={14} /> : value === 1 ? <Play size={14} /> : <FastForward size={14} />}
                {value === 0 ? "Pause" : value === 100 ? "Century" : `${value}x`}
              </button>
            ))}
          </div>
        </section>

        <section className="rail-section feed-section">
          <div className="section-title">World News</div>
          <div className="news-feed">
            {latestNews.length ? latestNews.map((item) => (
              <article key={item.id}>
                <span>Tick {item.tick}</span>
                <strong>{item.headline}</strong>
                <p>{item.body}</p>
              </article>
            )) : (
              <p className="empty-note">Trigger an event and the world press wakes up.</p>
            )}
          </div>
        </section>

        <button className="restart-button" onClick={restart}>
          <RefreshCw size={15} />
          Restart World
        </button>
      </aside>

      <section className="world-stage">
        <header className="living-topbar">
          <div>
            <h1>Living Civilization World</h1>
            <p>
              Tick {state.tick} / {state.civilizations?.length ?? 0} civilizations / {state.cities?.length ?? 0} cities / {state.effects?.length ?? 0} active effects
            </p>
          </div>
          <div className="live-pill">
            <span className={apiOnline ? "online" : ""} />
            {apiOnline ? "Actual live backend" : "Preset fallback"}
          </div>
        </header>

        <WorldMap state={state} selectedCivId={selectedCiv?.id} onSelectCiv={setSelectedCivId} />

        <div className="timeline-strip">
          {(state.events ?? []).slice(-8).map((event) => (
            <button key={event.id} className={`timeline-node ${event.type}`}>
              <span>{event.type.replaceAll("_", " ")}</span>
              <small>t{event.created_tick}</small>
            </button>
          ))}
        </div>
      </section>

      <aside className="right-rail">
        <AgentPanel civilization={selectedCiv} agents={selectedAgents} allAgents={state.agents} relationships={state.relationships} />
        <ReasoningLog logs={state.reasoning_logs ?? []} agents={state.agents} />
        <AllianceGraph agents={state.agents} relationships={state.relationships} selectedFaction={selectedCiv?.name} />
      </aside>

      <section className="bottom-console">
        <EventTimeline events={state.events ?? []} />
        <div className="news-ticker" aria-label="Live world ticker">
          <span>LIVE CHRONICLE</span>
          <div>
            {(latestNews.length ? latestNews : [{ id: "seed-news", headline: "The world waits for a god's command.", body: status }]).map((item) => (
              <p key={item.id}>{item.headline} / {item.body}</p>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

function CinematicOverlay({ type }) {
  const copy = {
    meteor: ["METEOR STRIKE", "Impact shockwave detected. Refugees are moving."],
    plague: ["GLOBAL PLAGUE", "Red fog spreads. Quarantine borders rising."],
    war: ["WAR DECLARED", "Alliance lines fracture across the frontier."],
    ai_uprising: ["AI UPRISING", "Machine councils seize command channels."],
    resource_boom: ["RESOURCE BOOM", "New veins glow under contested land."],
    religion: ["NEW RELIGION", "Faith waves split cultural identity."],
    climate_collapse: ["CLIMATE COLLAPSE", "Flood zones and storm bands expand."],
    alien_contact: ["ALIEN CONTACT", "Unknown signal changes every doctrine."],
    technological_revolution: ["TECH REVOLUTION", "Inventions cascade through the cities."],
    nuclear_strike: ["NUCLEAR STRIKE", "The region becomes a forbidden zone."],
  }[type] ?? ["WORLD EVENT", "Civilizations are adapting."];

  return (
    <div className="cinematic-overlay">
      <div className="impact-ring" />
      <Flame className="impact-icon" size={60} />
      <h2>{copy[0]}</h2>
      <p>{copy[1]}</p>
    </div>
  );
}
