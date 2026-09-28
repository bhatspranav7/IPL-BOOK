"""Race demo: two threads hit the same seat at the same instant.

Uses a throwaway key namespace with a short TTL so it never interferes with
real bookings, but it exercises the exact SET NX EX primitive the booking
flow relies on.
"""
import threading
import time
import uuid

from fastapi import APIRouter

from app.schemas.payment_schema import RaceRequest
from app.utils.redis_client import redis_client, REDIS_MODE

router = APIRouter(prefix="/lab", tags=["Lab"])


@router.post("/race")
def race(data: RaceRequest):
    key = f"race:{data.match_id}:{data.seat.upper()}:{uuid.uuid4().hex[:8]}"
    barrier = threading.Barrier(2)
    results = {}

    def contender(name: str):
        barrier.wait()
        start = time.perf_counter()
        won = bool(redis_client.set(key, name, nx=True, ex=5))
        results[name] = {
            "user": name,
            "acquired": won,
            "latency_ms": round((time.perf_counter() - start) * 1000, 3),
        }

    threads = [threading.Thread(target=contender, args=(n,)) for n in ("user_A", "user_B")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    winner = redis_client.get(key)
    redis_client.delete(key)

    return {
        "seat": data.seat.upper(),
        "lock_backend": REDIS_MODE,
        "winner": winner,
        "contenders": [results["user_A"], results["user_B"]],
        "exactly_one_winner": sum(r["acquired"] for r in results.values()) == 1,
    }
