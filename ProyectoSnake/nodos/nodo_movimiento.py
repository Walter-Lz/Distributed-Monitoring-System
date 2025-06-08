import redis
import json
from Logic import deep_search

# Conexión a Redis (ajusta host/port si es necesario)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

print("Nodo de movimiento iniciado. Esperando peticiones...")

while True:
    # Espera una petición en la cola 'snake:movement:request'
    _, msg = r.blpop("snake:movement:request")
    data = json.loads(msg)
    start = tuple(data["start"])
    end = tuple(data["end"])
    obstacles = [tuple(x) for x in data["obstacles"]]
    # Calcula el camino usando deep_search
    path = deep_search(start, end, obstacles)
    # Devuelve el resultado en la cola 'snake:movement:response'
    r.rpush("snake:movement:response", json.dumps({"path": path}))