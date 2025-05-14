import time
import json
import threading
import psutil
import whisper
from utils import redis_client

RESOURCE_THRESHOLD = 80.0 
MAX_THREADS = 3  
active_threads = 0  
thread_lock = threading.Lock()  

r = redis_client.get_redis()

node_id = r.incr("global:node_counter")
node_id = f"node{node_id}"
print(f"🔧 Nodo registrado como ID: {node_id}")

r.hset(f"node_stats:{node_id}", mapping={
    "avg_time": 0.0,
    "last_time": 0.0,
    "cpu": 100.0,
    "ram": 100.0,
    "disk": 100.0,
    "tasks": 0,
    "status": "available",
    "active_threads": 0
})

def is_overloaded():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    return cpu > RESOURCE_THRESHOLD or ram > RESOURCE_THRESHOLD

def reset_task_counter():
    with thread_lock:
        # Contar tareas reales pendientes
        pending_tasks = len(r.lrange(f"task_queue:{node_id}", 0, -1))
        # Establecer el contador al número real de tareas activas
        r.hset(f"node_stats:{node_id}", "tasks", active_threads + pending_tasks)
        print(f"🔄 Contador de tareas reiniciado: {active_threads + pending_tasks} tareas activas")
        return active_threads + pending_tasks

def update_task_counter(increment=True):
    with thread_lock:
        try:
            current_tasks = int(r.hget(f"node_stats:{node_id}", "tasks") or 0)
            # Si detectamos un valor negativo, reiniciar el contador
            if current_tasks < 0:
                return reset_task_counter()
                
            new_tasks = current_tasks + (1 if increment else -1)
            # Asegurar que nunca sea negativo
            new_tasks = max(0, new_tasks)
            # Verificar que el número de tareas tenga sentido
            if new_tasks < active_threads:
                return reset_task_counter()
                
            r.hset(f"node_stats:{node_id}", "tasks", new_tasks)
            return new_tasks
        except Exception as e:
            print(f"Error actualizando contador de tareas: {e}")
            return reset_task_counter()

def update_node_status():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    status = "overloaded" if (cpu > RESOURCE_THRESHOLD or ram > RESOURCE_THRESHOLD) else "available"
    
    # Verificar y corregir el contador de tareas si es necesario
    current_tasks = int(r.hget(f"node_stats:{node_id}", "tasks") or 0)
    if current_tasks < 0 or current_tasks < active_threads:
        current_tasks = reset_task_counter()
    
    r.hset(f"node_stats:{node_id}", mapping={
        "cpu": cpu,
        "ram": ram,
        "disk": psutil.disk_usage("/").percent,
        "last_heartbeat": time.time(),
        "status": status,
        "active_threads": active_threads,
        "tasks": current_tasks
    })
    
    if status == "overloaded":
        print(f"⚠️ Nodo {node_id} sobrecargado - CPU: {cpu}% RAM: {ram}%")
    return status

def report_status():
    while True:
        update_node_status()
        time.sleep(1)

def process_task(data):
    global active_threads
    try:
        model = whisper.load_model("base")
        task = json.loads(data)
        index = task["index"]
        path = task["path"]

        start = time.time()
        result = model.transcribe(path)
        end = time.time()

        duration = end - start
        avg_time = float(r.hget(f"node_stats:{node_id}", "avg_time") or 0)
        avg_time = (avg_time + duration) / 2

        r.hset(f"node_stats:{node_id}", mapping={
            "last_time": duration,
            "avg_time": avg_time,
        })

        print(f"Nodo {node_id} transcribió '{path}' en {duration:.2f} s")

        payload = json.dumps({"index": index, "text": result["text"]})
        r.rpush(f"results:{node_id}", payload)
        tasks_remaining = update_task_counter(increment=False)
        print(f"📊 Tareas activas restantes: {tasks_remaining}")
    finally:
        with thread_lock:
            active_threads -= 1
            print(f"🧵 Hilos activos en {node_id}: {active_threads}/{MAX_THREADS}")

# Arrancar hilo de monitoreo
threading.Thread(target=report_status, daemon=True).start()

# Al inicio del nodo, reiniciar el contador
print(f"🔄 Iniciando nodo {node_id} - Reiniciando contadores...")
reset_task_counter()

print(f"Nodo {node_id} escuchando (máximo {MAX_THREADS} tareas simultáneas)")
while True:
    # Verificar recursos antes de aceptar nueva tarea
    status = update_node_status()
    if status == "overloaded":
        print(f"😴 Nodo {node_id} esperando a que bajen los recursos...")
        time.sleep(5)  # Esperar más tiempo cuando está sobrecargado
        continue
        
    # Verificar si podemos crear más hilos
    with thread_lock:
        if active_threads >= MAX_THREADS:
            print(f"🔒 Límite de hilos alcanzado ({active_threads}/{MAX_THREADS}). Esperando...")
            time.sleep(1)
            continue
    
    try:
        # Intentar obtener una tarea con timeout para no bloquear
        task = r.blpop(f"task_queue:{node_id}", timeout=1)
        if task:
            _, data = task
            # Verificar recursos nuevamente antes de crear el hilo
            if not is_overloaded():
                with thread_lock:
                    active_threads += 1
                    print(f"🧵 Hilos activos en {node_id}: {active_threads}/{MAX_THREADS}")
                current_tasks = update_task_counter(increment=True)
                print(f"📊 Total de tareas activas: {current_tasks}")
                threading.Thread(target=process_task, args=(data,), daemon=True).start()
            else:
                # Devolver la tarea a la cola si estamos sobrecargados
                print(f"⚠️ Recursos altos, devolviendo tarea a la cola")
                r.rpush(f"task_queue:{node_id}", data)
    except Exception as e:
        print(f"Error procesando tarea: {e}")
        time.sleep(1)
