import time
import json
from utils import redis_client

# Configuración de Redis
r = redis_client.get_redis()

NODE_TIMEOUT = 5  # segundos, tiempo máximo entre heartbeats para considerar un nodo "vivo"

# Cola global de entrada de tareas (donde la API o scripts depositan tareas)
UNASSIGNED_TASKS_QUEUE = "global:unassigned_tasks"
  


  
# Colas específicas para cada tipo de worker
PLAYER_TASKS_QUEUE = "player_tasks"
SCENARIO_TASKS_QUEUE = "scenario_tasks"

def check_node_status(node_id):
    stats = r.hgetall(f"node_stats:{node_id}")
    if not stats:
        return False
    try:
        last_heartbeat = float(stats.get("last_heartbeat", 0))
        return time.time() - last_heartbeat <= NODE_TIMEOUT
    except Exception:
        return False

def show_node_statuses():
    print("\nEstado actual de los nodos:")
    node_keys = [key for key in r.scan_iter("node_stats:*")]
    for key in node_keys:
        node = key.split(":")[1]
        stats = r.hgetall(key)
        if check_node_status(node):
            cpu = float(stats.get("cpu", 100))
            ram = float(stats.get("ram", 100))
            status = stats.get("status", "available")
            tasks = int(stats.get("tasks", 0))
            max_tasks = int(stats.get("max_tasks", 1))
            print(f"🟢 Nodo {node} ➤ CPU: {cpu:.1f}% | RAM: {ram:.1f}% | Tareas: {tasks}/{max_tasks} | Estado: {status}")
        else:
            print(f"🔴 Nodo {node} inactivo o sin heartbeat reciente.")

def distribute_task(task):
    # Decide a qué cola enviar la tarea según el tipo
    task_type = task.get("type")
    if task_type == "snake_move":
        r.lpush(PLAYER_TASKS_QUEUE, json.dumps(task))
        print(f"🚀 Tarea de movimiento enviada a {PLAYER_TASKS_QUEUE}")
    elif task_type == "scenario_update":
        r.lpush(SCENARIO_TASKS_QUEUE, json.dumps(task))
        print(f"🚀 Tarea de escenario enviada a {SCENARIO_TASKS_QUEUE}")
    else:
        print(f"⚠️ Tipo de tarea desconocido: {task_type}")

def main():
    print("📝 Main node iniciado y listo para repartir tareas...\n")
    while True:
        show_node_statuses()
        # Escucha la cola global de entrada y reparte
        new_task = r.blpop(UNASSIGNED_TASKS_QUEUE, timeout=2)
        if new_task:
            _, task_data = new_task
            try:
                task = json.loads(task_data)
                distribute_task(task)
            except Exception as e:
                print(f"❌ Error al procesar tarea: {e}")
        else:
            print("⏳ Esperando tareas...")
        time.sleep(1)

if __name__ == "__main__":
    main()
