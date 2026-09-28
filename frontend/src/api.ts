// Same-origin by default: in dev Vite proxies /api, in prod FastAPI serves the app.
// Set VITE_API_URL only when the frontend is hosted separately from the backend.
const API_ORIGIN = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
const API = `${API_ORIGIN}/api`;
const TOKEN_KEY = "iplbook.token";

export type SeatStatus = "AVAILABLE" | "LOCKED" | "BOOKED";
export type PaymentStatus = "PENDING" | "SUCCESS" | "FAILED";

export interface User {
  id: number;
  name: string;
  email: string;
  is_admin: boolean;
}

export interface Match {
  id: number;
  team1: string;
  team2: string;
  stadium: string;
  date: string;
  total_seats: number;
  available_seats: number;
}

export interface Seat {
  seat: string;
  status: SeatStatus;
  mine: boolean;
}

export interface Pricing {
  match_id: number;
  base_price: number;
  total_seats: number;
  seats_remaining: number;
  occupancy: number;
  time_to_match_hours: number;
  demand_score: number;
  dynamic_price: number;
  model_mae: number | null;
}

export interface Payment {
  payment_id: string;
  status: PaymentStatus;
  match_id: number;
  seats: string[];
  amount: number | null;
  created_at: string;
  expires_in?: number;
  price_per_seat?: number;
  match?: { team1: string; team2: string; stadium: string; date: string };
}

export interface AgentResult {
  selected_seats: string[];
  reasoning: { seats: string[]; score: number; centre_score: number; row_score: number };
  alternatives: { seats: string[]; score: number }[];
  trace: { seats: string[]; result: string }[];
  booking_response: Payment;
}

export interface RaceResult {
  seat: string;
  lock_backend: string;
  winner: string;
  contenders: { user: string; acquired: boolean; latency_ms: number }[];
  exactly_one_winner: boolean;
}

export interface Health {
  status: string;
  database: string;
  lock_backend: string;
  kafka: string;
  lock_ttl_seconds: number;
  model_mae: number | null;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export const tokenStore = {
  get: () => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set: (token: string | null) => {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* storage unavailable: session-only login */
    }
  },
};

let onUnauthorized: () => void = () => {};
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

function errorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (d && typeof d === "object" && "msg" in d ? String(d.msg) : String(d)))
        .join(", ");
    }
    if (detail && typeof detail === "object" && "message" in detail) {
      return String((detail as { message: unknown }).message);
    }
  }
  return fallback;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  let res: Response;
  try {
    res = await fetch(`${API}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "Cannot reach the server");
  }

  const body = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized();
    throw new ApiError(res.status, errorMessage(body, `Request failed (${res.status})`));
  }
  return body as T;
}

const post = <T>(path: string, data?: unknown) =>
  request<T>(path, { method: "POST", body: data === undefined ? undefined : JSON.stringify(data) });

type AuthResponse = { access_token: string; user: User };

export const api = {
  health: () => request<Health>("/health"),
  register: (name: string, email: string, password: string) =>
    post<AuthResponse>("/register", { name, email, password }),
  login: (email: string, password: string) => post<AuthResponse>("/login", { email, password }),
  me: () => request<User>("/me"),

  matches: () => request<Match[]>("/matches"),
  match: (id: number) => request<Match>(`/matches/${id}`),
  seats: (id: number) => request<Seat[]>(`/matches/${id}/seats`),
  createMatch: (data: { team1: string; team2: string; stadium: string; date: string; seats: number }) =>
    post<{ match_id: number }>("/create-match", data),

  price: (id: number) => request<Pricing>(`/dynamic-price/${id}`),
  simulatePrice: (occupancy: number, hours: number) =>
    request<{ demand_score: number; dynamic_price: number }>(
      `/price-simulate?occupancy=${occupancy}&hours_to_match=${hours}`,
    ),

  lockSeats: (match_id: number, seats: string[]) =>
    post<{ seats: string[]; expires_in: number }>("/booking/validate-seats", { match_id, seats }),
  releaseSeats: (match_id: number, seats: string[]) =>
    post<{ released: string[] }>("/booking/release", { match_id, seats }),
  myBookings: () => request<Payment[]>("/booking/me"),

  initiatePayment: (match_id: number, seats: string[]) =>
    post<Payment>("/payments/initiate-payment", { match_id, seats }),
  confirmPayment: (payment_id: string) => post<Payment>("/payments/confirm-payment", { payment_id }),
  failPayment: (payment_id: string) => post<Payment>("/payments/fail-payment", { payment_id }),
  paymentStatus: (payment_id: string) => request<Payment>(`/payments/status/${payment_id}`),

  aiBook: (match_id: number, count: number) => post<AgentResult>(`/ai-book/${match_id}?count=${count}`),
  race: (match_id: number, seat: string) => post<RaceResult>("/lab/race", { match_id, seat }),
};

export function wsUrl(path: string): string {
  const base = API_ORIGIN || window.location.origin;
  return `${base.replace(/^http/, "ws")}/api${path}`;
}
