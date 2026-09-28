const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });

export const money = (n: number | null | undefined) => (n == null ? "—" : inr.format(n));

export function matchDate(value: string): string {
  const iso = /^\d{4}-\d{2}-\d{2}/.test(value)
    ? value.slice(0, 10)
    : value.replace(/^(\d{2})-(\d{2})-(\d{4})$/, "$3-$2-$1");
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric" });
}

export function hoursLabel(h: number): string {
  if (h <= 0) return "started";
  if (h < 1) return `${Math.round(h * 60)}m`;
  if (h < 48) return `${Math.round(h)}h`;
  return `${Math.round(h / 24)}d`;
}

export function clock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export function timeStamp(d = new Date()): string {
  return d.toLocaleTimeString("en-GB", { hour12: false });
}

// Short team codes for the crest badges
const TEAM_COLORS: Record<string, string> = {
  CSK: "#f9cd05",
  MI: "#3a7bd5",
  RCB: "#e2383f",
  KKR: "#8e5cc7",
  SRH: "#f26522",
  DC: "#3b82f6",
  PBKS: "#ed1b24",
  RR: "#e73895",
  GT: "#5b7bb6",
  LSG: "#44c3e3",
};

export function teamColor(team: string): string {
  const key = team.trim().toUpperCase();
  if (TEAM_COLORS[key]) return TEAM_COLORS[key];
  let h = 0;
  for (const ch of key) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return `hsl(${h} 60% 58%)`;
}
