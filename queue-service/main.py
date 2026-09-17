import os
import time
import uuid

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="QueueGuard Queue Service")

# Redis connection — host/port come from env vars, defaults for local dev
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


# ---------- Request models ----------

class JoinRequest(BaseModel):
    event_id: str
    user_id: str


# ---------- Endpoints ----------

@app.get("/health")
def health():
    try:
        r.ping()
        return {"status": "ok", "redis": "up"}
    except Exception as e:
        return {"status": "degraded", "redis": "down", "error": str(e)}


@app.post("/queue/join")
def join_queue(req: JoinRequest):
    queue_key = f"queue:{req.event_id}"

    # Score = join timestamp. Earlier join = lower score = earlier in line.
    # NX = only add if user isn't already in the queue (idempotent).
    added = r.zadd(queue_key, {req.user_id: time.time()}, nx=True)

    # Get this user's rank (0-indexed). Position = rank + 1.
    rank = r.zrank(queue_key, req.user_id)

    return {
        "event_id": req.event_id,
        "user_id": req.user_id,
        "position": rank + 1,
        "already_in_queue": added == 0,
        "queue_size": r.zcard(queue_key),
    }


@app.get("/queue/status/{event_id}/{user_id}")
def queue_status(event_id: str, user_id: str):
    queue_key = f"queue:{event_id}"
    rank = r.zrank(queue_key, user_id)

    if rank is None:
        raise HTTPException(status_code=404, detail="User not in queue")

    return {
        "event_id": event_id,
        "user_id": user_id,
        "position": rank + 1,
        "queue_size": r.zcard(queue_key),
    }
