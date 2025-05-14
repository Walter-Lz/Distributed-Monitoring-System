import time
import json
import threading
import psutil
import whisper
from utils import redis_client

RESOURCE_THRESHOLD = 80.0  # Umbral de uso de recursos (CPU y RAM) en porcentaje
MAX_THREADS = 3  # Número máximo de hilos concurrentes
active_threads = 0  # Contador de hilos activos
thread_lock = threading.Lock()  # Lock para el contador de hilos

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

def update_node_status():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    status = "overloaded" if (cpu > RESOURCE_THRESHOLD or ram > RESOURCE_THRESHOLD) else "available"
    
    r.hset(f"node_stats:{node_id}", mapping={
        "cpu": cpu,
        "ram": ram,
        "disk": psutil.disk_usage("/").percent,
        "last_heartbeat": time.time(),
        "status": status,
        "active_threads": active_threads
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
        r.hincrby(f"node_stats:{node_id}", "tasks", -1)
    finally:
        with thread_lock:
            active_threads -= 1
            print(f"🧵 Hilos activos en {node_id}: {active_threads}/{MAX_THREADS}")

# Arrancar hilo de monitoreo
threading.Thread(target=report_status, daemon=True).start()

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
                r.hincrby(f"node_stats:{node_id}", "tasks", 1)
                threading.Thread(target=process_task, args=(data,), daemon=True).start()
            else:
                # Devolver la tarea a la cola si estamos sobrecargados
                print(f"⚠️ Recursos altos, devolviendo tarea a la cola")
                r.rpush(f"task_queue:{node_id}", data)
    except Exception as e:
        print(f"Error procesando tarea: {e}")
        time.sleep(1)
