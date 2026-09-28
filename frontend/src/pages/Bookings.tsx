import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Payment } from "../api";
import { matchDate, money } from "../format";

const PILL: Record<string, string> = { SUCCESS: "green", PENDING: "blue", FAILED: "red" };

export default function Bookings() {
  const [bookings, setBookings] = useState<Payment[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .myBookings()
      .then(setBookings)
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed to load bookings");
        setBookings([]);
      });
  }, []);

  const confirmed = bookings?.filter((b) => b.status === "SUCCESS") ?? [];
  const spent = confirmed.reduce((sum, b) => sum + (b.amount ?? 0), 0);

  return (
    <>
      <section className="match-head">
        <div>
          <div className="eyebrow">
            Account <span className="rule" /> Bookings
          </div>
          <h1>My bookings</h1>
          <div className="muted mono" style={{ fontSize: 13 }}>
            {confirmed.length} confirmed · {confirmed.reduce((n, b) => n + b.seats.length, 0)} seats · {money(spent)}
          </div>
        </div>
      </section>

      {error && <p className="error">{error}</p>}

      <div className="panel">
        {bookings === null ? (
          <div className="skeleton" style={{ border: 0 }} />
        ) : bookings.length === 0 ? (
          <div className="empty">
            <p>No bookings yet.</p>
            <Link to="/" className="btn primary">
              Find a match
            </Link>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>Match</th>
                  <th>Seats</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Payment ID</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {bookings.map((b) => (
                  <tr key={b.payment_id}>
                    <td>
                      <Link to={`/match/${b.match_id}`} style={{ color: "var(--accent)" }}>
                        {b.match ? `${b.match.team1} v ${b.match.team2}` : `#${b.match_id}`}
                      </Link>
                      {b.match && (
                        <div className="muted" style={{ fontSize: 11, marginTop: 3 }}>
                          {matchDate(b.match.date)}
                        </div>
                      )}
                    </td>
                    <td>{b.seats.join(", ")}</td>
                    <td>{money(b.amount)}</td>
                    <td>
                      <span className={`pill ${PILL[b.status] ?? "grey"}`}>
                        <span className="dot" /> {b.status}
                      </span>
                    </td>
                    <td className="muted" title={b.payment_id}>
                      {b.payment_id.slice(0, 8)}…
                    </td>
                    <td className="muted">{new Date(b.created_at + "Z").toLocaleString("en-IN")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
