import { useMemo } from "react";
import type { Seat } from "../api";

interface Props {
  seats: Seat[];
  selected: Set<string>;
  flashing: Set<string>;
  interactive: boolean;
  onToggle: (seat: string) => void;
}

const SEAT_RE = /^([A-Z]+)(\d+)$/;

export function SeatGrid({ seats, selected, flashing, interactive, onToggle }: Props) {
  const rows = useMemo(() => {
    const map = new Map<string, Seat[]>();
    for (const s of seats) {
      const m = SEAT_RE.exec(s.seat);
      const row = m ? m[1] : "?";
      if (!map.has(row)) map.set(row, []);
      map.get(row)!.push(s);
    }
    for (const list of map.values()) {
      list.sort((a, b) => Number(SEAT_RE.exec(a.seat)?.[2]) - Number(SEAT_RE.exec(b.seat)?.[2]));
    }
    return [...map.entries()];
  }, [seats]);

  return (
    <>
      <div className="pitch">PITCH · THIS WAY</div>
      <div className="seat-grid" role="grid" aria-label="Seat map">
        {rows.map(([row, list]) => (
          <div key={row} role="row" style={{ display: "contents" }}>
            <span className="row-label">{row}</span>
            {Array.from({ length: 10 }, (_, i) => {
              const seat = list.find((s) => Number(SEAT_RE.exec(s.seat)?.[2]) === i + 1);
              if (!seat) return <span key={i} />;

              const isSelected = selected.has(seat.seat);
              const blocked = seat.status === "BOOKED" || (seat.status === "LOCKED" && !seat.mine);
              const cls = [
                "seat",
                seat.status === "BOOKED" && "booked",
                seat.status === "LOCKED" && (seat.mine ? "mine" : "locked"),
                isSelected && seat.status === "AVAILABLE" && "selected",
                flashing.has(seat.seat) && "flash",
              ]
                .filter(Boolean)
                .join(" ");

              return (
                <button
                  key={seat.seat}
                  role="gridcell"
                  className={cls}
                  disabled={blocked || !interactive}
                  aria-pressed={isSelected}
                  aria-label={`${seat.seat} ${seat.mine ? "held by you" : seat.status.toLowerCase()}`}
                  onClick={() => onToggle(seat.seat)}
                >
                  {seat.seat}
                </button>
              );
            })}
          </div>
        ))}
      </div>
      <div className="legend">
        <span>
          <span className="dot" style={{ color: "var(--available)" }} /> Available
        </span>
        <span>
          <span className="dot" style={{ color: "var(--accent)" }} /> Selected
        </span>
        <span>
          <span className="dot" style={{ color: "var(--pending)" }} /> Held by you
        </span>
        <span>
          <span className="dot" style={{ color: "var(--locked)" }} /> Locked
        </span>
        <span>
          <span className="dot" style={{ color: "var(--success)" }} /> Booked
        </span>
      </div>
    </>
  );
}
