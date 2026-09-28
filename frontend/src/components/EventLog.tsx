export interface LogEntry {
  id: number;
  time: string;
  kind: "info" | "ok" | "warn" | "err" | "net";
  text: string;
}

export function EventLog({ entries, connected }: { entries: LogEntry[]; connected: boolean }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <div className="label">Request log · Redis + FastAPI + Postgres</div>
        <span className={`pill ${connected ? "green" : "grey"}`}>
          <span className="dot" /> {connected ? "WS live" : "WS offline"}
        </span>
      </div>
      <div className="log" aria-live="polite">
        {entries.length === 0 ? (
          <div className="log-line info">
            <time>--:--:--</time>
            <span>idle — pick seats, or open this match in a second tab to watch locks propagate.</span>
          </div>
        ) : (
          entries.map((e) => (
            <div key={e.id} className={`log-line ${e.kind}`}>
              <time>{e.time}</time>
              <span>{e.text}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
