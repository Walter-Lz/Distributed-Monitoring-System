import redis

def get_redis():
    r= redis.Redis(host="localhost", port=6379, decode_responses=True)
    return r