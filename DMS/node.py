import time
import json
import psutil
import whisper
import threading
from queue import Queue
from utils import redis_client

RESOURCE_THRESHOLD = 80.0

r = redis_client.get_redis()

node_id = r.incr("global:node_counter")
node_id = f"node{node_id}"
print(f"🔧 Nodo registrado como ID: {node_id}")

# Cola para comunicación entre hilos
task_queue = Queue()
result_queue = Queue()

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
        # Incrementar contador de tareas atómicamente
        r.hincrby(f"node_stats:{node_id}", "tasks", 1)
        r.hset(f"node_stats:{node_id}", "current_task", data)
        
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
        
        # Enviar resultado a la cola de resultados
        result_data = {
            "index": index,
            "text": result["text"],
            "duration": duration
        }
        result_queue.put(result_data)
        
    finally:
        # Decrementar contador de tareas atómicamente y limpiar tarea actual
        r.hincrby(f"node_stats:{node_id}", "tasks", -1)
        r.hdel(f"node_stats:{node_id}", "current_task")

def task_processor():
    """Hilo dedicado al procesamiento de tareas"""
    print(f"🎯 Iniciando procesador de tareas en nodo {node_id}")
    while True:
        try:
            data = task_queue.get()
            if data == "STOP":
                break
            process_task(data)
        except Exception as e:
            print(f"❌ Error en procesador de tareas: {e}")
        finally:
            task_queue.task_done()

def control_manager():
    """Hilo dedicado a la gestión de control y comunicación con el main"""
    print(f"🔄 Iniciando gestor de control en nodo {node_id}")
    while True:
        try:
            # Actualizar estado del nodo
            status = update_node_status()
            
            # Verificar resultados pendientes y enviarlos al main
            while not result_queue.empty():
                result_data = result_queue.get()
                payload = json.dumps(result_data)
                r.rpush(f"results:{node_id}", payload)
                result_queue.task_done()
            
            # Verificar nuevas tareas
            task = r.blpop(f"task_queue:{node_id}", timeout=1)
            if task:
                _, data = task
                if not is_overloaded():
                    task_queue.put(data)
                else:
                    print(f"⚠️ Recursos altos, devolviendo tarea a la cola")
                    r.rpush(f"task_queue:{node_id}", data)
                    
        except Exception as e:
            print(f"❌ Error en gestor de control: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    print(f"🎤 Nodo {node_id} iniciando...")
    
    # Crear y arrancar hilos
    processor_thread = threading.Thread(target=task_processor, daemon=True)
    control_thread = threading.Thread(target=control_manager, daemon=True)
    
    processor_thread.start()
    control_thread.start()
    
    try:
        # Mantener el programa principal vivo
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⚠️ Señal de terminación recibida")
        # Enviar señal de parada al procesador
        task_queue.put("STOP")
        # Esperar a que terminen las tareas pendientes
        task_queue.join()
        result_queue.join()
        print("✅ Nodo terminado correctamente")
