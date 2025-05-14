import os
import json
import time
from utils import redis_client

r = redis_client.get_redis()
r.flushall()
AUDIO_DIR = "audios"
NODE_TIMEOUT = 5  # Tiempo máximo sin heartbeat antes de considerar un nodo como inactivo

# Mantener registro de nodos activos y sus tareas
active_nodes = set()
node_tasks = {}

audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]
if not audio_files:
    print("❌ No hay audios para procesar.")
    exit()

def check_node_status(node_id):
    stats = r.hgetall(f"node_stats:{node_id}")
    if not stats:
        return False
    last_heartbeat = float(stats.get("last_heartbeat", 0))
    return time.time() - last_heartbeat <= NODE_TIMEOUT

def handle_node_disconnection(node_id):
    if node_id not in active_nodes:
        return
    
    print(f"❌ Nodo {node_id} se ha desconectado!")
    active_nodes.remove(node_id)
    
    # Recuperar tareas pendientes del nodo
    pending_tasks = r.lrange(f"task_queue:{node_id}", 0, -1)
    
    # Limpiar datos del nodo en Redis
    r.delete(f"node_stats:{node_id}")
    r.delete(f"task_queue:{node_id}")
    r.delete(f"results:{node_id}")
    
    if pending_tasks:
        print(f"🔄 Reasignando {len(pending_tasks)} tareas de nodo {node_id}")
        # Reasignar cada tarea
        for task_data in pending_tasks:
            assign_task(task_data)

def assign_task(task_data):
    node = None
    while not node:
        node = get_best_node()
        if not node:
            print("⏳ Esperando nodos disponibles para reasignar tarea...")
            time.sleep(1)
    
    print(f"📤 Reasignando tarea a {node}")
    r.rpush(f"task_queue:{node}", task_data)

def show_node_statuses():
    print("\nEstado actual de los nodos:")
    node_keys = [key for key in r.scan_iter("node_stats:*")]
    current_nodes = set()
    
    for key in node_keys:
        node = key.split(":")[1]
        current_nodes.add(node)
        stats = r.hgetall(key)
        
        # Verificar si el nodo está activo
        if check_node_status(node):
            if node not in active_nodes:
                active_nodes.add(node)
                print(f"✅ Nodo {node} se ha conectado!")
            status = "🟢"
        else:
            status = "🔴"
            handle_node_disconnection(node)
            continue
            
        print(f"{status} Nodo {node} ➤ CPU: {stats.get('cpu', '?')}% | RAM: {stats.get('ram', '?')}% | Disco: {stats.get('disk', '?')}% | Tareas: {stats.get('tasks', '0')}")

def get_best_node():
    candidates = []
    for key in r.scan_iter("node_stats:*"):
        node = key.split(":")[1]
        if not check_node_status(node):
            continue
        stats = r.hgetall(key)
        try:
            cpu = float(stats.get("cpu", 100))
            ram = float(stats.get("ram", 100))
            tasks = int(stats.get("tasks", 0))
            load_score = (cpu + ram) / 2 + (tasks * 10) 
            candidates.append((node, load_score))
        except (ValueError, TypeError):
            continue

    if not candidates:
        print("No hay nodos disponibles.")
        return None

    return min(candidates, key=lambda x: x[1])[0]

# Asignación inicial de tareas
for idx, filename in enumerate(audio_files):
    path = os.path.join(AUDIO_DIR, filename)
    task_data = json.dumps({"index": idx, "path": path})
    assign_task(task_data)

results = {}
print("\n📝 TRANSCRIPCIONES EN TIEMPO REAL:\n")
while len(results) < len(audio_files):
    show_node_statuses()
    
    for key in r.scan_iter("node_stats:*"):
        node = key.split(":")[1]
        if not check_node_status(node):
            continue
            
        res = r.lpop(f"results:{node}")
        if res:
            data = json.loads(res)
            index, text = data["index"], data["text"]
            if index not in results:
                results[index] = text
                print(f"📄 Audio {index}:")
                print(text)
                print("\n---\n")
            r.hincrby(f"node_stats:{node}", "tasks", -1)
    
    time.sleep(1)

print("\nTodas las transcripciones han sido recibidas.")
