# IPL Book

Full-stack IPL ticket booking system built around one problem: **two people clicking the same seat at the same instant must never both get it.**

- **Distributed seat locking.** Redis `SET NX EX`; the lock value is the user id, and release is owner-checked with a Lua script.
- **Two-phase payments.** `PENDING → SUCCESS | FAILED`. Confirm uses a conditional `UPDATE … WHERE is_booked = false` as a second line of defence.
- **ML dynamic pricing.** A gradient-boosted demand model (occupancy, hours to match, hour, weekday) sets `price = base × (1 + demand)`.
- **AI seat agent.** Scores contiguous seat blocks (centre of row, closeness to the pitch), then runs the normal lock → pay flow.
- **Real-time.** Every lock, release, payment and booking is pushed over WebSockets to every open seat map, and to Kafka when it's enabled.
- **React frontend.** Live seat grid, lock countdown, pricing what-if sliders, request log, and a lock-race lab.

```
React (Vite) ──► FastAPI ──► Redis        seat locks (TTL 120s → 300s during payment)
                   │    └──► PostgreSQL   users · matches · seats · bookings · booking_logs
                   │    └──► scikit-learn demand model
                   └──► WebSocket / Kafka booking events
```

## Run it

### Everything in Docker (recommended)

```bash
docker compose up --build
```

Open http://localhost:8000 (the UI) and http://localhost:8000/docs (Swagger). Add `--profile kafka` and set `KAFKA_BOOTSTRAP=kafka:9092` to turn on the Kafka event stream.

### Local development

```bash
# 1. Postgres + Redis
docker compose -f backend/docker-compose.yml up -d

# 2. Backend (WSL / Linux / macOS)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5433/ipldb
uvicorn main:app --reload

# 3. Frontend (another terminal): proxies /api to :8000
cd frontend
npm install
npm run dev          # http://localhost:5173
```

If Redis isn't reachable, the backend falls back to an in-process lock store and reports `lock_backend: in-memory` at `/health`.

## Deploy (Render, free tier)

1. Push this repo to GitHub.
2. In Render, go to **New → Blueprint** and select the repo. `render.yaml` creates:
   - `ipl-book`: a Docker web service (FastAPI + the built React app on one URL)
   - `ipl-book-db`: PostgreSQL
   - `ipl-book-redis`: a Redis-compatible Key Value store
3. Optional: set `ADMIN_EMAILS=you@example.com` so only you can create matches. If it's empty, any signed-in user can create one (demo mode).

`SECRET_KEY` is generated for you. The first deploy takes about 5 minutes. Free services sleep after inactivity, so the first request after a pause is slow.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/ipldb` | Postgres connection string (`postgres://` is accepted) |
| `REDIS_URL` | `redis://localhost:6379/0` | Seat lock store |
| `SECRET_KEY` | random per boot | JWT signing key. **Set this in production.** |
| `ADMIN_EMAILS` | empty (everyone) | Comma-separated emails allowed to create matches |
| `KAFKA_BOOTSTRAP` | empty (disabled) | e.g. `kafka:9092` |
| `LOCK_TTL_SECONDS` | `120` | Seat hold before payment starts |
| `PAYMENT_TTL_SECONDS` | `300` | Seat hold once payment is initiated |
| `CORS_ORIGINS` | `*` | Only needed if the frontend is hosted on another origin (`VITE_API_URL` at build time) |

## API

Every route is served at the root (Swagger / curl) and under `/api` (used by the UI).

| Method | Path | Auth | |
| --- | --- | --- | --- |
| POST | `/register`, `/login` | – | JSON body; returns a JWT |
| GET | `/me` | ✓ | Current user |
| GET | `/matches`, `/matches/{id}` | – | With live seat counts |
| GET | `/matches/{id}/seats` | optional | `AVAILABLE / LOCKED / BOOKED`, plus `mine` |
| POST | `/create-match` | admin | Generates seats A1…A10, B1… |
| GET | `/dynamic-price/{id}` | – | ML price with its inputs |
| GET | `/price-simulate?occupancy=&hours_to_match=` | – | What-if pricing |
| POST | `/booking/validate-seats` | ✓ | Validate and lock seats |
| POST | `/booking/release` | ✓ | Release your own locks |
| GET | `/booking/me` | ✓ | Your bookings |
| POST | `/payments/initiate-payment` | ✓ | Requires your locks; creates a PENDING booking |
| POST | `/payments/confirm-payment` | ✓ owner | Books the seats |
| POST | `/payments/fail-payment` | ✓ owner | Releases the seats |
| GET | `/payments/status/{id}` | ✓ owner | |
| POST | `/ai-book/{id}?count=2` | ✓ | Agent picks and locks seats, then initiates payment |
| POST | `/lab/race` | – | Two threads race `SET NX` on a sandbox key |
| WS | `/ws/events` | – | Booking event stream |
| GET | `/health` | – | DB / lock backend / Kafka / model status |

See [DEMO.md](DEMO.md) for a step-by-step walkthrough.
