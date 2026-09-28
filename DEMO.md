# Demo script

## Start

```bash
docker compose up --build
```

Wait for `Application startup complete`, then open:

- UI: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health (should show `postgres`, `lock_backend: redis`)

## Part 1: UI walkthrough (about 3 minutes)

1. **Sign in → Create account.**
2. **Admin → Create a match** (for example RCB v CSK, 50 seats). You land on the seat map.
3. **Open the same match in a second browser window** (incognito, with a second account). Keep both visible.
4. In window 1, pick `A1, A2` and click **Lock**. Window 2 turns them amber instantly (WebSocket), and the request log shows `SET lock:… NX EX 120 → OK`.
5. In window 2, try to lock `A2`. You get *"A2 is being booked by someone else"*.
6. In window 1: **Proceed to pay → Pay.** The seats turn green in both windows. The live price rises, because occupancy fed the model.
7. Lock another seat and click **Simulate failure**. The locks are released and the seat is back on sale.
8. **AI pick best**: the agent scores seat blocks, locks the best one, and opens a pending payment. The log shows its trace.
9. **Lab → Run race**: two threads hit the same Redis key at once. Exactly one wins, every time.
10. **Pricing sliders**: drag occupancy or time-to-match to see the model's what-if price.

## Part 2: API in Swagger

All request bodies are JSON. Credentials are no longer sent as query parameters.

1. `POST /register` with `{"name": "pranav", "email": "pranav@1.com", "password": "1234"}`
2. `POST /login` with `{"email": "pranav@1.com", "password": "1234"}`. Copy `access_token`, click **Authorize**, and paste the token.
3. `POST /create-match` with `{"team1": "RCB", "team2": "CSK", "stadium": "Chinnaswamy", "date": "2026-06-26", "seats": 50}`, which returns `match_id`.
4. `GET /matches` and `GET /matches/{id}/seats`
5. `GET /dynamic-price/{id}`
6. `POST /booking/validate-seats` with `{"match_id": 1, "seats": ["A1", "A2"]}`, which returns `Seats locked successfully`.
7. `POST /payments/initiate-payment` with the same body, which returns `payment_id` and `PENDING`.
8. `GET /payments/status/{payment_id}` shows `PENDING` and `expires_in`.
9. `POST /payments/confirm-payment` with `{"payment_id": "…"}`, which returns `SUCCESS`.
10. `POST /booking/validate-seats` for `A1` again, which returns `409 A1 already booked`.
11. `POST /ai-book/{id}?count=2` (optional)
12. `POST /payments/fail-payment` on a new pending payment (optional)

## Talking points

1. **Race conditions.** Redis `SET NX EX` is atomic, so exactly one concurrent caller gets a seat. Tested with 20 simultaneous users on one seat: 1 winner, 19 rejections.
2. **Ownership.** The lock value is the user id. Initiate-payment requires that you hold the locks, and release uses a compare-and-delete Lua script, so nobody can pay for or free someone else's hold.
3. **Defence in depth.** Confirm runs `UPDATE seats … WHERE is_booked = false` and checks the row count. Even if a lock is lost (Redis restart, expiry), Postgres will never double-book.
4. **Abandoned carts.** TTLs evict locks automatically. The hold is 120s while selecting and extended to 300s once payment starts, so no cleanup job is needed.
5. **Payment security.** Confirm, fail and status all require the booking owner's JWT. Someone else's payment_id returns 404, so ids can't be probed.
6. **Pricing.** A gradient-boosted regressor on scale-free features (occupancy, not raw seat counts) gives `price = base × (1 + demand)`. It is trained at Docker build time, so the pickle always matches the installed sklearn version.
7. **Real-time.** Sync endpoints publish to the event loop with `run_coroutine_threadsafe`, and every seat map updates live. Kafka receives the same events when enabled.
8. **Deployment.** One Docker image (the React build is served by FastAPI), with a Render blueprint for web + Postgres + Redis.

## Scaling next steps

- Redis pub/sub fan-out so WebSockets work across multiple app instances (today the broadcast is per process)
- A real payment gateway (Razorpay/Stripe) with webhooks driving confirm/fail
- Alembic migrations in place of `create_all` plus the `ADD COLUMN IF NOT EXISTS` shim
- Retrain the demand model on the `booking_logs` history (`app/ml/export_data.py`)
