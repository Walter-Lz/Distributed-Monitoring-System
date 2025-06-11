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
    """
    Encola un movimiento de Snake para ser procesado por el sistema distribuido.
    Espera un dict con {type, player_id, direction}
    """
    r.lpush("player_tasks", json.dumps(move))  # <-- Cambia aquí la cola
    return {"status": "ok"}

@app.websocket("/ws/snake")
async def ws_snake(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            state = r.get("snake:state")
            if state:
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
            # Info de nodos
            node_keys = list(r.scan_iter("node_stats:*"))
            nodes = {key.split(":")[1]: r.hgetall(key) for key in node_keys}
            # Tareas activas por nodo
            task_keys = list(r.scan_iter("task_queue:*"))
            tasks = {key.split(":")[1]: r.lrange(key, 0, -1) for key in task_keys}
            # También agregamos tareas activas embebidas (current_task)
            for key in node_keys:
                node = key.split(":")[1]
                stats = r.hgetall(key)
                active_tasks = [stats[k] for k in stats if k.startswith("current_task:")]
                if active_tasks:
                    if node not in tasks:
                        tasks[node] = []
                    tasks[node].extend(active_tasks)
            # Leer resultados finalizados por nodo desde archivo (si existe)
            results = {}
            try:
                with open("finalizadas.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
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
