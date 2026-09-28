import { useState } from "react";
import { api, type RaceResult } from "../api";

export function RaceLab({ matchId, seat }: { matchId: number; seat: string }) {
  const [result, setResult] = useState<RaceResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      setResult(await api.race(matchId, seat));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Race failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="panel">
      <div className="panel-head">
        <div className="label">Lab · lock race</div>
        <button className="btn small primary" onClick={run} disabled={busy}>
          {busy ? "Racing…" : `▷ Run race → ${seat}`}
        </button>
      </div>
      <p className="muted" style={{ margin: 0, fontSize: 14, lineHeight: 1.55 }}>
        Two threads call <span className="mono">SET NX EX</span> on the same seat key at the same instant. Exactly one
        wins; that is the whole double-booking defence. Uses a sandbox key, so real seats are untouched.
      </p>
      {error && <p className="error">{error}</p>}
      {result && (
        <>
          <div className="race-grid">
            {result.contenders.map((c) => (
              <div key={c.user} className={`racer ${c.acquired ? "win" : "lose"}`}>
                <div style={{ color: c.acquired ? "var(--success)" : "var(--failed)" }}>
                  {c.acquired ? "✓ LOCK ACQUIRED" : "✗ REJECTED"}
                </div>
                <div className="muted" style={{ marginTop: 6 }}>
                  {c.user} · {c.latency_ms} ms
                </div>
              </div>
            ))}
          </div>
          <p className="formula">
            backend: {result.lock_backend} · winner: {result.winner} · exactly one winner:{" "}
            {String(result.exactly_one_winner)}
          </p>
        </>
      )}
    </div>
  );
}
