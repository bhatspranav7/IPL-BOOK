import redis

r = redis.Redis(host="localhost", port=6379, db=0)

def lock_seat(match_id, user_id):

    key = f"lock:{match_id}:{user_id}"

    if r.get(key):
        return False

    r.setex(key, 120, "locked")

    return True