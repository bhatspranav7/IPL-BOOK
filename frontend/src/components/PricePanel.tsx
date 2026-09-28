import { useEffect, useState } from "react";
import { api, type Pricing } from "../api";
import { hoursLabel, money } from "../format";

export function PricePanel({ pricing }: { pricing: Pricing | null }) {
  const [occupancy, setOccupancy] = useState(0);
  const [hours, setHours] = useState(24);
  const [touched, setTouched] = useState(false);
  const [whatIf, setWhatIf] = useState<{ demand_score: number; dynamic_price: number } | null>(null);

  // Seed the what-if sliders from live data until the user drags them
  useEffect(() => {
    if (pricing && !touched) {
      setOccupancy(pricing.occupancy);
      setHours(Math.min(Math.round(pricing.time_to_match_hours), 720));
    }
  }, [pricing, touched]);

  useEffect(() => {
    if (!touched) return;
    const t = window.setTimeout(() => {
      api.simulatePrice(occupancy, hours).then(setWhatIf).catch(() => setWhatIf(null));
    }, 150);
    return () => window.clearTimeout(t);
  }, [occupancy, hours, touched]);

  if (!pricing) return <div className="panel skeleton" style={{ minHeight: 220 }} />;

  const shown = touched && whatIf ? whatIf : pricing;

  return (
    <div className="panel">
      <div className="panel-head">
        <div className="label">Dynamic pricing · demand model</div>
        <span className={`pill ${touched ? "amber" : "cyan"}`}>
          <span className="dot" /> {touched ? "What-if" : "Live"}
        </span>
      </div>

      <div className="stats">
        <div className="stat">
          <div className="label">Seats left</div>
          <div className="value">
            {pricing.seats_remaining}/{pricing.total_seats}
          </div>
        </div>
        <div className="stat">
          <div className="label">Demand</div>
          <div className="value">{shown.demand_score.toFixed(2)}</div>
        </div>
        <div className="stat">
          <div className="label">Price / seat</div>
          <div className="value accent">{money(shown.dynamic_price)}</div>
        </div>
      </div>

      <div className="divider" />

      <div className="form-grid">
        <label className="field">
          <span className="label">
            Occupancy · {Math.round(occupancy * 100)}%
          </span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={occupancy}
            onChange={(e) => {
              setTouched(true);
              setOccupancy(Number(e.target.value));
            }}
          />
        </label>
        <label className="field">
          <span className="label">Time to match · {hoursLabel(hours)}</span>
          <input
            type="range"
            min={0}
            max={720}
            step={1}
            value={hours}
            onChange={(e) => {
              setTouched(true);
              setHours(Number(e.target.value));
            }}
          />
        </label>
      </div>

      {touched && (
        <button className="btn small ghost" onClick={() => setTouched(false)}>
          Reset to live
        </button>
      )}

      <p className="formula">
        price = {money(pricing.base_price)} × (1 + demand) · demand = GBM(occupancy, hours_to_match, hour, weekday)
        {pricing.model_mae != null && ` · test MAE ${pricing.model_mae}`}
      </p>
    </div>
  );
}
