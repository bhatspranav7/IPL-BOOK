import { teamColor } from "../format";

export function Crest({ team, large = false }: { team: string; large?: boolean }) {
  const code = team.trim().slice(0, 4).toUpperCase();
  return (
    <span className={`crest${large ? " lg" : ""}`} style={{ background: teamColor(team) }} aria-hidden="true">
      {code}
    </span>
  );
}
