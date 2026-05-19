import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Biohazard,
  Brain,
  CloudLightning,
  Crown,
  FastForward,
  Flame,
  Info,
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
import { JacTracePanel } from "./components/JacTracePanel.jsx";
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
  const [command, setCommand] = useState("");
  const [commandStatus, setCommandStatus] = useState("");
  const [showAbout, setShowAbout] = useState(false);

  const selectedCiv = useMemo(
    () => {
      const alive = state.civilizations?.filter((civ) => civ.status !== "collapsed" && civ.population > 0) ?? [];
      return alive.find((civ) => civ.id === selectedCivId) ?? alive[0] ?? state.civilizations?.[0];
    },
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

  const submitCommand = (event) => {
    event.preventDefault();
    const text = command.trim();
    if (!text) return;
    setCommand("");
    return runAction(`Command: ${text}`, async () => {
      const result = await apiRequest("/commands", {
        method: "POST",
        body: JSON.stringify({ text }),
      });
      setCommandStatus(result.message ?? "Command understood -> Jac walker triggered -> World updated");
      return result.state;
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
  const activeOrders = (state.orders ?? []).slice(-3);
  const latestTrace = (state.jac_traces ?? []).slice(-1)[0];
  const aliveCount = state.metrics?.alive_civilizations ?? state.civilizations?.filter((civ) => civ.status !== "collapsed").length ?? 0;

  return (
    <main className={`god-shell cinematic-${cinematic ?? "idle"}`}>
      {cinematic && <CinematicOverlay type={cinematic} />}

      <aside className="left-rail">
        <div className="brand-lockup">
          <div className="logo-mark" aria-hidden="true">
            <Crown size={17} />
            <b>JC</b>
          </div>
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

        <section className="rail-section command-section">
          <div className="section-title">Command</div>
          <form className="command-form" onSubmit={submitCommand}>
            <input
              value={command}
              onChange={(event) => setCommand(event.target.value)}
              placeholder="Varku attack Khepri"
              aria-label="World command"
            />
            <button type="submit">Issue</button>
          </form>
          {commandStatus && <p className="command-status">{commandStatus}</p>}
          <p className="command-help">Try: Khepri ally Solarians / meteor desert / give Solarians tech boost</p>
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
            {apiOnline && state.jac_runtime?.enabled ? "Live Jac backend" : apiOnline ? "Actual live backend" : "Preset fallback"}
          </div>
          <button className="about-jac-button" onClick={() => setShowAbout(true)}>
            <Info size={14} />
            About Jac
          </button>
        </header>

        <WorldMap state={state} selectedCivId={selectedCiv?.id} onSelectCiv={setSelectedCivId} />

        <div className="world-intel-console">
          <div className="world-dossier">
            <article>
              <span>World Condition</span>
              <strong>{aliveCount} civilizations alive</strong>
              <p>{(state.metrics?.deaths ?? 0).toLocaleString()} total deaths / {(state.metrics?.kills ?? 0).toLocaleString()} combat kills / {state.effects?.length ?? 0} active effects</p>
            </article>
            <article>
              <span>Selected Faction</span>
              <strong>{selectedCiv?.name ?? "No faction"}</strong>
              {selectedCiv ? (
                <div className="faction-mini-stats">
                  <b>Pop {selectedCiv.population.toLocaleString()}</b>
                  <b>Stability {selectedCiv.stability}%</b>
                  <b>Kills {(selectedCiv.kills ?? 0).toLocaleString()}</b>
                  <b>Deaths {(selectedCiv.deaths ?? 0).toLocaleString()}</b>
                  <b>Tech {selectedCiv.technology}</b>
                  <b>Recent {selectedCiv.recent_deaths ?? 0}</b>
                </div>
              ) : (
                <p>Select a faction on the map.</p>
              )}
            </article>
            <article>
              <span>Active Orders</span>
              <strong>{activeOrders.length ? activeOrders.map((order) => order.type).join(", ") : "No active routes"}</strong>
              <p>{activeOrders[0] ? `${activeOrders[0].source} -> ${activeOrders[0].target} / ${activeOrders[0].progress ?? 0}% progress` : "Wars, alliances, and trade routes will appear here."}</p>
            </article>
            <article>
              <span>Latest Jac Decision</span>
              <strong>{latestTrace ? `${latestTrace.civilization}: ${latestTrace.decision}` : "Awaiting walker"}</strong>
              <p>{latestTrace?.reason ?? "Tick the world or issue a command to see live agent reasoning."}</p>
            </article>
          </div>
          <JacTracePanel traces={state.jac_traces ?? []} />
        </div>
      </section>

      <aside className="right-rail">
        <AgentPanel civilization={selectedCiv} agents={selectedAgents} allAgents={state.agents} relationships={state.relationships} />
        <ReasoningLog logs={state.reasoning_logs ?? []} agents={state.agents} />
        <AllianceGraph agents={state.agents} relationships={state.relationships} selectedFaction={selectedCiv?.name} civilizations={state.civilizations ?? []} metrics={state.metrics ?? {}} />
      </aside>

      <section className="bottom-console">
        <EventTimeline events={state.events ?? []} />
        <div className="news-ticker chronicle-board" aria-label="Live world ticker">
          <header>
            <span>Chronicle</span>
            <small>Tick {state.tick}</small>
          </header>
          <article className="chronicle-feature">
            <b>{(latestNews[0]?.headline ?? "The world waits for a god's command.")}</b>
            <p>{latestNews[0]?.body ?? status}</p>
          </article>
          <div className="chronicle-ribbon" aria-hidden="true">
            <div>
              {(latestNews.length ? [...latestNews, ...latestNews] : [{ id: "seed-news", headline: "The world waits for a god's command.", body: status }]).map((item, index) => (
                <p key={`${item.id}-${index}`}>
                  <strong>Tick {item.tick ?? state.tick}</strong>
                  {item.headline}
                </p>
              ))}
            </div>
          </div>
        </div>
      </section>

      {showAbout && (
        <div className="about-backdrop" role="dialog" aria-modal="true" aria-label="How Jac is used">
          <section className="about-modal">
            <header>
              <h2>How Jac Powers This World</h2>
              <button onClick={() => setShowAbout(false)}>Close</button>
            </header>
            <p>
              Jac powers the agentic civilization logic. Each civilization is represented as an agent node. Jac walkers evaluate world state, memory, personality, threats, and resources, then choose actions. React only visualizes the simulation, and FastAPI connects the frontend with the Jac-powered backend.
            </p>
            <div className="architecture-line">
              {"React Frontend -> FastAPI Backend -> Jac Agent Engine -> Civilization Decisions -> World State Update -> Live Map Visualization"}
            </div>
          </section>
        </div>
      )}
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
    <div className={`cinematic-overlay ${type}`}>
      <div className="impact-ring" />
      <div className="cinematic-pixels" aria-hidden="true">
        {Array.from({ length: 18 }, (_, index) => <i key={index} style={{ "--p": index }} />)}
      </div>
      <Flame className="impact-icon" size={60} />
      <h2>{copy[0]}</h2>
      <p>{copy[1]}</p>
    </div>
  );
}
