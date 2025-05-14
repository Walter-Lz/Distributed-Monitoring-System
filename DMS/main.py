import os
import json
import time
from utils import redis_client

r = redis_client.get_redis()
r.flushall()
AUDIO_DIR = "audios"
NODE_TIMEOUT = 3  # Tiempo máximo sin heartbeat antes de considerar un nodo como inactivo

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
    retry_count = 0
    max_retries = 3  # Número máximo de intentos para asignar una tarea
    
    while not node and retry_count < max_retries:
        node = get_best_node()
        if not node:
            print("⏳ Esperando nodos disponibles para asignar tarea...")
            time.sleep(2)
            retry_count += 1
    
    if not node:
        print("❌ No se pudo asignar la tarea después de varios intentos")
        return False
    
    print(f"📤 Asignando tarea a {node}")
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
    
    # Primero recolectamos información de todos los nodos disponibles
    for key in r.scan_iter("node_stats:*"):
        node = key.split(":")[1]
        if not check_node_status(node):
            continue
        
        stats = r.hgetall(key)
        if is_node_overloaded(stats):
            continue
            
        try:
            # Obtener métricas del nodo
            cpu = float(stats.get("cpu", 100))
            ram = float(stats.get("ram", 100))
            active_tasks = int(stats.get("tasks", 0))
            
            # Obtener tareas pendientes
            pending_tasks = len(r.lrange(f"task_queue:{node}", 0, -1))
            total_tasks = active_tasks + pending_tasks
            
            # Calcular puntuación de carga
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

    # Encontrar el nodo con menor carga
    min_load_node = min(candidates, key=lambda x: node_loads[x]["load_score"])
    
    # Imprimir información de distribución de carga
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
    
    # Mostrar tareas pendientes totales
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
    
    for key in node_keys:
        node = key.split(":")[1]
        current_nodes.add(node)
        stats = r.hgetall(key)
        
        # Verificar si el nodo está activo
        if check_node_status(node):
            if node not in active_nodes:
                active_nodes.add(node)
                print(f"✅ Nodo {node} se ha conectado!")
            
            # Determinar el estado del nodo
            if is_node_overloaded(stats):
                status = "🔶"  # Naranja para sobrecargado
            else:
                status = "🟢"  # Verde para disponible
        else:
            status = "🔴"  # Rojo para desconectado
            handle_node_disconnection(node)
            continue
            
        cpu = stats.get("cpu", "?")
        ram = stats.get("ram", "?")
        disk = stats.get("disk", "?")
        tasks = stats.get("tasks", "0")
        node_status = stats.get("status", "available")
        
        status_text = "SOBRECARGADO" if is_node_overloaded(stats) else "DISPONIBLE"
        print(f"{status} Nodo {node} [{status_text}] ➤ CPU: {cpu}% | RAM: {ram}% | Disco: {disk}% | Tareas activas: {tasks} | Estado: {node_status}")

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
