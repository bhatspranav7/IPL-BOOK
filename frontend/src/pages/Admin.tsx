import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { useToast } from "../components/Toast";

const TEAMS = ["CSK", "MI", "RCB", "KKR", "SRH", "DC", "PBKS", "RR", "GT", "LSG"];
const STADIUMS = [
  "M. Chinnaswamy Stadium, Bengaluru",
  "Wankhede Stadium, Mumbai",
  "M. A. Chidambaram Stadium, Chennai",
  "Eden Gardens, Kolkata",
  "Narendra Modi Stadium, Ahmedabad",
  "Arun Jaitley Stadium, Delhi",
];

function inDays(n: number) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export default function Admin() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const [team1, setTeam1] = useState("RCB");
  const [team2, setTeam2] = useState("CSK");
  const [stadium, setStadium] = useState(STADIUMS[0]);
  const [date, setDate] = useState(inDays(7));
  const [seats, setSeats] = useState(50);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user && !user.is_admin) return <Navigate to="/" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api.createMatch({ team1, team2, stadium, date, seats });
      toast(`Match #${res.match_id} created with ${seats} seats`, "ok");
      navigate(`/match/${res.match_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create match");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ maxWidth: 640, margin: "0 auto" }}>
      <section className="match-head">
        <div>
          <div className="eyebrow">
            Admin <span className="rule" /> Inventory
          </div>
          <h1>Create a match</h1>
          <div className="muted" style={{ fontSize: 15 }}>
            Seats are generated automatically in rows of 10 (A1…A10, B1…).
          </div>
        </div>
      </section>

      <form className="panel" onSubmit={submit}>
        <datalist id="teams">
          {TEAMS.map((t) => (
            <option key={t} value={t} />
          ))}
        </datalist>
        <datalist id="stadiums">
          {STADIUMS.map((s) => (
            <option key={s} value={s} />
          ))}
        </datalist>

        <div className="form-grid">
          <label className="field">
            <span className="label">Home team</span>
            <input list="teams" value={team1} onChange={(e) => setTeam1(e.target.value)} required maxLength={40} />
          </label>
          <label className="field">
            <span className="label">Away team</span>
            <input list="teams" value={team2} onChange={(e) => setTeam2(e.target.value)} required maxLength={40} />
          </label>
        </div>
        <label className="field">
          <span className="label">Stadium</span>
          <input list="stadiums" value={stadium} onChange={(e) => setStadium(e.target.value)} required maxLength={80} />
        </label>
        <div className="form-grid">
          <label className="field">
            <span className="label">Date</span>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </label>
          <label className="field">
            <span className="label">Seats (1–260)</span>
            <input
              type="number"
              min={1}
              max={260}
              value={seats}
              onChange={(e) => setSeats(Number(e.target.value))}
              required
            />
          </label>
        </div>
        {error && <p className="error">{error}</p>}
        <button className="btn primary block" disabled={busy}>
          {busy ? "Creating…" : "Create match + seats"}
        </button>
      </form>
    </div>
  );
}
