const FLOW = [
  {
    title: "Select & lock",
    body: "POST /booking/validate-seats checks Postgres, then SET lock:{match}:{seat} <user> NX EX 120 in Redis. Exactly one concurrent caller wins each seat.",
  },
  {
    title: "Initiate payment",
    body: "Verifies the caller still owns every lock, prices seats with the demand model, writes a PENDING booking and extends the lock TTL to 5 minutes.",
  },
  {
    title: "Confirm",
    body: "UPDATE seats SET is_booked = true WHERE is_booked = false. If the row count is short, the transaction rolls back, so a lost lock still can't double-book.",
  },
  {
    title: "Release & broadcast",
    body: "Locks are deleted with an owner-checked Lua script. Every state change goes to Kafka and is pushed over WebSockets to every open seat map.",
  },
];

const STACK = [
  ["FastAPI", "REST + WebSocket API, JWT auth"],
  ["PostgreSQL", "Users, matches, seats, bookings, audit log"],
  ["Redis", "Distributed seat locks with TTL"],
  ["scikit-learn", "Gradient-boosted demand model for pricing"],
  ["Kafka", "Booking event stream (optional)"],
  ["React + Vite", "This UI, served by FastAPI in production"],
];

const GUARANTEES = [
  ["Race conditions", "Redis SET NX is atomic, and the Lab panel on every match page proves it live."],
  ["Lock theft", "Lock value is the user id; release and payment both check ownership."],
  ["Lost locks", "Conditional UPDATE in Postgres is the second line of defence."],
  ["Abandoned carts", "TTL evicts locks automatically; seats return to sale with no cleanup job."],
  ["Payment tampering", "Confirm / fail / status all require the JWT of the booking owner."],
];

export default function Architecture() {
  return (
    <>
      <section className="hero" style={{ gridTemplateColumns: "1fr" }}>
        <div>
          <div className="eyebrow">
            System <span className="rule" /> Design
          </div>
          <h1>How a seat gets sold exactly once.</h1>
          <p>
            The hardest part of a booking system isn't booking. It's what happens when two people press the button at the
            same instant.
          </p>
        </div>
      </section>

      <div className="flow">
        {FLOW.map((s, i) => (
          <div key={s.title} className="panel flow-step">
            <div className="n">0{i + 1}</div>
            <h3>{s.title}</h3>
            <p>{s.body}</p>
          </div>
        ))}
      </div>

      <h2 className="section-title">State machine</h2>
      <div className="panel mono" style={{ fontSize: 13, lineHeight: 2, overflowX: "auto", whiteSpace: "nowrap" }}>
        <span className="pill grey">AVAILABLE</span> → <span className="pill amber">LOCKED</span> →{" "}
        <span className="pill blue">PAYMENT_PENDING</span> → <span className="pill green">SUCCESS</span>
        <br />
        <span className="muted">
          LOCKED / PENDING ─ TTL expires or payment fails →
        </span>{" "}
        <span className="pill red">FAILED</span> → <span className="pill grey">AVAILABLE</span>
      </div>

      <h2 className="section-title">What it defends against</h2>
      <div className="panel table-scroll">
        <table className="table">
          <tbody>
            {GUARANTEES.map(([k, v]) => (
              <tr key={k}>
                <td style={{ whiteSpace: "nowrap", color: "var(--accent)" }}>{k}</td>
                <td className="muted" style={{ fontFamily: "var(--sans)", fontSize: 15 }}>
                  {v}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="section-title">Stack</h2>
      <div className="stack-grid">
        {STACK.map(([name, role]) => (
          <div key={name} className="panel">
            <div className="label" style={{ color: "var(--accent)" }}>
              {name}
            </div>
            <div style={{ marginTop: 8, fontSize: 15 }}>{role}</div>
          </div>
        ))}
      </div>

      <p className="formula" style={{ marginTop: 32 }}>
        API reference: <a href="/docs" style={{ color: "var(--accent)" }}>/docs</a> (Swagger)
      </p>
    </>
  );
}
