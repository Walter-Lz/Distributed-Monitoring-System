import redis
import json

r = redis.Redis()
score = 0

while True:
    _, msg = r.blpop("snake:score:event")
    data = json.loads(msg)
    if data["event"] == "objective_reached":
        score += 1
        r.set("snake:score:value", score)