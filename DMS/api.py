from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from utils.redis_client import get_redis
import asyncio
import json

app = FastAPI()
r = get_redis()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.post("/snake/move")
async def snake_move(move: dict):
    # move = {"type": "snake_move", "player_id": "...", "direction": "..."}
    r.lpush("global:unassigned_tasks", json.dumps(move))
    return {"status": "ok"}


@app.websocket("/ws/snake")
async def ws_snake(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            state = r.get("snake:state")
            if state:
                # Si el estado está en bytes, decodifica
                if isinstance(state, bytes):
                    state = state.decode("utf-8")
                await websocket.send_text(state)
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"WebSocket Snake desconectado: {e}")
    finally:
        await websocket.close()

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