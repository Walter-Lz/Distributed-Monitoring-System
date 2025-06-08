import time
import json
import threading
from queue import Queue
from utils import redis_client
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTO_SNAKE_PATH = os.path.join(BASE_DIR, "ProyectoSnake")
if PROYECTO_SNAKE_PATH not in sys.path:
    sys.path.append(PROYECTO_SNAKE_PATH)

from Logic import create_game_state

r = redis_client.get_redis()
node_id = "nodoMovimiento"
print(f"🔧 Nodo de movimiento registrado como ID: {node_id}")

def move_snake(snake, direction):
    new_snake = [list(pos) for pos in snake]
    head = new_snake[0].copy()
    if direction == "up":
        head[1] -= 1
    elif direction == "down":
        head[1] += 1
    elif direction == "left":
        head[0] -= 1
    elif direction == "right":
        head[0] += 1
    new_snake.insert(0, head)
    new_snake.pop()
    return new_snake

def process_task(data):
    task = json.loads(data)
    if task.get("type") != "snake_move":
        print(f"⚠️ Tipo de tarea no soportado: {task.get('type')}")
        return

    print(f"🐍 Nodo de movimiento procesando tarea Snake: {task}")
    state_json = r.get("snake:state")
    if state_json:
        if isinstance(state_json, bytes):
            state_json = state_json.decode("utf-8")
        game_state = json.loads(state_json)
    else:
        initial_snake = [[5, 5], [5, 4], [5, 3]]
        initial_objectives = [[10, 10]]
        initial_obstacles = []
        game_state = {
            "snake": initial_snake,
            "food": initial_objectives[0],
            "score": 0,
            "game_over": False,
            "obstacles": initial_obstacles
        }

    direction = task.get("direction")
    snake = game_state.get("snake", [[5, 5], [5, 4], [5, 3]])
    food = game_state.get("food", [10, 10])  # [10, 10]
    obstacles = game_state.get("obstacles", [])
    score = game_state.get("score", 0)
    game_over = game_state.get("game_over", False)

    # Mueve la serpiente
    snake = move_snake(snake, direction)

    # Pasa [food] para que objectives sea una lista de listas
    new_state = create_game_state(snake, [food], obstacles, score, game_over)
    r.set("snake:state", json.dumps(new_state))

def main():
    print(f"🎤 Nodo de movimiento {node_id} iniciando...")
    if not r.exists("snake:state"):
        print("🟢 Inicializando estado inicial de Snake en Redis...")
        initial_snake = [[5, 5], [5, 4], [5, 3]]
        initial_objectives = [[10, 10]]
        initial_obstacles = []
        initial_state = create_game_state(initial_snake, initial_objectives, initial_obstacles)
        r.set("snake:state", json.dumps(initial_state))

    while True:
        task = r.blpop("global:unassigned_tasks", timeout=1)
        if task:
            _, data = task
            process_task(data)
        time.sleep(0.1)

if __name__ == "__main__":
    main()