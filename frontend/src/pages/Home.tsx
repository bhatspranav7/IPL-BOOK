import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Health, type Match } from "../api";
import { useAuth } from "../auth";
import { Crest } from "../components/Crest";
import { matchDate, money } from "../format";
import { useEvents } from "../useEvents";

export default function Home() {
  const { user } = useAuth();
  const [matches, setMatches] = useState<Match[] | null>(null);
  const [prices, setPrices] = useState<Record<number, number>>({});
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const list = await api.matches();
      setMatches(list);
      setError(null);
      const entries = await Promise.all(
        list.slice(0, 24).map((m) =>
          api
            .price(m.id)
            .then((p) => [m.id, p.dynamic_price] as const)
            .catch(() => null),
        ),
      );
      setPrices(Object.fromEntries(entries.filter((e): e is readonly [number, number] => e !== null)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load matches");
      setMatches([]);
    }
  }, []);

  useEffect(() => {
    load();
    api.health().then(setHealth).catch(() => setHealth(null));
  }, [load]);

  const live = useEvents((e) => {
    if (e.event === "seats_booked") load();
  });

  return (
    <>
      <section className="hero">
        <div>
          <div className="eyebrow">
            IPL 2026 <span className="rule" /> <span className="dot live" /> {live ? "Live" : "Connecting"}
          </div>
          <h1>Book the match.<br />Never the same seat twice.</h1>
          <p>
            Seats are locked in Redis the moment you pick them, paid for in two phases, and priced by a
            demand model that reacts to how fast the stadium fills.
          </p>
        </div>
        {health && (
          <div className="status-strip">
            <span className={`pill ${health.database === "postgres" ? "green" : "red"}`}>
              <span className="dot" /> {health.database}
            </span>
            <span className={`pill ${health.lock_backend === "redis" ? "cyan" : "amber"}`}>
              <span className="dot" /> locks: {health.lock_backend}
            </span>
            <span className={`pill ${health.kafka === "enabled" ? "cyan" : "grey"}`}>
              <span className="dot" /> kafka: {health.kafka}
            </span>
          </div>
        )}
      </section>

      <div className="panel-head">
        <div className="label">Upcoming fixtures · {matches?.length ?? "…"}</div>
        {user?.is_admin && (
          <Link to="/admin" className="btn small">
            + New match
          </Link>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {matches === null ? (
        <div className="match-grid">
          {[0, 1, 2].map((i) => (
            <div key={i} className="skeleton" />
          ))}
        </div>
      ) : matches.length === 0 ? (
        <div className="panel empty">
          <p>No matches scheduled yet.</p>
          {user?.is_admin ? (
            <Link to="/admin" className="btn primary">
              Create the first match
            </Link>
          ) : !user ? (
            <Link to="/login" className="btn primary">
              Sign in to get started
            </Link>
          ) : null}
        </div>
      ) : (
        <div className="match-grid">
          {matches.map((m) => {
            const sold = m.total_seats ? (m.total_seats - m.available_seats) / m.total_seats : 0;
            return (
              <Link key={m.id} to={`/match/${m.id}`} className="panel match-card">
                <div className="meta-row">
                  <span>MATCH #{m.id}</span>
                  <span>{matchDate(m.date)}</span>
                </div>
                <div className="fixture">
                  <Crest team={m.team1} />
                  <span className="vs">VS</span>
                  <Crest team={m.team2} />
                  <div>
                    <div className="fixture-names">
                      {m.team1} v {m.team2}
                    </div>
                    <div className="muted" style={{ fontSize: 14, marginTop: 2 }}>
                      {m.stadium}
                    </div>
                  </div>
                </div>
                <div>
                  <div className="bar">
                    <span style={{ width: `${sold * 100}%` }} />
                  </div>
                  <div className="meta-row" style={{ marginTop: 8 }}>
                    <span>
                      {m.available_seats}/{m.total_seats} left
                    </span>
                    <span>{Math.round(sold * 100)}% sold</span>
                  </div>
                </div>
                <div className="card-foot">
                  <div>
                    <div className="label">Dynamic price</div>
                    <div className="price-big">{money(prices[m.id])}</div>
                  </div>
                  <span className="btn small">{m.available_seats ? "Pick seats →" : "Sold out"}</span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </>
  );
}
