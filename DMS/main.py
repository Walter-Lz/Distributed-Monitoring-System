import os
import json
import time
from utils import redis_client

r = redis_client.get_redis()
r.flushall()
AUDIO_DIR = "audios"
NODE_TIMEOUT = 5 

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
    
    try:
        last_heartbeat = float(stats.get("last_heartbeat", 0))
        current_time = time.time()
        time_diff = current_time - last_heartbeat
        
        # Verificar el heartbeat y el estado del nodo
        is_alive = time_diff <= NODE_TIMEOUT
        has_valid_stats = all(key in stats for key in ["cpu", "ram", "disk", "status"])
        if not is_alive or not has_valid_stats:
            return False
            
        return True
    except (ValueError, TypeError):
        return False

def handle_node_disconnection(node_id):
    if node_id not in active_nodes:
        return
    
    print(f"❌ Nodo {node_id} se ha desconectado!")
    active_nodes.remove(node_id)
    
    # Recuperar tareas pendientes del nodo
    pending_tasks = r.lrange(f"task_queue:{node_id}", 0, -1)
    
    # Obtener la tarea activa si existe
    active_tasks = int(r.hget(f"node_stats:{node_id}", "tasks") or 0)
    if active_tasks > 0:
        print(f"⚠️ El nodo {node_id} tenía {active_tasks} tarea(s) activa(s) al desconectarse")
        # Intentar recuperar la última tarea asignada
        last_task = r.hget(f"node_stats:{node_id}", "current_task")
        if last_task:
            print(f"🔄 Reasignando última tarea activa del nodo {node_id}")
            pending_tasks.append(last_task)
    
    # Limpiar datos del nodo en Redis
    r.delete(f"node_stats:{node_id}")
    r.delete(f"task_queue:{node_id}")
    r.delete(f"results:{node_id}")
    
    if pending_tasks:
        print(f"🔄 Reasignando {len(pending_tasks)} tareas de nodo {node_id}")
        for task_data in pending_tasks:
            assign_task(task_data)

def assign_task(task_data):
    node = None
    retry_count = 0
    MAX_RETRIES = 3  
    
    while not node and retry_count <= MAX_RETRIES:
        node = get_best_node()
        if not node:
            print("⏳ Esperando nodos disponibles para asignar tarea...")
            time.sleep(2)
            retry_count += 1
    
    if not node:
        print("❌ No se pudo asignar la tarea después de varios intentos")
        return False
    
    print(f"📤 Asignando tarea a {node}")
    # Guardar la tarea actual en el estado del nodo
    r.hset(f"node_stats:{node}", "current_task", task_data)
    r.rpush(f"task_queue:{node}", task_data)
    return True

def is_node_overloaded(stats):
    try:
        cpu = float(stats.get("cpu", 100))
        ram = float(stats.get("ram", 100))
        return cpu >= 80 or ram >= 90
    except (ValueError, TypeError):
        return True

def get_best_node():
    candidates = []
    node_loads = {}
    
    for key in r.scan_iter("node_stats:*"):
        node = key.split(":")[1]
        if not check_node_status(node):
            continue
        
        stats = r.hgetall(key)
        if is_node_overloaded(stats):
            continue
            
        try:
            cpu = float(stats.get("cpu", 100))
            ram = float(stats.get("ram", 100))
            active_tasks = int(stats.get("tasks", 0))
            
            pending_tasks = len(r.lrange(f"task_queue:{node}", 0, -1))
            total_tasks = active_tasks + pending_tasks
            
            resource_score = (cpu + ram) / 2 
            task_score = total_tasks * 15    
            load_score = resource_score + task_score
            
            node_loads[node] = {
                "load_score": load_score,
                "total_tasks": total_tasks,
                "cpu": cpu,
                "ram": ram
            }
            candidates.append(node)
            
        except (ValueError, TypeError):
            continue

    if not candidates:
        print("No hay nodos disponibles o todos están sobrecargados.")
        return None

    min_load_node = min(candidates, key=lambda x: node_loads[x]["load_score"])
    
    print("\n📊 Distribución de carga actual:")
    for node in candidates:
        load = node_loads[node]
        status = "✓" if node == min_load_node else " "
        print(f"   {status} Nodo {node}: {load['total_tasks']} tareas | CPU: {load['cpu']}% | RAM: {load['ram']}% | Score: {load['load_score']:.1f}")

    return min_load_node

def show_node_statuses():
    print("\nEstado actual de los nodos:")
    node_keys = [key for key in r.scan_iter("node_stats:*")]
    current_nodes = set()
    disconnected_nodes = set()
    
    total_pending = 0
    print("\n📋 Tareas pendientes por nodo:")
    for key in r.scan_iter("task_queue:*"):
        node = key.split(":")[1]
        pending_tasks = r.lrange(key, 0, -1)
        if pending_tasks:
            total_pending += len(pending_tasks)
            print(f"   📌 Nodo {node}: {len(pending_tasks)} tareas")
            for i, task in enumerate(pending_tasks, 1):
                task_data = json.loads(task)
                print(f"      {i}. Audio {task_data['index']}: {task_data['path']}")
    
    if total_pending == 0:
        print("   💤 No hay tareas pendientes")
    print(f"\n📊 Total de tareas pendientes: {total_pending}")
    print("\n🖥️ Estado de los nodos:")
    
    # Primera pasada: identificar nodos desconectados
    for key in node_keys:
        node = key.split(":")[1]
        if not check_node_status(node):
            disconnected_nodes.add(node)
            if node in active_nodes:
                handle_node_disconnection(node)
    
    # Segunda pasada: mostrar estado de nodos
    for key in node_keys:
        node = key.split(":")[1]
        current_nodes.add(node)
        stats = r.hgetall(key)
        
        if node in disconnected_nodes:
            continue
            
        if node not in active_nodes:
            active_nodes.add(node)
            print(f"✅ Nodo {node} se ha conectado!")
        
        try:
            cpu = float(stats.get("cpu", 100))
            ram = float(stats.get("ram", 100))
            disk = float(stats.get("disk", 100))
            tasks = int(stats.get("tasks", 0))
            node_status = stats.get("status", "available")
            
            if is_node_overloaded(stats):
                status = "🔶" 
                status_text = "SOBRECARGADO"
            else:
                status = "🟢" 
                status_text = "DISPONIBLE"
                
            print(f"{status} Nodo {node} [{status_text}] ➤ CPU: {cpu:.1f}% | RAM: {ram:.1f}% | Disco: {disk:.1f}% | Tareas activas: {tasks} | Estado: {node_status}")
        except (ValueError, TypeError):
            print(f"⚠️ Nodo {node} tiene datos de estado inválidos")

# Asignación inicial de tareas
for idx, filename in enumerate(audio_files):
    path = os.path.join(AUDIO_DIR, filename)
    task_data = json.dumps({"index": idx, "path": path})
    assign_task(task_data)

results = {}
tasks_completed = False
print("\n📝 TRANSCRIPCIONES EN TIEMPO REAL:\n")

while True:
    show_node_statuses()
    
    # Procesar resultados si aún hay tareas pendientes
    if not tasks_completed:
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
        
        # Verificar si se completaron todas las tareas
        if len(results) == len(audio_files) and not tasks_completed:
            tasks_completed = True
            print("\n✅ Todas las transcripciones han sido recibidas.")
            print("👀 Sistema en espera de nuevas tareas...\n")
    
    time.sleep(1)
