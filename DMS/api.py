from fastapi import FastAPI
from utils.redis_client import get_redis
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
redis_client = get_redis()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite solicitudes desde cualquier origen. Cambia "*" por dominios específicos si es necesario.
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP (GET, POST, etc.).
    allow_headers=["*"],  # Permite todos los encabezados.
)


@app.get("/nodes")
async def get_nodes():
    """Endpoint para obtener el estado de todos los nodos."""
    keys = redis_client.keys("node_stats:*")
    nodes = {key.split(":")[1]: redis_client.hgetall(key) for key in keys}
    return nodes

@app.get("/tasks")
async def get_tasks():
    """Endpoint para obtener las tareas en progreso."""
    keys = redis_client.keys("task_queue:*")
    tasks = {key.split(":")[1]: redis_client.lrange(key, 0, -1) for key in keys}
    return tasks

@app.get("/results")
async def get_results():
    """Endpoint para obtener los resultados de las transcripciones."""
    keys = redis_client.keys("results:*")
    results = {key.split(":")[1]: redis_client.lrange(key, 0, -1) for key in keys}
    return results