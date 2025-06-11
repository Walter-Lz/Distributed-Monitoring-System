import time
import json
from utils import redis_client
import os
import sys

# Ajusta rutas si es necesario
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTO_SNAKE_PATH = os.path.join(BASE_DIR, "ProyectoSnake")
if PROYECTO_SNAKE_PATH not in sys.path:
    sys.path.append(PROYECTO_SNAKE_PATH)

from logic.game_state import create_game_state

r = redis_client.get_redis()
node_id = "player_node"

PLAYER_TASKS_QUEUE = "player_tasks"
SNAKE_STATE_KEY = "snake:state"
GLOBAL_TASKS_QUEUE = "global:unassigned_tasks"  # <- Para enviar tareas de escenario

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
    return new_snake  # No hacemos pop todavía

def process_task(data):
    task = json.loads(data)
    if task.get("type") != "snake_move":
        print(f"⚠️ Tipo de tarea no soportado: {task.get('type')}")
        return

    print(f"🐍 {node_id} procesando tarea: {task}")
    state_json = r.get(SNAKE_STATE_KEY)
    if state_json:
        if isinstance(state_json, bytes):
            state_json = state_json.decode("utf-8")
        game_state = json.loads(state_json)
    else:
        # Estado inicial si no existe
        game_state = {
            "snake": [[5, 5], [5, 4], [5, 3]],
            "food": [10, 10],
            "score": 0,
            "game_over": False,
            "obstacles": []
        }

    direction = task.get("direction")
    snake = game_state.get("snake", [[5, 5], [5, 4], [5, 3]])
    food = game_state.get("food", [10, 10])
    obstacles = game_state.get("obstacles", [])
    score = game_state.get("score", 0)
    game_over = game_state.get("game_over", False)

    # Mueve la snake (no hacemos pop todavía)
    new_snake = move_snake(snake, direction)
    head = new_snake[0]

    ate_food = (head == food)
    if ate_food:
        # No se hace pop -> la snake crece
        score += 1  # Si quieres sumar puntos al comer
        print(f"🍏 ¡Comida comida en {food}! Enviando tarea para nueva comida.")
        # Envía tarea de escenario
        r.lpush(GLOBAL_TASKS_QUEUE, json.dumps({
            "type": "scenario_update",
            "action": "add_food"
        }))
    else:
        new_snake.pop()  # No crece, solo mueve

    # Guarda el nuevo estado
    new_state = create_game_state(new_snake, [food], obstacles, score, game_over)
    r.set(SNAKE_STATE_KEY, json.dumps(new_state))
    print(f"✅ Estado actualizado por {node_id}")

def main():
    print(f"🎤 {node_id} iniciado y esperando tareas...")
    # Si el estado inicial no existe, lo crea:
    if not r.exists(SNAKE_STATE_KEY):
        print("🟢 Inicializando estado inicial de Snake en Redis...")
        initial_state = create_game_state(
            snake=[[5, 5], [5, 4], [5, 3]],
            food=[[10, 10]],
            obstacles=[]
        )
        r.set(SNAKE_STATE_KEY, json.dumps(initial_state))

    while True:
        task = r.blpop(PLAYER_TASKS_QUEUE, timeout=1)
        if task:
            _, data = task
            process_task(data)
        time.sleep(0.05)

if __name__ == "__main__":
    main()
