from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from utils.redis_client import get_redis
import asyncio

app = FastAPI()
redis_client = get_redis()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia "*" por dominios específicos si es necesario.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para enviar actualizaciones continuas."""
    await websocket.accept()
    try:
        while True:
            # Obtener datos de nodos, tareas y resultados
            nodes = {key.split(":")[1]: redis_client.hgetall(key) for key in redis_client.keys("node_stats:*")}
            tasks = {key.split(":")[1]: redis_client.lrange(key, 0, -1) for key in redis_client.keys("task_queue:*")}
            results = {key.split(":")[1]: redis_client.lrange(key, 0, -1) for key in redis_client.keys("results:*")}

            # Enviar datos al cliente
            await websocket.send_json({
                "nodes": nodes,
                "tasks": tasks,
                "results": results,
            })

            # Esperar antes de enviar la siguiente actualización
            await asyncio.sleep(2)
    except Exception as e:
        print(f"WebSocket desconectado: {e}")
    finally:
        await websocket.close()