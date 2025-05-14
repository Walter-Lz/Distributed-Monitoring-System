import os
import json
import time
from utils import redis_client

r = redis_client.get_redis()
r.flushall()
AUDIO_DIR = "audios"
NODE_TIMEOUT = 5 

# Clave para la cola global de tareas sin asignar
UNASSIGNED_TASKS_QUEUE = "global:unassigned_tasks"
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
        if last_task and last_task not in pending_tasks:  # Evitar duplicados
            print(f"🔄 Devolviendo última tarea activa a la cola global")
            r.rpush(UNASSIGNED_TASKS_QUEUE, last_task)
    
    # Limpiar datos del nodo en Redis
    r.delete(f"node_stats:{node_id}")
    r.delete(f"task_queue:{node_id}")
    r.delete(f"results:{node_id}")
    
    # Devolver todas las tareas pendientes a la cola global
    if pending_tasks:
        print(f"🔄 Devolviendo {len(pending_tasks)} tareas a la cola global")
        for task_data in pending_tasks:
            # Verificar que la tarea no esté ya en la cola global
            if not r.lrem(UNASSIGNED_TASKS_QUEUE, 0, task_data):
                r.rpush(UNASSIGNED_TASKS_QUEUE, task_data)

def assign_task(task_data):
    node = get_best_node()
    if not node:
        return False
    
    # Verificar que la tarea no esté ya asignada a otro nodo
    for key in r.scan_iter("task_queue:*"):
        if r.lrem(key, 0, task_data) > 0:
            print(f"⚠️ Tarea encontrada y removida de otro nodo")
    
    print(f"📤 Asignando tarea a {node}")
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
            max_tasks = int(stats.get("max_tasks", 1))
            
            # Si el nodo está en su límite de tareas, ignorarlo
            if active_tasks >= max_tasks:
                continue
                
            pending_tasks = len(r.lrange(f"task_queue:{node}", 0, -1))
            total_tasks = active_tasks + pending_tasks
            
            # Calcular score basado en recursos y capacidad disponible
            resource_score = (cpu + ram) / 2
            capacity_score = (active_tasks / max_tasks) * 100 if max_tasks > 0 else 100
            load_score = resource_score * 0.7 + capacity_score * 0.3
            
            node_loads[node] = {
                "load_score": load_score,
                "active_tasks": active_tasks,
                "max_tasks": max_tasks,
                "cpu": cpu,
                "ram": ram
            }
            candidates.append(node)
            
        except (ValueError, TypeError):
            continue

    if not candidates:
        return None

    min_load_node = min(candidates, key=lambda x: node_loads[x]["load_score"])
    
    print("\n📊 Distribución de carga actual:")
    for node in candidates:
        load = node_loads[node]
        status = "✓" if node == min_load_node else " "
        print(f"   {status} Nodo {node}: {load['active_tasks']}/{load['max_tasks']} tareas | CPU: {load['cpu']:.1f}% | RAM: {load['ram']:.1f}% | Score: {load['load_score']:.1f}")

    return min_load_node

def show_node_statuses():
    print("\nEstado actual de los nodos:")
    node_keys = [key for key in r.scan_iter("node_stats:*")]
    current_nodes = set()
    disconnected_nodes = set()
    
    # Mostrar tareas sin asignar
    unassigned_tasks = r.lrange(UNASSIGNED_TASKS_QUEUE, 0, -1)
    print("\n📋 Tareas sin asignar:")
    if unassigned_tasks:
        for i, task in enumerate(unassigned_tasks, 1):
            task_data = json.loads(task)
            print(f"   {i}. Audio {task_data['index']}: {task_data['path']}")
    else:
        print("   💤 No hay tareas sin asignar")
    print(f"\n📊 Total de tareas sin asignar: {len(unassigned_tasks)}")
    
    # Mostrar tareas pendientes por nodo
    total_pending = 0
    total_active = 0
    print("\n📋 Estado de tareas por nodo:")
    
    for key in r.scan_iter("node_stats:*"):
        node = key.split(":")[1]
        stats = r.hgetall(key)
        
        if not check_node_status(node):
            continue
            
        try:
            active_tasks = int(stats.get("tasks", 0))
            max_tasks = int(stats.get("max_tasks", 1))
            total_active += active_tasks
            
            # Obtener tareas pendientes
            pending_tasks = r.lrange(f"task_queue:{node}", 0, -1)
            pending_count = len(pending_tasks)
            total_pending += pending_count
            
            # Obtener tareas activas (current_task:thread_X)
            active_task_keys = [k for k in stats.keys() if k.startswith("current_task:")]
            
            print(f"\n   📌 Nodo {node}: {active_tasks}/{max_tasks} tareas activas, {pending_count} pendientes")
            
            # Mostrar tareas activas
            if active_task_keys:
                print(f"      Tareas activas:")
                for task_key in active_task_keys:
                    task_data = json.loads(stats[task_key])
                    print(f"         🔄 Audio {task_data['index']}: {task_data['path']}")
            
            # Mostrar tareas pendientes
            if pending_tasks:
                print(f"      Tareas pendientes:")
                for i, task in enumerate(pending_tasks, 1):
                    task_data = json.loads(task)
                    print(f"         ⏳ Audio {task_data['index']}: {task_data['path']}")
                    
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            print(f"      ⚠️ Error al procesar estado: {e}")
    
    print(f"\n📊 Resumen global:")
    print(f"   • Tareas sin asignar: {len(unassigned_tasks)}")
    print(f"   • Tareas activas: {total_active}")
    print(f"   • Tareas pendientes en nodos: {total_pending}")
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
            max_tasks = int(stats.get("max_tasks", 1))
            node_status = stats.get("status", "available")
            
            if is_node_overloaded(stats):
                status = "🔶" 
                status_text = "SOBRECARGADO"
            else:
                status = "🟢" 
                status_text = "DISPONIBLE"
                
            print(f"{status} Nodo {node} [{status_text}] ➤ CPU: {cpu:.1f}% | RAM: {ram:.1f}% | Disco: {disk:.1f}% | Tareas: {tasks}/{max_tasks} | Estado: {node_status}")
        except (ValueError, TypeError):
            print(f"⚠️ Nodo {node} tiene datos de estado inválidos")

def try_assign_pending_tasks():
    """Intenta asignar tareas pendientes a nodos disponibles"""
    # Verificar cuántas tareas hay sin asignar
    unassigned_count = r.llen(UNASSIGNED_TASKS_QUEUE)
    if unassigned_count == 0:
        return

    # Obtener una tarea sin asignar
    task = r.rpoplpush(UNASSIGNED_TASKS_QUEUE, "temp:task")
    if not task:
        return
        
    try:
        # Intentar asignarla
        if assign_task(task):
            # Si se asignó correctamente, eliminar de la cola temporal
            r.delete("temp:task")
        else:
            # Si no se pudo asignar, moverla de vuelta a la cola global
            r.rpoplpush("temp:task", UNASSIGNED_TASKS_QUEUE)
    except Exception as e:
        # En caso de error, asegurar que la tarea vuelva a la cola
        if r.exists("temp:task"):
            r.rpoplpush("temp:task", UNASSIGNED_TASKS_QUEUE)
        print(f"❌ Error al asignar tarea: {e}")

# Poner todas las tareas iniciales en la cola global
print("\n📝 Inicializando sistema de transcripción...")
for idx, filename in enumerate(audio_files):
    path = os.path.join(AUDIO_DIR, filename)
    task_data = json.dumps({"index": idx, "path": path})
    r.rpush(UNASSIGNED_TASKS_QUEUE, task_data)

print(f"✅ {len(audio_files)} tareas agregadas a la cola global")
print("\n📝 TRANSCRIPCIONES EN TIEMPO REAL:\n")

results = {}
tasks_completed = False

while True:
    show_node_statuses()
    try_assign_pending_tasks()
    
    # Procesar resultados si aún hay tareas pendientes
    if not tasks_completed:
        for key in r.scan_iter("node_stats:*"):
            node = key.split(":")[1]
            if not check_node_status(node):
                continue
                
            res = r.lpop(f"results:{node}")
            if res:
                data = json.loads(res)
                index = data["index"]
                if index not in results:
                    results[index] = data["text"]
                    print(f"\n📄 Audio {index}:")
                    print(data["text"])
                    print(f"\nTranscrito en {data.get('duration', '?')} segundos")
                    print("\n---\n")
        
        # Verificar si se completaron todas las tareas
        total_tasks = len(audio_files)
        completed_tasks = len(results)
        pending_unassigned = len(r.lrange(UNASSIGNED_TASKS_QUEUE, 0, -1))
        
        if completed_tasks == total_tasks and not tasks_completed:
            tasks_completed = True
            print("\n✅ Todas las transcripciones han sido recibidas.")
            print("👀 Sistema en espera de nuevas tareas...\n")
        else:
            print(f"\n📊 Progreso: {completed_tasks}/{total_tasks} tareas completadas ({pending_unassigned} sin asignar)")
    
    time.sleep(1)
