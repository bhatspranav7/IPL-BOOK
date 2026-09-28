import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, type Match, type Payment, type Pricing, type Seat } from "../api";
import { useAuth } from "../auth";
import { Crest } from "../components/Crest";
import { EventLog, type LogEntry } from "../components/EventLog";
import { PricePanel } from "../components/PricePanel";
import { RaceLab } from "../components/RaceLab";
import { SeatGrid } from "../components/SeatGrid";
import { useToast } from "../components/Toast";
import { clock, matchDate, money, timeStamp } from "../format";
import { useEvents, type LiveEvent } from "../useEvents";

type Phase = "select" | "locked" | "pending" | "success" | "failed" | "expired";

const MAX_SEATS = 6;
const EVENT_TEXT: Record<string, string> = {
  seats_locked: "locked",
  seats_released: "released",
  payment_pending: "started payment for",
  seats_booked: "booked",
  payment_failed: "payment failed for",
};

let logId = 1;

export default function MatchPage() {
  const matchId = Number(useParams().id);
  const { user } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const [match, setMatch] = useState<Match | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [seats, setSeats] = useState<Seat[]>([]);
  const [pricing, setPricing] = useState<Pricing | null>(null);

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [held, setHeld] = useState<string[]>([]);
  const [phase, setPhase] = useState<Phase>("select");
  const [payment, setPayment] = useState<Payment | null>(null);
  const [expiresAt, setExpiresAt] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const [busy, setBusy] = useState(false);
  const [aiCount, setAiCount] = useState(2);

  const [log, setLog] = useState<LogEntry[]>([]);
  const [flashing, setFlashing] = useState<Set<string>>(new Set());
  const refreshTimer = useRef<number>();

  const addLog = useCallback((kind: LogEntry["kind"], text: string) => {
    setLog((l) => [{ id: logId++, time: timeStamp(), kind, text }, ...l].slice(0, 80));
  }, []);

  const refreshSeats = useCallback(async () => {
    try {
      setSeats(await api.seats(matchId));
    } catch {
      /* transient; next event or poll retries */
    }
  }, [matchId]);

  const refreshPrice = useCallback(async () => {
    try {
      setPricing(await api.price(matchId));
    } catch {
      setPricing(null);
    }
  }, [matchId]);

  const scheduleRefresh = useCallback(() => {
    window.clearTimeout(refreshTimer.current);
    refreshTimer.current = window.setTimeout(refreshSeats, 120);
  }, [refreshSeats]);

  // Initial load
  useEffect(() => {
    if (!Number.isFinite(matchId)) {
      setNotFound(true);
      return;
    }
    api
      .match(matchId)
      .then(setMatch)
      .catch(() => setNotFound(true));
    refreshSeats();
    refreshPrice();
  }, [matchId, refreshSeats, refreshPrice, user]);

  // Locks expire silently in Redis, so poll as a safety net for other users' TTLs
  useEffect(() => {
    const t = window.setInterval(refreshSeats, 10000);
    return () => window.clearInterval(t);
  }, [refreshSeats]);

  // Countdown ticker
  useEffect(() => {
    if (!expiresAt) return;
    const t = window.setInterval(() => setNow(Date.now()), 250);
    return () => window.clearInterval(t);
  }, [expiresAt]);

  const remaining = expiresAt ? Math.max(0, (expiresAt - now) / 1000) : 0;

  useEffect(() => {
    if (expiresAt && remaining <= 0 && (phase === "locked" || phase === "pending")) {
      setPhase("expired");
      setExpiresAt(null);
      addLog("err", `lock TTL elapsed → Redis evicted ${held.join(", ")}`);
      refreshSeats();
    }
  }, [remaining, expiresAt, phase, held, addLog, refreshSeats]);

  const connected = useEvents((e: LiveEvent) => {
    if (e.match_id !== matchId) return;
    const who = user && e.user_id === user.id ? "you" : `user #${e.user_id}`;
    const verb = EVENT_TEXT[e.event] ?? e.event;
    const kind: LogEntry["kind"] =
      e.event === "seats_booked" ? "ok" : e.event === "payment_failed" ? "err" : e.event === "seats_locked" ? "warn" : "info";
    addLog(kind, `WS ← ${who} ${verb} ${e.seats.join(", ")}`);

    setFlashing(new Set(e.seats));
    window.setTimeout(() => setFlashing(new Set()), 900);
    scheduleRefresh();
    if (e.event === "seats_booked") refreshPrice();
  });

  const requireUser = () => {
    if (user) return true;
    navigate("/login", { state: { from: `/match/${matchId}` } });
    return false;
  };

  const run = async (label: string, fn: () => Promise<void>) => {
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      addLog("err", `${label} ✗ ${msg}`);
      toast(msg, "err");
      refreshSeats();
    } finally {
      setBusy(false);
    }
  };

  const toggle = (seat: string) => {
    if (phase !== "select") return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(seat)) next.delete(seat);
      else if (next.size < MAX_SEATS) next.add(seat);
      else toast(`Max ${MAX_SEATS} seats per booking`);
      return next;
    });
  };

  const lock = () =>
    requireUser() &&
    run("POST /booking/validate-seats", async () => {
      const list = [...selected];
      addLog("net", `POST /booking/validate-seats ${list.join(", ")}`);
      const res = await api.lockSeats(matchId, list);
      setHeld(res.seats);
      setExpiresAt(Date.now() + res.expires_in * 1000);
      setPhase("locked");
      addLog("warn", `SET lock:${matchId}:{${res.seats.join(",")}} NX EX ${res.expires_in} → OK`);
    });

  const release = () =>
    run("POST /booking/release", async () => {
      await api.releaseSeats(matchId, held);
      addLog("info", `DEL locks ${held.join(", ")} (owner check via Lua)`);
      reset();
      refreshSeats();
    });

  const initiate = () =>
    run("POST /payments/initiate-payment", async () => {
      addLog("net", "POST /payments/initiate-payment");
      const p = await api.initiatePayment(matchId, held);
      setPayment(p);
      setPhase("pending");
      if (p.expires_in) setExpiresAt(Date.now() + p.expires_in * 1000);
      addLog("info", `INSERT bookings status=PENDING payment_id=${p.payment_id.slice(0, 8)}… · lock TTL → ${p.expires_in}s`);
    });

  const confirm = () =>
    payment &&
    run("POST /payments/confirm-payment", async () => {
      addLog("net", "POST /payments/confirm-payment");
      const p = await api.confirmPayment(payment.payment_id);
      setPayment(p);
      setPhase("success");
      setExpiresAt(null);
      addLog("ok", `UPDATE seats SET is_booked=true WHERE is_booked=false → ${held.length} rows · SUCCESS`);
      toast(`Booked ${held.join(", ")}`, "ok");
      refreshSeats();
      refreshPrice();
    });

  const fail = () =>
    payment &&
    run("POST /payments/fail-payment", async () => {
      addLog("net", "POST /payments/fail-payment");
      const p = await api.failPayment(payment.payment_id);
      setPayment(p);
      setPhase("failed");
      setExpiresAt(null);
      addLog("err", `payment FAILED → locks released, ${held.join(", ")} back on sale`);
      refreshSeats();
    });

  const aiBook = () =>
    requireUser() &&
    run("POST /ai-book", async () => {
      addLog("net", `POST /ai-book/${matchId}?count=${aiCount}`);
      const res = await api.aiBook(matchId, aiCount);
      for (const t of res.trace) addLog(t.result === "locked" ? "warn" : "info", `agent tried ${t.seats.join(", ")} → ${t.result}`);
      addLog(
        "ok",
        `agent picked ${res.selected_seats.join(", ")} · score ${res.reasoning.score} (centre ${res.reasoning.centre_score}, row ${res.reasoning.row_score})`,
      );
      setSelected(new Set(res.selected_seats));
      setHeld(res.selected_seats);
      setPayment(res.booking_response);
      setPhase("pending");
      if (res.booking_response.expires_in) setExpiresAt(Date.now() + res.booking_response.expires_in * 1000);
      refreshSeats();
    });

  const reset = () => {
    setSelected(new Set());
    setHeld([]);
    setPayment(null);
    setExpiresAt(null);
    setPhase("select");
  };

  if (notFound) {
    return (
      <div className="panel empty" style={{ marginTop: 48 }}>
        <p>That match doesn't exist.</p>
        <Link to="/" className="btn">
          ← All matches
        </Link>
      </div>
    );
  }

  const price = pricing?.dynamic_price ?? 0;
  const count = phase === "select" ? selected.size : held.length;
  const total = payment?.amount ?? price * count;
  const stepIndex = { select: 0, locked: 1, expired: 1, pending: 2, failed: 3, success: 3 }[phase];
  const raceSeat = [...selected][0] ?? seats.find((s) => s.status === "AVAILABLE")?.seat ?? "A1";

  return (
    <>
      <section className="match-head">
        <div>
          <Link to="/" className="eyebrow">
            ← Matches <span className="rule" /> #{matchId}
          </Link>
          {match ? (
            <>
              <h1>
                {match.team1} v {match.team2}
              </h1>
              <div className="muted mono" style={{ fontSize: 13 }}>
                {match.stadium} · {matchDate(match.date)}
              </div>
            </>
          ) : (
            <h1>Loading…</h1>
          )}
        </div>
        {match && (
          <div className="fixture">
            <Crest team={match.team1} large />
            <span className="vs">VS</span>
            <Crest team={match.team2} large />
          </div>
        )}
      </section>

      <div className="match-layout">
        <div className="stack">
          <div className="panel">
            <div className="panel-head">
              <div className="label">Seat grid</div>
              <span className="pill amber">
                <span className="dot" /> Redis lock TTL
              </span>
            </div>
            <SeatGrid
              seats={seats}
              selected={phase === "select" ? selected : new Set(held)}
              flashing={flashing}
              interactive={phase === "select" && !busy}
              onToggle={toggle}
            />

            <div className="actions">
              {phase === "select" && (
                <>
                  <button className="btn primary" disabled={!selected.size || busy} onClick={lock}>
                    ▷ Lock {selected.size || ""} seat{selected.size === 1 ? "" : "s"}
                  </button>
                  <button className="btn" disabled={!selected.size || busy} onClick={() => setSelected(new Set())}>
                    ↺ Clear
                  </button>
                  <span style={{ flex: 1 }} />
                  <select
                    className="btn"
                    value={aiCount}
                    onChange={(e) => setAiCount(Number(e.target.value))}
                    aria-label="Seats for AI to pick"
                  >
                    {[1, 2, 3, 4].map((n) => (
                      <option key={n} value={n}>
                        {n} seat{n > 1 ? "s" : ""}
                      </option>
                    ))}
                  </select>
                  <button className="btn" disabled={busy} onClick={aiBook}>
                    ✦ AI pick best
                  </button>
                </>
              )}
            </div>
          </div>

          <PricePanel pricing={pricing} />
        </div>

        <div className="stack">
          <div className="panel">
            <div className="steps" aria-hidden="true">
              {[0, 1, 2, 3].map((i) => (
                <span key={i} className={i <= stepIndex ? "done" : ""} />
              ))}
            </div>
            <div className="panel-head">
              <div className="label">
                {
                  {
                    select: "01 · Select seats",
                    locked: "02 · Seats locked",
                    expired: "02 · Lock expired",
                    pending: "03 · Payment pending",
                    success: "04 · Booking confirmed",
                    failed: "04 · Payment failed",
                  }[phase]
                }
              </div>
              {(phase === "locked" || phase === "pending") && expiresAt && (
                <span className={`timer${remaining < 20 ? " urgent" : ""}`}>
                  <span className="dot" /> {clock(remaining)}
                </span>
              )}
            </div>

            {phase === "success" ? (
              <div className="result">
                <span className="pill green">
                  <span className="dot" /> SUCCESS
                </span>
                <div className="big">You're going to the match.</div>
                <p className="muted mono" style={{ fontSize: 12 }}>
                  {held.join(", ")} · {money(payment?.amount)} · {payment?.payment_id.slice(0, 8)}
                </p>
                <div className="actions" style={{ justifyContent: "center" }}>
                  <Link to="/bookings" className="btn">
                    My bookings
                  </Link>
                  <button className="btn primary" onClick={reset}>
                    Book more
                  </button>
                </div>
              </div>
            ) : phase === "failed" || phase === "expired" ? (
              <div className="result">
                <span className="pill red">
                  <span className="dot" /> {phase === "failed" ? "PAYMENT_FAILED" : "LOCK_EXPIRED"}
                </span>
                <div className="big">{phase === "failed" ? "Payment didn't go through." : "Your hold ran out."}</div>
                <p className="muted" style={{ fontSize: 14 }}>
                  The Redis locks were released so other fans can book {held.join(", ")}.
                </p>
                <button className="btn primary" onClick={reset}>
                  Start over
                </button>
              </div>
            ) : (
              <>
                <div className="checkout-seats">
                  {count ? (
                    (phase === "select" ? [...selected] : held).map((s) => (
                      <span key={s} className="chip">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="muted" style={{ fontSize: 14 }}>
                      Tap seats on the grid (max {MAX_SEATS}).
                    </span>
                  )}
                </div>
                <div className="line">
                  <span>
                    {count} × {money(payment?.price_per_seat ?? price)}
                  </span>
                  <span>{money(total)}</span>
                </div>
                <div className="line total">
                  <span>Total</span>
                  <span>{money(total)}</span>
                </div>

                <div className="actions">
                  {phase === "locked" && (
                    <>
                      <button className="btn primary" disabled={busy} onClick={initiate}>
                        Proceed to pay
                      </button>
                      <button className="btn" disabled={busy} onClick={release}>
                        Release
                      </button>
                    </>
                  )}
                  {phase === "pending" && (
                    <>
                      <button className="btn primary" disabled={busy} onClick={confirm}>
                        Pay {money(total)}
                      </button>
                      <button className="btn danger" disabled={busy} onClick={fail}>
                        Simulate failure
                      </button>
                    </>
                  )}
                  {phase === "select" && (
                    <p className="muted" style={{ fontSize: 13, margin: 0 }}>
                      {user ? "Locking holds seats for 2 minutes." : "Sign in to lock seats."}
                    </p>
                  )}
                </div>
                {phase === "pending" && (
                  <p className="formula">Demo gateway: no real money moves. Pay confirms, Simulate failure rolls back.</p>
                )}
              </>
            )}
          </div>

          <EventLog entries={log} connected={connected} />
          <RaceLab matchId={matchId} seat={raceSeat} />
        </div>
      </div>
    </>
  );
}
