import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  ArrowDown,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  Check,
  CheckCheck,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  CloudSun,
  Coffee,
  Download,
  ExternalLink,
  FlaskConical,
  Info,
  Leaf,
  LoaderCircle,
  LockKeyhole,
  MapPin,
  Plus,
  Printer,
  RefreshCw,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Sun,
  Trash2,
  TriangleAlert,
  UnlockKeyhole,
  Users,
  Workflow,
  X,
} from "lucide-react";
import {
  fingerprint,
  minutes,
  number,
  prettyDate,
  request,
  timeString,
} from "./api";
import type {
  AgentResponse,
  Health,
  PlanRequest,
  PlanResult,
  ScheduleItem,
  Task,
} from "./types";

const places = [
  { name: "Delhi · DTU", latitude: 28.75, longitude: 77.12 },
  { name: "Jaipur", latitude: 26.91, longitude: 75.79 },
  { name: "Ahmedabad", latitude: 23.02, longitude: 72.57 },
  { name: "Chennai", latitude: 13.08, longitude: 80.27 },
];
const toolLabels: Record<string, string> = {
  inspect_plan: "Read workday",
  propose_plan: "Review changes",
  propose_changes: "Review changes",
  inspect_weather: "Fetch forecast",
  fetch_weather: "Fetch forecast",
  optimize_plan: "Find schedule",
};
const hues = [
  "#34715d",
  "#b88c36",
  "#7397a3",
  "#aa785c",
  "#797bb0",
  "#6c8e48",
  "#a77089",
  "#5b8290",
];
type Accepted = { at: string; result: PlanResult };
const errorText = (error: unknown) =>
  error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
function IconLabel({
  children,
  icon,
}: {
  children: ReactNode;
  icon: ReactNode;
}) {
  return (
    <span className="icon-label">
      {icon}
      {children}
    </span>
  );
}
function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">
        <Sun size={24} />
        <span />
      </span>
      <span>
        heatshift<span className="brand-dot">.</span>
      </span>
    </div>
  );
}
function Alert({
  children,
  tone = "warning",
}: {
  children: ReactNode;
  tone?: "warning" | "info" | "success";
}) {
  return (
    <div
      className={`alert ${tone}`}
      role={tone === "warning" ? "alert" : "status"}
    >
      {tone === "success" ? (
        <CheckCheck size={17} />
      ) : tone === "info" ? (
        <Info size={17} />
      ) : (
        <TriangleAlert size={17} />
      )}
      <div>{children}</div>
    </div>
  );
}

function WeatherChart({ result }: { result: PlanResult }) {
  const { weather, request: plan } = result;
  const start = minutes(plan.shiftStart),
    end = minutes(plan.shiftEnd);
  const hours = (weather?.hours ?? []).filter(
    (h) =>
      minutes(h.time) >= start - 60 &&
      minutes(h.time) <= end + 60 &&
      Number.isFinite(h.apparentTemperatureC),
  );
  if (hours.length < 2)
    return (
      <div className="empty-chart">
        Not enough hourly forecast data to draw a chart.
      </div>
    );
  const w = 760,
    h = 160,
    pad = { l: 34, r: 16, t: 18, b: 28 };
  const values = hours.map((x) => x.apparentTemperatureC);
  const lo = Math.floor(Math.min(...values, plan.thresholdC) - 2),
    hi = Math.ceil(Math.max(...values, plan.thresholdC) + 2);
  const x = (t: number) =>
      pad.l + ((t - start) / (end - start)) * (w - pad.l - pad.r),
    y = (v: number) => pad.t + ((hi - v) / (hi - lo)) * (h - pad.t - pad.b);
  const visible = hours.filter(
    (d) => minutes(d.time) >= start && minutes(d.time) <= end,
  );
  if (!visible.length) return null;
  const path = visible
    .map(
      (d, i) =>
        `${i ? "L" : "M"}${x(minutes(d.time))},${y(d.apparentTemperatureC)}`,
    )
    .join(" ");
  const base = h - pad.b;
  const ticks = Array.from(
    { length: Math.floor((end - start) / 120) + 1 },
    (_, i) => start + i * 120,
  );
  return (
    <div className="weather-chart">
      <svg
        viewBox={`0 0 ${w} ${h}`}
        role="img"
        aria-label={`Apparent temperature forecast for the shift, ranging from ${Math.min(...values).toFixed(1)} to ${Math.max(...values).toFixed(1)} degrees Celsius`}
      >
        <defs>
          <linearGradient id="warmth" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#dfad55" stopOpacity=".40" />
            <stop offset="100%" stopColor="#dfad55" stopOpacity=".025" />
          </linearGradient>
        </defs>
        {[lo, (lo + hi) / 2, hi].map((v) => (
          <g key={v}>
            <line
              x1={pad.l}
              x2={w - pad.r}
              y1={y(v)}
              y2={y(v)}
              stroke="#eae8df"
              strokeDasharray="3 4"
            />
            <text x={0} y={y(v) + 4} className="chart-label">
              {v.toFixed(0)}°
            </text>
          </g>
        ))}
        <path
          d={`${path} L${x(minutes(visible.at(-1)!.time))},${base} L${x(minutes(visible[0].time))},${base} Z`}
          fill="url(#warmth)"
        />
        <path
          d={path}
          fill="none"
          stroke="#c29442"
          strokeWidth="2.8"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        <line
          x1={pad.l}
          x2={w - pad.r}
          y1={y(plan.thresholdC)}
          y2={y(plan.thresholdC)}
          stroke="#a27735"
          strokeWidth="1"
          strokeDasharray="5 5"
        />
        {visible.map((d) => (
          <circle
            key={d.time}
            cx={x(minutes(d.time))}
            cy={y(d.apparentTemperatureC)}
            r={3}
            fill="#fffdf7"
            stroke="#bc8a39"
            strokeWidth={1.5}
          >
            <title>
              {d.time} · feels like {d.apparentTemperatureC.toFixed(1)}°C · air{" "}
              {d.temperatureC.toFixed(1)}°C
            </title>
          </circle>
        ))}
        {ticks.map((t) => (
          <text
            key={t}
            x={x(t)}
            y={h - 4}
            textAnchor="middle"
            className="chart-label"
          >
            {timeString(t)}
          </text>
        ))}
      </svg>
      <div className="chart-legend">
        <span>
          <i className="dot amber" />
          Apparent temperature
        </span>
        <span>
          <i className="dashed" />
          {plan.thresholdC}°C planning threshold
        </span>
        <span className="forecast-note">
          Forecast · not a heat-safety limit
        </span>
      </div>
    </div>
  );
}

function Timeline({ result }: { result: PlanResult }) {
  const p = result.request,
    start = minutes(p.shiftStart),
    span = minutes(p.shiftEnd) - start;
  const lanes: [string, ScheduleItem[]][] = [
    ["Original", result.baselineSchedule ?? []],
    ["Proposed", result.schedule ?? []],
  ];
  return (
    <div className="timeline">
      <div className="timeline-labels">
        <span />
        <div>
          <span>{p.shiftStart}</span>
          <span>{timeString(start + Math.round(span / 30) * 15)}</span>
          <span>{p.shiftEnd}</span>
        </div>
      </div>
      {lanes.map(([label, items]) => (
        <div className="timeline-row" key={label}>
          <span
            className={`lane-name ${label === "Proposed" ? "proposed-label" : ""}`}
          >
            {label}
          </span>
          <div
            className={`timeline-track ${label === "Proposed" ? "proposed-track" : ""}`}
          >
            {p.breaks.map((b, i) => (
              <div
                className="break-block"
                key={i}
                style={{
                  left: `${((minutes(b.start) - start) / span) * 100}%`,
                  width: `${((minutes(b.end) - minutes(b.start)) / span) * 100}%`,
                }}
                title={`Break ${b.start}–${b.end}`}
              >
                <Coffee size={12} />
              </div>
            ))}
            {items.map((item, i) => {
              const idx = p.tasks.findIndex((t) => t.id === item.taskId);
              const left = Math.max(
                  0,
                  ((minutes(item.start) - start) / span) * 100,
                ),
                width = Math.min(
                  100 - left,
                  ((minutes(item.end) - minutes(item.start)) / span) * 100,
                );
              return (
                <div
                  className={`task-block ${label === "Original" ? "original-block" : ""}`}
                  key={`${item.taskId}-${i}`}
                  style={{
                    left: `${left}%`,
                    width: `${Math.max(width, 0)}%`,
                    background: hues[(idx < 0 ? i : idx) % hues.length],
                  }}
                  title={`${item.title}: ${item.start}–${item.end}${item.locked ? " · locked" : ""}`}
                >
                  <span>{idx + 1}</span>
                  {item.locked && <LockKeyhole size={10} />}
                </div>
              );
            })}
            {!items.length && (
              <span className="no-schedule">
                {label === "Proposed"
                  ? "No feasible schedule"
                  : "No original schedule"}
              </span>
            )}
          </div>
        </div>
      ))}
      <div className="task-legend">
        {p.tasks.map((t, i) => (
          <span key={t.id}>
            <i style={{ background: hues[i % hues.length] }} />
            {i + 1}. {t.title}
          </span>
        ))}
        <span>
          <i className="break-swatch" />
          Break
        </span>
      </div>
    </div>
  );
}

function TaskEditor({
  task,
  index,
  update,
  remove,
}: {
  task: Task;
  index: number;
  update: (patch: Partial<Task>) => void;
  remove: () => void;
}) {
  return (
    <details className="task-editor">
      <summary>
        <span
          className="task-index"
          style={{ background: hues[index % hues.length] }}
        >
          {index + 1}
        </span>
        <span className="task-summary">
          <strong>{task.title || "Untitled task"}</strong>
          <span>
            {task.durationMinutes} min · {task.earliestStart}–{task.latestEnd}
          </span>
        </span>
        {task.locked ? <LockKeyhole size={14} className="locked-icon" /> : null}
        <ChevronDown size={15} className="disclosure" />
      </summary>
      <div className="task-fields">
        <label>
          Task name
          <input
            value={task.title}
            maxLength={80}
            onChange={(e) => update({ title: e.target.value })}
          />
        </label>
        <div className="field-pair">
          <label>
            Duration · minutes
            <input
              type="number"
              min={15}
              max={720}
              step={15}
              value={task.durationMinutes}
              onChange={(e) =>
                update({ durationMinutes: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Original start
            <input
              type="time"
              step={900}
              value={task.baselineStart}
              onChange={(e) => update({ baselineStart: e.target.value })}
            />
          </label>
        </div>
        <div className="field-pair">
          <label>
            Earliest start
            <input
              type="time"
              step={900}
              value={task.earliestStart}
              onChange={(e) => update({ earliestStart: e.target.value })}
            />
          </label>
          <label>
            Finish by
            <input
              type="time"
              step={900}
              value={task.latestEnd}
              onChange={(e) => update({ latestEnd: e.target.value })}
            />
          </label>
        </div>
        <div className="task-actions">
          <button
            type="button"
            className={`lock-button ${task.locked ? "is-locked" : ""}`}
            onClick={() => update({ locked: !task.locked })}
            aria-pressed={task.locked}
          >
            {task.locked ? (
              <LockKeyhole size={13} />
            ) : (
              <UnlockKeyhole size={13} />
            )}{" "}
            {task.locked ? "Start time locked" : "Flexible start"}
          </button>
          <button
            className="icon-button danger"
            aria-label={`Remove ${task.title}`}
            type="button"
            onClick={remove}
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
    </details>
  );
}

function ProposalDiff({
  before,
  after,
}: {
  before: PlanRequest;
  after: PlanRequest;
}) {
  const changes: string[] = [];
  if (before.date !== after.date)
    changes.push(`Date: ${before.date} → ${after.date}`);
  if (
    before.shiftStart !== after.shiftStart ||
    before.shiftEnd !== after.shiftEnd
  )
    changes.push(
      `Shift: ${before.shiftStart}–${before.shiftEnd} → ${after.shiftStart}–${after.shiftEnd}`,
    );
  if (fingerprint(before.location) !== fingerprint(after.location))
    changes.push(
      `Location: ${before.location.name} → ${after.location.name} (${after.location.latitude}, ${after.location.longitude})`,
    );
  if (before.thresholdC !== after.thresholdC)
    changes.push(
      `Planning threshold: ${before.thresholdC}°C → ${after.thresholdC}°C`,
    );
  if (fingerprint(before.breaks) !== fingerprint(after.breaks))
    changes.push(
      `Breaks: ${after.breaks.map((b) => `${b.start}–${b.end}`).join(", ") || "none"}`,
    );
  after.tasks.forEach((t) => {
    const old = before.tasks.find((o) => o.id === t.id);
    if (!old) changes.push(`Add ${t.title}: ${t.durationMinutes} minutes`);
    else {
      const edits: string[] = [];
      if (old.title !== t.title) edits.push(`rename to ${t.title}`);
      if (old.durationMinutes !== t.durationMinutes)
        edits.push(`${old.durationMinutes} → ${t.durationMinutes} min`);
      if (
        old.earliestStart !== t.earliestStart ||
        old.latestEnd !== t.latestEnd
      )
        edits.push(`window ${t.earliestStart}–${t.latestEnd}`);
      if (old.baselineStart !== t.baselineStart)
        edits.push(`original start ${t.baselineStart}`);
      if (old.locked !== t.locked)
        edits.push(t.locked ? "lock start" : "unlock start");
      if (edits.length) changes.push(`${old.title}: ${edits.join(", ")}`);
    }
  });
  before.tasks
    .filter((t) => !after.tasks.some((a) => a.id === t.id))
    .forEach((t) => changes.push(`Remove ${t.title}`));
  return (
    <ul className="proposal-changes">
      {changes.length ? (
        changes.map((c, i) => <li key={i}>{c}</li>)
      ) : (
        <li>
          Task constraints are unchanged. Review the agent's schedule and
          explanation.
        </li>
      )}
    </ul>
  );
}

export default function App() {
  const [plan, setPlan] = useState<PlanRequest | null>(null),
    [result, setResult] = useState<PlanResult | null>(null),
    [health, setHealth] = useState<Health | null>(null);
  const [loading, setLoading] = useState(true),
    [optimizing, setOptimizing] = useState(false),
    [lastRunFailed, setLastRunFailed] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [scenario, setScenario] = useState<"normal" | "conflict">("normal"),
    [activeNav, setActiveNav] = useState("planner");
  const [agentInput, setAgentInput] = useState(""),
    [agentBusy, setAgentBusy] = useState(false),
    [agentError, setAgentError] = useState(""),
    [agentResponse, setAgentResponse] = useState<AgentResponse | null>(null),
    [agentBase, setAgentBase] = useState<PlanRequest | null>(null),
    [sentMessage, setSentMessage] = useState(""),
    [proposalApplied, setProposalApplied] = useState(false);
  const [accepted, setAccepted] = useState<Accepted | null>(() => {
    try {
      return JSON.parse(localStorage.getItem("heatshift-accepted") ?? "null");
    } catch {
      return null;
    }
  });
  const [showHistory, setShowHistory] = useState(false);
  const agentRef = useRef<HTMLTextAreaElement>(null);
  const dirty = !!(
    plan &&
    result &&
    fingerprint(plan) !== fingerprint(result.request)
  );
  const validResult =
    !!result && result.status !== "infeasible" && !dirty && !lastRunFailed;
  const acceptedCurrent =
    !!accepted &&
    !!result &&
    !dirty &&
    fingerprint(accepted.result.request) === fingerprint(result.request) &&
    fingerprint(accepted.result.schedule) === fingerprint(result.schedule);
  const workMinutes =
    plan?.tasks.reduce((total, t) => total + t.durationMinutes, 0) ?? 0;

  async function optimize(current: PlanRequest) {
    setOptimizing(true);
    setLastRunFailed(false);
    setError("");
    setNotice("");
    try {
      setResult(await request<PlanResult>("/api/optimize", current));
    } catch (e) {
      setError(errorText(e));
      setLastRunFailed(true);
    } finally {
      setOptimizing(false);
    }
  }
  async function loadDemo(conflict = false) {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const { plan: demo } = await request<{ plan: PlanRequest }>("/api/demo");
      const next = conflict
        ? {
            ...demo,
            tasks: demo.tasks.map((t, i) =>
              i < 2
                ? {
                    ...t,
                    baselineStart: demo.shiftStart,
                    earliestStart: demo.shiftStart,
                    latestEnd: demo.shiftEnd,
                    locked: true,
                  }
                : t,
            ),
          }
        : demo;
      setPlan(next);
      setScenario(conflict ? "conflict" : "normal");
      setAgentResponse(null);
      setResult(null);
      await optimize(next);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    let alive = true;
    async function start() {
      const [demo, h] = await Promise.allSettled([
        request<{ plan: PlanRequest }>("/api/demo"),
        request<Health>("/api/health"),
      ]);
      if (!alive) return;
      if (h.status === "fulfilled") setHealth(h.value);
      if (demo.status === "fulfilled") {
        setPlan(demo.value.plan);
        setLoading(false);
        setOptimizing(true);
        try {
          const answer = await request<PlanResult>(
            "/api/optimize",
            demo.value.plan,
          );
          if (alive) setResult(answer);
        } catch (e) {
          if (alive) {
            setError(errorText(e));
            setLastRunFailed(true);
          }
        } finally {
          if (alive) setOptimizing(false);
        }
      } else {
        setError(errorText(demo.reason));
        setLoading(false);
      }
    }
    void start();
    return () => {
      alive = false;
    };
  }, []);
  function patchPlan(patch: Partial<PlanRequest>) {
    setPlan((p) => (p ? { ...p, ...patch } : p));
    setNotice("");
  }
  function updateTask(id: string, patch: Partial<Task>) {
    if (plan)
      patchPlan({
        tasks: plan.tasks.map((t) => (t.id === id ? { ...t, ...patch } : t)),
      });
  }
  async function sendAgent(message = agentInput) {
    if (!plan || !message.trim() || agentBusy) return;
    const snapshot = structuredClone(plan);
    setAgentBusy(true);
    setAgentError("");
    setAgentResponse(null);
    setProposalApplied(false);
    setSentMessage(message.trim());
    setAgentBase(snapshot);
    setAgentInput("");
    try {
      const response = await request<AgentResponse>("/api/agent", {
        message: message.trim(),
        plan: snapshot,
      });
      setAgentResponse(response);
      setHealth((h) =>
        h
          ? {
              ...h,
              agent: {
                available: true,
                provider: response.provider,
                model: response.model,
              },
            }
          : h,
      );
    } catch (e) {
      setAgentError(errorText(e));
    } finally {
      setAgentBusy(false);
    }
  }
  function applyProposal() {
    const proposed = agentResponse?.proposedPlan;
    if (!proposed || !agentBase || fingerprint(agentBase) !== fingerprint(plan))
      return;
    setPlan(proposed);
    setProposalApplied(true);
    setNotice(
      "Agent proposal applied to your inputs. Review the plan, then accept it when ready.",
    );
    if (
      agentResponse?.result &&
      fingerprint(agentResponse.result.request) === fingerprint(proposed)
    ) {
      setResult(agentResponse.result);
      setLastRunFailed(false);
    } else void optimize(proposed);
  }
  function acceptPlan() {
    if (!result || !validResult) return;
    const next = { at: new Date().toISOString(), result };
    try {
      localStorage.setItem("heatshift-accepted", JSON.stringify(next));
      setAccepted(next);
      setNotice(
        "Plan accepted and saved in this browser. Share the report with your crew when ready.",
      );
    } catch {
      setError(
        "The browser could not save this plan. You can still export the report or JSON.",
      );
    }
  }
  function exportJSON() {
    if (!result) return;
    const blob = new Blob(
      [
        JSON.stringify(
          {
            application: "HeatShift",
            exportedAt: new Date().toISOString(),
            acceptance: acceptedCurrent
              ? { status: "accepted locally", at: accepted?.at }
              : { status: "not accepted" },
            disclaimer:
              "Forecast-based planning. Apparent temperature is not measured worker exposure or a medical safety assessment.",
            ...result,
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob),
      link = document.createElement("a");
    link.href = url;
    link.download = `heatshift-${result.request.date}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
  const improvement = result?.baselineValid ? result.metrics?.deltaC : null;
  const stats = result?.metrics;
  const nav = [
    { id: "planner", label: "Day planner", icon: <Workflow size={17} /> },
    { id: "crew", label: "Crew & tasks", icon: <Users size={17} /> },
    { id: "forecast", label: "Weather outlook", icon: <CloudSun size={17} /> },
    {
      id: "assistant",
      label: "Planning assistant",
      icon: <Sparkles size={17} />,
    },
    {
      id: "evidence",
      label: "Plan evidence",
      icon: <ClipboardCheck size={17} />,
    },
  ];

  return (
    <>
      <div className="app-shell">
        <aside className="sidebar">
          <a href="#planner" className="brand-link" aria-label="HeatShift home">
            <Brand />
          </a>
          <div className="workspace-badge">
            <span className="workspace-icon">
              <Leaf size={16} />
            </span>
            <div>
              <strong>Campus operations</strong>
              <span>One crew · day planning</span>
            </div>
          </div>
          <span className="nav-eyebrow">WORKSPACE</span>
          <nav>
            {nav.map((n) => (
              <a
                key={n.id}
                href={`#${n.id}`}
                title={n.label}
                aria-label={n.label}
                className={activeNav === n.id ? "active" : ""}
                onClick={() => setActiveNav(n.id)}
              >
                {n.icon}
                <span>{n.label}</span>
                {activeNav === n.id && <span className="nav-active-dot" />}
              </a>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="sidebar-art">
              <Sun size={36} />
              <div className="orbit-line" />
              <div className="orbit-line second" />
            </div>
            <h3>Work with the weather.</h3>
            <p>
              Same crew. Same commitments.
              <br />A more considered schedule.
            </p>
            <div className="sidebar-foot">
              <span className="tiny-status" /> Environmental Hacks{" "}
              <span>2026</span>
            </div>
          </div>
        </aside>
        <main id="planner">
          <header className="topbar">
            <span className="breadcrumb">
              Workspace <ChevronRight size={13} /> <strong>Day planner</strong>
            </span>
            <div className="topbar-right">
              <span className="quiet-pill">
                <span className={`status-dot ${health ? "" : "offline"}`} />
                {health
                  ? "Planning service connected"
                  : loading
                    ? "Connecting to service"
                    : "Planning service unavailable"}
              </span>
              <span className="avatar">HS</span>
            </div>
          </header>
          <div className="page-content">
            <section className="hero">
              <div>
                <div className="eyebrow">
                  <span /> BUILT AROUND YOUR CREW
                </div>
                <h1>
                  A cooler plan.
                  <br />
                  <em>The same work.</em>
                </h1>
                <p>
                  Move flexible work into cooler hours.
                  <br className="desktop-break" /> Keep every commitment, break,
                  and shift intact.
                </p>
              </div>
              <div className="hero-right">
                <div className="date-card">
                  <div className="date-icon">
                    <CalendarDays size={23} />
                  </div>
                  <div>
                    <span>YOUR NEXT WORKDAY</span>
                    <strong>
                      {plan ? prettyDate(plan.date) : "Preparing your planner"}
                    </strong>
                    <small>
                      <MapPin size={12} />
                      {plan?.location.name.replace(" (illustrative)", "") ??
                        "Choose a campus"}{" "}
                      · IST
                    </small>
                  </div>
                  <div className="sun-doodle">
                    <Sun size={48} />
                  </div>
                </div>
                <div className="hero-caption">
                  <ShieldCheck size={15} />
                  <span>Your constraints decide what can move.</span>
                </div>
              </div>
            </section>
            <div className="demo-strip">
              <span>
                <FlaskConical size={15} />
                <strong>Illustrative campus scenario</strong>
                <span className="demo-description">
                  Edit these tasks to match your crew.
                </span>
              </span>
              <div className="demo-controls">
                <span>TRY A SCENARIO</span>
                <button
                  disabled={loading || optimizing || agentBusy}
                  className={scenario === "normal" ? "selected" : ""}
                  onClick={() => void loadDemo(false)}
                >
                  Normal day
                </button>
                <button
                  disabled={loading || optimizing || agentBusy}
                  className={scenario === "conflict" ? "selected" : ""}
                  onClick={() => void loadDemo(true)}
                >
                  Conflicting locks
                </button>
              </div>
            </div>
            {error && (
              <Alert>
                {error}
                {!plan && (
                  <button
                    className="text-button"
                    onClick={() => void loadDemo()}
                  >
                    Retry connection <RefreshCw size={13} />
                  </button>
                )}
              </Alert>
            )}
            {notice && (
              <Alert tone="success">
                {notice}
                <button
                  className="dismiss"
                  aria-label="Dismiss notice"
                  onClick={() => setNotice("")}
                >
                  <X size={14} />
                </button>
              </Alert>
            )}
            {plan ? (
              <>
                <div className="planner-grid">
                  <section className="inputs-column" id="crew">
                    <div className="section-heading">
                      <div>
                        <span className="section-number">01</span>
                        <h2>Set the day</h2>
                      </div>
                      <span className="subtle">Your non-negotiables</span>
                    </div>
                    <fieldset
                      disabled={loading || optimizing}
                      className="input-fieldset"
                    >
                      <details className="panel day-settings">
                        <summary className="settings-summary">
                          <span className="settings-icon">
                            <Settings2 size={19} />
                          </span>
                          <span>
                            <strong>Day settings</strong>
                            <small>
                              {prettyDate(plan.date)} · {plan.shiftStart}–
                              {plan.shiftEnd}
                            </small>
                            <small>
                              {plan.breaks.length} protected{" "}
                              {plan.breaks.length === 1 ? "break" : "breaks"} ·
                              edit settings
                            </small>
                          </span>
                          <ChevronDown size={16} />
                        </summary>
                        <div className="settings-fields">
                          <div className="field-pair">
                            <label>
                              Work date
                              <input
                                aria-label="Work date"
                                type="date"
                                value={plan.date}
                                onChange={(e) =>
                                  patchPlan({ date: e.target.value })
                                }
                              />
                            </label>
                            <label>
                              Campus / city
                              <select
                                value={
                                  places.find(
                                    (p) =>
                                      plan.location.name === p.name ||
                                      plan.location.name ===
                                        `${p.name} (illustrative)`,
                                  )?.name ?? "custom"
                                }
                                onChange={(e) => {
                                  const place = places.find(
                                    (p) => p.name === e.target.value,
                                  );
                                  if (place) patchPlan({ location: place });
                                  else
                                    patchPlan({
                                      location: {
                                        ...plan.location,
                                        name: "Custom location",
                                      },
                                    });
                                }}
                              >
                                {places.map((p) => (
                                  <option key={p.name}>{p.name}</option>
                                ))}
                                <option value="custom">Custom location</option>
                              </select>
                            </label>
                          </div>
                          <details className="location-details">
                            <summary>
                              <MapPin size={12} /> Coordinates & location name{" "}
                              <ChevronDown size={12} />
                            </summary>
                            <label>
                              Location name
                              <input
                                value={plan.location.name}
                                onChange={(e) =>
                                  patchPlan({
                                    location: {
                                      ...plan.location,
                                      name: e.target.value,
                                    },
                                  })
                                }
                              />
                            </label>
                            <div className="field-pair">
                              <label>
                                Latitude
                                <input
                                  type="number"
                                  step="0.001"
                                  min={-90}
                                  max={90}
                                  value={plan.location.latitude}
                                  onChange={(e) =>
                                    patchPlan({
                                      location: {
                                        ...plan.location,
                                        latitude: Number(e.target.value),
                                      },
                                    })
                                  }
                                />
                              </label>
                              <label>
                                Longitude
                                <input
                                  type="number"
                                  step="0.001"
                                  min={-180}
                                  max={180}
                                  value={plan.location.longitude}
                                  onChange={(e) =>
                                    patchPlan({
                                      location: {
                                        ...plan.location,
                                        longitude: Number(e.target.value),
                                      },
                                    })
                                  }
                                />
                              </label>
                            </div>
                            <p>All schedules use India Standard Time.</p>
                          </details>
                          <div className="field-pair shift-fields">
                            <label>
                              <Clock3 size={12} /> Shift starts
                              <input
                                type="time"
                                step={900}
                                value={plan.shiftStart}
                                onChange={(e) =>
                                  patchPlan({ shiftStart: e.target.value })
                                }
                              />
                            </label>
                            <label>
                              Shift ends
                              <input
                                type="time"
                                step={900}
                                value={plan.shiftEnd}
                                onChange={(e) =>
                                  patchPlan({ shiftEnd: e.target.value })
                                }
                              />
                            </label>
                          </div>
                          <div className="breaks-heading">
                            <span>
                              <Coffee size={13} /> Protected breaks
                            </span>
                            <button
                              className="text-button"
                              type="button"
                              onClick={() =>
                                patchPlan({
                                  breaks: [
                                    ...plan.breaks,
                                    { start: "12:30", end: "13:00" },
                                  ],
                                })
                              }
                            >
                              <Plus size={13} /> Add
                            </button>
                          </div>
                          {plan.breaks.map((b, i) => (
                            <div className="break-inputs" key={i}>
                              <input
                                aria-label={`Break ${i + 1} starts`}
                                type="time"
                                step={900}
                                value={b.start}
                                onChange={(e) =>
                                  patchPlan({
                                    breaks: plan.breaks.map((old, j) =>
                                      j === i
                                        ? { ...old, start: e.target.value }
                                        : old,
                                    ),
                                  })
                                }
                              />
                              <span>to</span>
                              <input
                                aria-label={`Break ${i + 1} ends`}
                                type="time"
                                step={900}
                                value={b.end}
                                onChange={(e) =>
                                  patchPlan({
                                    breaks: plan.breaks.map((old, j) =>
                                      j === i
                                        ? { ...old, end: e.target.value }
                                        : old,
                                    ),
                                  })
                                }
                              />
                              <button
                                type="button"
                                className="icon-button"
                                aria-label={`Remove break ${i + 1}`}
                                onClick={() =>
                                  patchPlan({
                                    breaks: plan.breaks.filter(
                                      (_, j) => j !== i,
                                    ),
                                  })
                                }
                              >
                                <X size={13} />
                              </button>
                            </div>
                          ))}
                          <div className="threshold-control">
                            <div>
                              <label htmlFor="threshold">
                                Planning threshold
                              </label>
                              <span>
                                A comparison marker, not a safety limit
                              </span>
                            </div>
                            <div className="unit-input">
                              <input
                                id="threshold"
                                type="number"
                                min={10}
                                max={60}
                                step={1}
                                value={plan.thresholdC}
                                onChange={(e) =>
                                  patchPlan({
                                    thresholdC: Number(e.target.value),
                                  })
                                }
                              />
                              <span>°C</span>
                            </div>
                          </div>
                        </div>
                      </details>
                      <div className="tasks-heading">
                        <h3>
                          Outdoor work <span>{plan.tasks.length}/8</span>
                        </h3>
                        <span>{workMinutes} min total</span>
                      </div>
                      <div className="task-list">
                        {plan.tasks.map((t, i) => (
                          <TaskEditor
                            key={t.id}
                            task={t}
                            index={i}
                            update={(p) => updateTask(t.id, p)}
                            remove={() =>
                              patchPlan({
                                tasks: plan.tasks.filter(
                                  (old) => old.id !== t.id,
                                ),
                              })
                            }
                          />
                        ))}
                      </div>
                      <button
                        type="button"
                        className="add-task"
                        disabled={plan.tasks.length >= 8}
                        onClick={() =>
                          patchPlan({
                            tasks: [
                              ...plan.tasks,
                              {
                                id: `task-${Date.now()}`,
                                title: "New task",
                                durationMinutes: 60,
                                earliestStart: plan.shiftStart,
                                latestEnd: plan.shiftEnd,
                                baselineStart: plan.shiftStart,
                                locked: false,
                              },
                            ],
                          })
                        }
                      >
                        <Plus size={15} /> Add a task
                      </button>
                      <div className="constraint-note">
                        <LockKeyhole size={13} />
                        <span>
                          Locked starts stay put. Tasks stay whole. Nothing
                          slips outside its allowed window.
                        </span>
                      </div>
                    </fieldset>
                    <button
                      className="primary optimize-button"
                      disabled={loading || optimizing || !plan.tasks.length}
                      onClick={() => void optimize(plan)}
                    >
                      {optimizing ? (
                        <LoaderCircle className="spin" size={18} />
                      ) : (
                        <Sparkles size={17} />
                      )}{" "}
                      {optimizing
                        ? "Finding a cooler plan…"
                        : "Find a cooler plan"}
                      {!optimizing && <ArrowRight size={17} />}
                    </button>
                    <div className="solver-note">
                      Deterministic scheduling · 15-minute slots
                    </div>
                  </section>
                  <div className="results-column">
                    <div className="section-heading">
                      <div>
                        <span className="section-number">02</span>
                        <h2>See what changes</h2>
                      </div>
                      {lastRunFailed && result ? (
                        <span className="badge amber-badge">
                          Previous result · refresh failed
                        </span>
                      ) : dirty ? (
                        <span className="badge amber-badge">
                          Inputs changed · run again
                        </span>
                      ) : result ? (
                        <span
                          className={`badge ${result.status === "infeasible" ? "red-badge" : "green-badge"}`}
                        >
                          {result.status === "infeasible"
                            ? "Needs your review"
                            : result.status === "improved"
                              ? "A cooler plan found"
                              : result.status === "planned"
                                ? "Feasible plan found"
                                : "Constraints respected"}
                        </span>
                      ) : (
                        <span className="subtle">
                          Forecast-backed comparison
                        </span>
                      )}
                    </div>
                    {!result ? (
                      <div className="panel result-empty">
                        <span className="empty-orbit">
                          {optimizing ? (
                            <LoaderCircle className="spin" size={31} />
                          ) : (
                            <CloudSun size={34} />
                          )}
                        </span>
                        <h3>
                          {optimizing
                            ? "Reading the weather. Respecting the work."
                            : "Your comparison will appear here."}
                        </h3>
                        <p>
                          {optimizing
                            ? "Finding the best feasible hours for this crew, using real forecast data."
                            : "Set your tasks and find a cooler plan. If the forecast is unavailable, we’ll say so."}
                        </p>
                        <div className="empty-features">
                          <span>
                            <Check size={13} /> Same outdoor workload
                          </span>
                          <span>
                            <Check size={13} /> Breaks preserved
                          </span>
                          <span>
                            <Check size={13} /> Locks respected
                          </span>
                        </div>
                      </div>
                    ) : (
                      <>
                        {result.status === "infeasible" ? (
                          <div className="panel conflict-card">
                            <div className="conflict-icon">
                              <LockKeyhole size={23} />
                            </div>
                            <div>
                              <span className="eyebrow">
                                THE CONSTRAINTS DON’T FIT
                              </span>
                              <h3>No plan is better than a broken promise.</h3>
                              <p>{result.explanation}</p>
                              {result.violations?.length > 0 && (
                                <ul>
                                  {result.violations.map((v, i) => (
                                    <li key={i}>{v}</li>
                                  ))}
                                </ul>
                              )}
                              <p className="subtle">
                                Adjust a lock, window, or workload, then try
                                again. HeatShift will not silently drop work.
                              </p>
                            </div>
                          </div>
                        ) : (
                          <div className="metric-grid">
                            <div className="metric-card lead-metric">
                              <span className="metric-label">
                                {result.baselineValid
                                  ? "Average apparent temperature"
                                  : "Proposed apparent temperature"}
                              </span>
                              <div className="metric-value">
                                {improvement != null && improvement > 0.04 ? (
                                  <>
                                    <ArrowDown size={23} />
                                    {number(improvement, "°")}
                                    <span>cooler</span>
                                  </>
                                ) : (
                                  <>
                                    {number(
                                      stats?.proposedMeanApparentTemperatureC,
                                      "°C",
                                    )}
                                  </>
                                )}
                              </div>
                              <div className="metric-description">
                                {result.baselineValid ? (
                                  <>
                                    {number(
                                      stats?.baselineMeanApparentTemperatureC,
                                      "°",
                                    )}{" "}
                                    <ArrowRight size={12} />{" "}
                                    {number(
                                      stats?.proposedMeanApparentTemperatureC,
                                      "°",
                                    )}{" "}
                                    apparent temperature
                                  </>
                                ) : (
                                  "No comparison: original schedule is invalid"
                                )}
                              </div>
                            </div>
                            <div className="metric-card">
                              <span className="metric-label">
                                At or above {stats?.thresholdC}°C
                              </span>
                              <div className="metric-value small-value">
                                {stats?.proposedHotMinutes ?? "—"}
                                <span>min</span>
                              </div>
                              <div className="metric-description">
                                {result.baselineValid
                                  ? `Original: ${stats?.baselineHotMinutes ?? "—"} min`
                                  : "User-defined planning indicator"}
                              </div>
                            </div>
                            <div className="metric-card">
                              <span className="metric-label">
                                Work preserved
                              </span>
                              <div className="metric-value small-value">
                                {stats?.workMinutes ?? "—"}
                                <span>min</span>
                              </div>
                              <div className="metric-description">
                                <span className="micro-check">
                                  <Check size={10} />
                                </span>
                                {result.schedule.length} tasks · one crew
                              </div>
                            </div>
                          </div>
                        )}
                        <section className="panel outlook-panel">
                          <div className="panel-heading">
                            <div>
                              <IconLabel icon={<Workflow size={18} />}>
                                Before. After. All the work.
                              </IconLabel>
                              <p>
                                {prettyDate(result.request.date)} ·{" "}
                                {result.request.location.name}
                              </p>
                            </div>
                            <span className="source-chip">
                              <span className="status-dot" />
                              {result.weather?.mode === "saved"
                                ? "Saved forecast"
                                : "Live forecast"}
                            </span>
                          </div>
                          <div className="mini-heading timeline-heading">
                            <h3>
                              {result.status === "improved"
                                ? "Same tasks. Better timing."
                                : result.status === "infeasible"
                                  ? "Where the plan conflicts."
                                  : result.status === "planned"
                                    ? "A feasible way through the day."
                                    : "Your timing, checked."}
                            </h3>
                            <span>
                              {result.request.shiftStart}–
                              {result.request.shiftEnd} IST
                            </span>
                          </div>
                          {!result.baselineValid && (
                            <div className="inline-warning">
                              <Info size={14} />
                              The original schedule violates constraints;
                              improvement metrics are withheld.
                            </div>
                          )}
                          <Timeline result={result} />
                          <div className="plan-divider" />
                          <div className="mini-heading" id="forecast">
                            <h3>
                              <CloudSun size={16} /> Forecast along the shift
                            </h3>
                            <span>Apparent temperature</span>
                          </div>
                          <WeatherChart result={result} />
                        </section>
                        <section className="panel schedule-panel">
                          <div className="panel-heading">
                            <div>
                              <IconLabel icon={<ClipboardCheck size={17} />}>
                                Your proposed workday
                              </IconLabel>
                              <p>
                                {result.status === "infeasible"
                                  ? "Resolve the conflicts to produce a schedule."
                                  : "Every move is visible. You make the final call."}
                              </p>
                            </div>
                            {acceptedCurrent && (
                              <span className="badge green-badge">
                                <CheckCheck size={12} /> Accepted locally
                              </span>
                            )}
                          </div>
                          {result.schedule.length > 0 && (
                            <div className="schedule-table-wrap">
                              <table className="schedule-table">
                                <thead>
                                  <tr>
                                    <th>Task</th>
                                    <th>Original</th>
                                    <th>Proposed</th>
                                    <th>Feels like</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {result.schedule.map((item) => {
                                    const original =
                                        result.baselineSchedule.find(
                                          (o) => o.taskId === item.taskId,
                                        ),
                                      idx = result.request.tasks.findIndex(
                                        (t) => t.id === item.taskId,
                                      );
                                    return (
                                      <tr key={item.taskId}>
                                        <td>
                                          <span className="table-task">
                                            <i
                                              style={{
                                                background:
                                                  hues[idx % hues.length],
                                              }}
                                            />
                                            <span>
                                              {item.title}
                                              {item.locked && (
                                                <span className="task-lock-caption">
                                                  <LockKeyhole size={10} />{" "}
                                                  Start locked
                                                </span>
                                              )}
                                            </span>
                                          </span>
                                        </td>
                                        <td className="original-time">
                                          {original
                                            ? `${original.start}–${original.end}`
                                            : "—"}
                                        </td>
                                        <td>
                                          <span
                                            className={`time-pill ${original?.start !== item.start ? "moved" : ""}`}
                                          >
                                            {item.start}–{item.end}
                                            {original?.start !== item.start && (
                                              <ArrowUpRight size={11} />
                                            )}
                                          </span>
                                        </td>
                                        <td className="temp-cell">
                                          {number(
                                            item.meanApparentTemperatureC,
                                            "°",
                                          )}
                                        </td>
                                      </tr>
                                    );
                                  })}
                                </tbody>
                              </table>
                            </div>
                          )}
                          <div className="explanation">
                            <span className="explanation-icon">
                              <Workflow size={15} />
                            </span>
                            <p>{result.explanation}</p>
                          </div>
                          <div className="schedule-actions">
                            <button
                              className="primary"
                              disabled={
                                !validResult || acceptedCurrent || optimizing
                              }
                              onClick={acceptPlan}
                            >
                              {acceptedCurrent ? (
                                <CheckCheck size={15} />
                              ) : (
                                <Check size={15} />
                              )}{" "}
                              {acceptedCurrent
                                ? "Accepted in this browser"
                                : "Accept proposed plan"}
                            </button>
                            <button
                              className="secondary"
                              disabled={!validResult}
                              onClick={() => window.print()}
                            >
                              <Printer size={15} />
                              <span>Print report</span>
                            </button>
                            <button
                              className="icon-button export-button"
                              aria-label="Export plan and evidence as JSON"
                              title="Export JSON with source data"
                              onClick={exportJSON}
                            >
                              <Download size={17} />
                            </button>
                          </div>
                          <p className="local-note">
                            Acceptance is saved locally. It does not notify or
                            assign your crew.
                          </p>
                        </section>
                      </>
                    )}
                    <section className="assistant-panel" id="assistant">
                      <div className="assistant-heading">
                        <div>
                          <span className="assistant-logo">
                            <Sparkles size={20} />
                          </span>
                          <div>
                            <h2>A little help with the what-ifs.</h2>
                            <p>
                              Ask the assistant to rethink the day, within your
                              rules.
                            </p>
                          </div>
                        </div>
                        <span
                          className={`assistant-status ${health?.agent.available ? "ready" : ""}`}
                        >
                          <span />
                          {health?.agent.available
                            ? "AWS Strands ready"
                            : "AWS Strands unavailable"}
                        </span>
                      </div>
                      <div className="suggestions">
                        {[
                          "Find a cooler plan without changing any constraints.",
                          "Garden maintenance can only start after 13:00. Replan the other jobs.",
                        ].map((prompt) => (
                          <button
                            key={prompt}
                            disabled={agentBusy}
                            onClick={() => {
                              setAgentInput(prompt);
                              agentRef.current?.focus();
                            }}
                          >
                            {prompt}
                            <ArrowUpRight size={12} />
                          </button>
                        ))}
                      </div>
                      {sentMessage && (
                        <div className="user-message">
                          <span>YOU</span>
                          <p>{sentMessage}</p>
                        </div>
                      )}
                      {agentBusy && (
                        <div className="agent-thinking">
                          <LoaderCircle className="spin" size={15} />
                          <span>
                            Working with your current plan… Tool activity
                            appears when returned.
                          </span>
                        </div>
                      )}
                      {agentError && (
                        <Alert>
                          {agentError}
                          <p className="agent-error-note">
                            The deterministic planner above remains available.
                            No agent changes were applied.
                          </p>
                        </Alert>
                      )}
                      {agentResponse && (
                        <div className="agent-answer">
                          <div className="answer-label">
                            <Sparkles size={13} /> AWS STRANDS{" "}
                            <span>
                              {agentResponse.provider} · {agentResponse.model}
                            </span>
                          </div>
                          <p className="answer-text">{agentResponse.message}</p>
                          {agentResponse.trace?.length > 0 && (
                            <details className="trace-details">
                              <summary>
                                <Workflow size={13} />
                                {agentResponse.trace.length} tool{" "}
                                {agentResponse.trace.length === 1
                                  ? "step"
                                  : "steps"}{" "}
                                returned
                                <ChevronDown size={13} />
                              </summary>
                              <ol>
                                {agentResponse.trace.map((step, i) => (
                                  <li key={i}>
                                    <span
                                      className={`trace-dot ${step.status === "error" ? "error" : ""}`}
                                    >
                                      {step.status === "complete" ? (
                                        <Check size={10} />
                                      ) : (
                                        <X size={10} />
                                      )}
                                    </span>
                                    <div>
                                      <strong title={step.tool}>
                                        {toolLabels[step.tool] ??
                                          step.tool.replaceAll("_", " ")}
                                      </strong>
                                      <p>{step.summary}</p>
                                    </div>
                                  </li>
                                ))}
                              </ol>
                            </details>
                          )}
                          {agentResponse.proposedPlan && agentBase && (
                            <div className="proposal-box">
                              <span className="eyebrow">
                                {proposalApplied
                                  ? "APPLIED TO INPUTS"
                                  : "PROPOSED CHANGES · YOUR REVIEW"}
                              </span>
                              <ProposalDiff
                                before={agentBase}
                                after={agentResponse.proposedPlan}
                              />
                              {fingerprint(agentBase) !== fingerprint(plan) &&
                                !proposalApplied && (
                                  <p className="proposal-caution">
                                    Your inputs changed after this request. Ask
                                    the assistant again with your current plan
                                    before applying a proposal.
                                  </p>
                                )}
                              {agentResponse.result && (
                                <p className="proposal-result">
                                  Schedule check:{" "}
                                  <strong>{agentResponse.result.status}</strong>{" "}
                                  · {agentResponse.result.explanation}
                                </p>
                              )}
                              <button
                                className="primary"
                                onClick={applyProposal}
                                disabled={
                                  proposalApplied ||
                                  optimizing ||
                                  fingerprint(agentBase) !== fingerprint(plan)
                                }
                              >
                                {proposalApplied ? (
                                  <Check size={14} />
                                ) : (
                                  <ArrowDownToLine size={14} />
                                )}{" "}
                                {proposalApplied
                                  ? "Applied — review the plan above"
                                  : "Apply reviewed changes"}
                              </button>
                              <small>
                                This updates the planner. Acceptance is a
                                separate decision.
                              </small>
                            </div>
                          )}
                        </div>
                      )}
                      <form
                        className="assistant-form"
                        onSubmit={(e) => {
                          e.preventDefault();
                          void sendAgent();
                        }}
                      >
                        <textarea
                          ref={agentRef}
                          aria-label="Message the planning assistant"
                          placeholder="Try: Garden maintenance can only start after 13:00. Replan the other jobs."
                          value={agentInput}
                          onChange={(e) => setAgentInput(e.target.value)}
                          maxLength={2000}
                          rows={2}
                          disabled={agentBusy}
                        />
                        <button
                          className="send-button"
                          type="submit"
                          disabled={agentBusy || !agentInput.trim()}
                          aria-label="Send message to planning assistant"
                        >
                          {agentBusy ? (
                            <LoaderCircle size={18} className="spin" />
                          ) : (
                            <Send size={17} />
                          )}
                        </button>
                      </form>
                      <div className="assistant-footer">
                        <span>
                          <ShieldCheck size={12} /> Suggestions need your
                          approval.
                        </span>
                        <button
                          className="text-button"
                          onClick={async () => {
                            try {
                              setHealth(await request<Health>("/api/health"));
                              setNotice("Service status refreshed.");
                            } catch (e) {
                              setAgentError(errorText(e));
                            }
                          }}
                        >
                          <RefreshCw size={11} /> Refresh status
                        </button>
                      </div>
                    </section>
                    {result && (
                      <section className="evidence-panel" id="evidence">
                        <div className="section-heading">
                          <div>
                            <ShieldCheck size={17} />
                            <h2>Nothing hidden in the numbers.</h2>
                          </div>
                          <button className="text-button" onClick={exportJSON}>
                            Export evidence <ArrowUpRight size={13} />
                          </button>
                        </div>
                        <div className="checks">
                          {(result.constraintChecks ?? []).map((check, i) => (
                            <span
                              className={check.passed ? "passed" : "failed"}
                              key={i}
                            >
                              {check.passed ? (
                                <Check size={13} />
                              ) : (
                                <X size={13} />
                              )}{" "}
                              {check.label}
                            </span>
                          ))}
                        </div>
                        <details className="provenance">
                          <summary>
                            Weather source & how to read this plan{" "}
                            <ChevronDown size={15} />
                          </summary>
                          <div className="provenance-content">
                            <dl>
                              <div>
                                <dt>Provider</dt>
                                <dd>
                                  {result.weather?.source} ·{" "}
                                  {result.weather?.mode === "saved"
                                    ? "date-matched saved response"
                                    : "live response"}
                                </dd>
                              </div>
                              <div>
                                <dt>Retrieved</dt>
                                <dd>
                                  {result.weather?.fetchedAt
                                    ? new Date(
                                        result.weather.fetchedAt,
                                      ).toLocaleString("en-IN", {
                                        timeZone: "Asia/Kolkata",
                                      })
                                    : "Not provided"}{" "}
                                  IST
                                </dd>
                              </div>
                              <div>
                                <dt>Forecast grid</dt>
                                <dd>
                                  {result.weather?.gridLatitude},{" "}
                                  {result.weather?.gridLongitude}
                                </dd>
                              </div>
                              <div>
                                <dt>Attribution</dt>
                                <dd>{result.weather?.attribution}</dd>
                              </div>
                            </dl>
                            <p>
                              Average apparent temperature is weighted by
                              scheduled work duration. “At or above threshold”
                              counts scheduled work minutes at or above your
                              chosen planning marker. These are forecast-based
                              comparisons, not measured worker exposure, reduced
                              illness, or a guarantee of safe conditions. Follow
                              applicable workplace guidance and the supervisor’s
                              judgment.
                            </p>
                            {result.weather?.warnings?.map((warning, i) => (
                              <p className="inline-warning" key={i}>
                                <TriangleAlert size={13} />
                                {warning}
                              </p>
                            ))}
                            {result.weather?.sourceUrl && (
                              <a
                                href={result.weather.sourceUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="text-link"
                              >
                                Open weather source <ExternalLink size={12} />
                              </a>
                            )}
                          </div>
                        </details>
                      </section>
                    )}
                  </div>
                </div>
              </>
            ) : !loading ? (
              <div className="panel result-empty">
                <CloudSun size={35} />
                <h3>
                  The workspace is ready. The service isn’t connected yet.
                </h3>
                <p>
                  Start the planning service to load the editable scenario and
                  real forecast. No sample weather or agent results are
                  substituted.
                </p>
                <button className="primary" onClick={() => void loadDemo()}>
                  <RefreshCw size={15} />
                  Try connecting again
                </button>
              </div>
            ) : (
              <div className="page-loading">
                <LoaderCircle className="spin" />
                Preparing your workspace…
              </div>
            )}
            <footer className="page-footer">
              <span>
                <Leaf size={13} /> HeatShift · Plan around the heat.
              </span>
              <button
                className="text-button"
                onClick={() => setShowHistory(!showHistory)}
              >
                <Clock3 size={13} /> {showHistory ? "Hide" : "View"} locally
                accepted plan
              </button>
              <span>Forecasts inform. People decide.</span>
            </footer>
            {showHistory && (
              <div className="panel history-panel">
                <h3>Saved in this browser</h3>
                {accepted ? (
                  <>
                    <p>
                      {prettyDate(accepted.result.request.date)} ·{" "}
                      {accepted.result.request.location.name} ·{" "}
                      {accepted.result.schedule.length} tasks
                    </p>
                    <span>
                      Accepted{" "}
                      {new Date(accepted.at).toLocaleString("en-IN", {
                        timeZone: "Asia/Kolkata",
                      })}{" "}
                      IST. This is local browser storage, not a server audit
                      log.
                    </span>
                    <button
                      className="text-button"
                      onClick={() => {
                        setPlan(accepted.result.request);
                        setResult(accepted.result);
                        setLastRunFailed(false);
                        setNotice(
                          "Loaded the locally accepted plan. Its saved forecast may no longer be current; run the planner to refresh.",
                        );
                        setShowHistory(false);
                      }}
                    >
                      Load saved plan <ArrowRight size={13} />
                    </button>
                  </>
                ) : (
                  <p>No plan has been accepted in this browser yet.</p>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
      {result && (
        <div className="print-report">
          <Brand />
          <h1>Campus work plan</h1>
          <p>
            {prettyDate(result.request.date)} · {result.request.location.name} ·{" "}
            {result.request.shiftStart}–{result.request.shiftEnd} IST
          </p>
          <p>
            {acceptedCurrent ? "Accepted locally" : "Draft · not accepted"} ·
            Exported{" "}
            {new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}{" "}
            IST
          </p>
          <h2>Forecast-based comparison</h2>
          <p>{result.explanation}</p>
          <p>
            Work: {result.metrics?.workMinutes} minutes. Original mean:{" "}
            {result.baselineValid
              ? number(result.metrics?.baselineMeanApparentTemperatureC, "°C")
              : "invalid baseline"}
            . Proposed mean:{" "}
            {number(result.metrics?.proposedMeanApparentTemperatureC, "°C")}. At
            or above {result.metrics?.thresholdC}°C:{" "}
            {result.metrics?.proposedHotMinutes ?? "—"} minutes.
          </p>
          <table>
            <thead>
              <tr>
                <th>Task</th>
                <th>Time</th>
                <th>Duration</th>
                <th>Locked</th>
              </tr>
            </thead>
            <tbody>
              {result.schedule.map((t) => (
                <tr key={t.taskId}>
                  <td>{t.title}</td>
                  <td>
                    {t.start}–{t.end}
                  </td>
                  <td>{minutes(t.end) - minutes(t.start)} min</td>
                  <td>{t.locked ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>
            Protected breaks:{" "}
            {result.request.breaks
              .map((b) => `${b.start}–${b.end}`)
              .join(", ") || "none"}
            .
          </p>
          <h2>Constraints checked</h2>
          <ul>
            {result.constraintChecks?.map((c, i) => (
              <li key={i}>
                {c.passed ? "PASS" : "FAIL"}: {c.label}
              </li>
            ))}
          </ul>
          <h2>Source and limitations</h2>
          <p>
            {result.weather?.source} · {result.weather?.mode} response ·
            Forecast date {result.weather?.date} · Retrieved{" "}
            {result.weather?.fetchedAt} · Grid {result.weather?.gridLatitude},{" "}
            {result.weather?.gridLongitude}
          </p>
          <p>{result.weather?.sourceUrl}</p>
          <p>{result.weather?.attribution}</p>
          <p>{result.weather?.warnings?.join(" ")}</p>
          <p>
            Apparent temperature and comparisons are forecast estimates. They
            are not measured worker exposure, health improvements or a safety
            guarantee. The threshold is a user-defined planning indicator. Human
            supervision and applicable workplace rules remain necessary.
          </p>
          <p>
            Illustrative scenario unless replaced with your own operating
            inputs. Acceptance is stored in this browser only.
          </p>
        </div>
      )}
    </>
  );
}
