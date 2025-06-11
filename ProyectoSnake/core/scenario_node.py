import time
import json
import psutil 
from utils import redis_client
import os
import sys

# Ajusta rutas si la lógica está fuera del PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIC_PATH = os.path.join(BASE_DIR, "core", "logic")
if LOGIC_PATH not in sys.path:
    sys.path.append(LOGIC_PATH)

from logic.game_state import create_game_state 
from logic.scenario import add_food, add_obstacle  

r = redis_client.get_redis()
node_id = "scenario_node"

SCENARIO_TASKS_QUEUE = "scenario_tasks"
SNAKE_STATE_KEY = "snake:state"

def update_node_status(node_id):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    r.hset(f"node_stats:{node_id}", mapping={
        "cpu": cpu,
        "ram": ram,
        "last_heartbeat": time.time(),
        "status": "available",
        "tasks": 1  # Puedes ajustar esto si quieres contar tareas concurrentes reales
    })

def process_task(data):
    task = json.loads(data)
    if task.get("type") != "scenario_update":
        print(f"⚠️ Tipo de tarea no soportado: {task.get('type')}")
        return

    print(f"🍏 {node_id} procesando tarea: {task}")
    state_json = r.get(SNAKE_STATE_KEY)
    if state_json:
        if isinstance(state_json, bytes):
            state_json = state_json.decode("utf-8")
        game_state = json.loads(state_json)
    else:
        # Cuando no existe el estado, crea snake y comida aleatoria
        game_state = create_game_state(
            snake=[[5, 5], [5, 4], [5, 3]],
            food=[],
            obstacles=[]
        )
        game_state = add_food(game_state)  # ← Comida aleatoria

    action = task.get("action")
    if action == "add_food":
        pos = task.get("position")
        game_state = add_food(game_state, pos)
        print(f"🍎 Comida agregada en {game_state['food']}")
    elif action == "add_obstacle":
        pos = task.get("position")
        game_state = add_obstacle(game_state, pos)
        print(f"🪨 Obstáculo agregado en {game_state['obstacles'][-1]}")
    # Puedes agregar más acciones aquí (remover comida, limpiar obstáculos, etc.)

    r.set(SNAKE_STATE_KEY, json.dumps(game_state))
    print(f"✅ Estado actualizado por {node_id}")

def main():
    print(f"🎤 {node_id} iniciado y esperando tareas de escenario...")
    if not r.exists(SNAKE_STATE_KEY):
        print("🟢 Inicializando estado inicial de Snake en Redis...")
        initial_state = create_game_state(
            snake=[[5, 5], [5, 4], [5, 3]],
            food=[],
            obstacles=[]
        )
        initial_state = add_food(initial_state)  # ← Comida aleatoria desde el inicio
        r.set(SNAKE_STATE_KEY, json.dumps(initial_state))

    while True:
        task = r.blpop(SCENARIO_TASKS_QUEUE, timeout=1)
        if task:
            _, data = task
            process_task(data)
        update_node_status(node_id)  # <--- NUEVO, se llama en cada ciclo
        time.sleep(0.05)

if __name__ == "__main__":
    main()
