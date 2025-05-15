from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from utils.redis_client import get_redis
import asyncio

app = FastAPI()
redis_client = get_redis()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            nodes = {key.split(":")[1]: redis_client.hgetall(key) for key in redis_client.keys("node_stats:*")}
            tasks = {key.split(":")[1]: redis_client.lrange(key, 0, -1) for key in redis_client.keys("task_queue:*")}
            
            for key in redis_client.keys("node_stats:*"):
                node = key.split(":")[1]
                stats = redis_client.hgetall(key)
                active_tasks = [stats[k] for k in stats if k.startswith("current_task:")]
                if active_tasks:
                    if node not in tasks:
                        tasks[node] = []
                    tasks[node].extend(active_tasks)
            
            # Leer el archivo finalizadas.txt y agrupar por nodo
            results = {}
            try:
                with open("finalizadas.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            # Espera formato: Nodo nodeX terminó la tarea: path en X.XX s
                            parts = line.split()
                            if len(parts) > 2:
                                node = parts[1]
                                if node not in results:
                                    results[node] = []
                                results[node].append(line.strip())
            except FileNotFoundError:
                results = {}
            await websocket.send_json({
                "nodes": nodes,
                "tasks": tasks,
                "results": results,
            })
            await asyncio.sleep(2)
    except Exception as e:
        print(f"WebSocket desconectado: {e}")
    finally:
        await websocket.close()