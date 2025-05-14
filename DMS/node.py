import time
import json
import psutil
import whisper
from utils import redis_client

RESOURCE_THRESHOLD = 80.0

r = redis_client.get_redis()

node_id = r.incr("global:node_counter")
node_id = f"node{node_id}"
print(f"🔧 Nodo registrado como ID: {node_id}")

# Inicializar estado del nodo
r.hset(f"node_stats:{node_id}", mapping={
    "avg_time": 0.0,
    "last_time": 0.0,
    "cpu": 100.0,
    "ram": 100.0,
    "disk": 100.0,
    "tasks": 0,
    "status": "available"
})

def is_overloaded():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    return cpu > RESOURCE_THRESHOLD or ram > RESOURCE_THRESHOLD

def update_node_status():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    status = "overloaded" if is_overloaded() else "available"
    
    r.hset(f"node_stats:{node_id}", mapping={
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "last_heartbeat": time.time(),
        "status": status
    })
    
    if status == "overloaded":
        print(f"⚠️ Nodo {node_id} sobrecargado - CPU: {cpu}% RAM: {ram}%")
    return status

def process_task(data):
    try:
        # Marcar nodo como ocupado
        r.hset(f"node_stats:{node_id}", "tasks", 1)
        
        # Cargar modelo y procesar tarea
        model = whisper.load_model("base")
        task = json.loads(data)
        index = task["index"]
        path = task["path"]
        
        print(f"🎯 Procesando audio {index}: {path}")
        
        # Transcribir audio
        start = time.time()
        result = model.transcribe(path)
        end = time.time()
        
        # Calcular estadísticas
        duration = end - start
        avg_time = float(r.hget(f"node_stats:{node_id}", "avg_time") or 0)
        avg_time = (avg_time + duration) / 2
        
        # Actualizar estadísticas
        r.hset(f"node_stats:{node_id}", mapping={
            "last_time": duration,
            "avg_time": avg_time,
        })
        
        print(f"✅ Nodo {node_id} transcribió '{path}' en {duration:.2f} s")
        
        # Enviar resultado
        payload = json.dumps({"index": index, "text": result["text"]})
        r.rpush(f"results:{node_id}", payload)
        
    finally:
        # Marcar nodo como disponible
        r.hset(f"node_stats:{node_id}", "tasks", 0)

print(f"🎤 Nodo {node_id} escuchando")

while True:
    # Actualizar y verificar estado
    status = update_node_status()
    
    # Intentar obtener una tarea
    try:
        task = r.blpop(f"task_queue:{node_id}", timeout=1)
        if task:
            _, data = task
            if not is_overloaded():
                process_task(data)
            else:
                print(f"⚠️ Recursos altos, devolviendo tarea a la cola")
                r.rpush(f"task_queue:{node_id}", data)
    except Exception as e:
        print(f"❌ Error procesando tarea: {e}")
        time.sleep(1)
    
    time.sleep(1)  # Pequeña pausa entre tareas
