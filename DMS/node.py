import time
import json
import psutil
import whisper
import threading
from queue import Queue
from utils import redis_client

# Umbrales de recursos
RESOURCE_THRESHOLD = 85.0  # Límite superior para considerar sobrecarga
RESOURCE_OPTIMAL = 60.0    # Límite para permitir múltiples tareas

r = redis_client.get_redis()

node_id = r.incr("global:node_counter")
node_id = f"node{node_id}"
print(f"🔧 Nodo registrado como ID: {node_id}")

# Cola para comunicación entre hilos
task_queue = Queue()
result_queue = Queue()

# Control de hilos de procesamiento
processing_threads = {}  # Diccionario para trackear hilos activos
thread_counter = 0      # Contador para IDs únicos de hilos

# Inicializar estado del nodo
r.hset(f"node_stats:{node_id}", mapping={
    "avg_time": 0.0,
    "last_time": 0.0,
    "cpu": 100.0,
    "ram": 100.0,
    "disk": 100.0,
    "tasks": 0,
    "max_tasks": 1,
    "status": "available"
})

def get_resource_usage():
    """Obtiene el uso actual de recursos"""
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    return {"cpu": cpu, "ram": ram}

def is_overloaded():
    """Verifica si el nodo está sobrecargado"""
    resources = get_resource_usage()
    return resources["cpu"] > RESOURCE_THRESHOLD or resources["ram"] > RESOURCE_THRESHOLD

def can_accept_more_tasks():
    """Determina si el nodo puede aceptar más tareas basado en uso de recursos"""
    resources = get_resource_usage()
    return (resources["cpu"] < RESOURCE_OPTIMAL and 
            resources["ram"] < RESOURCE_OPTIMAL and 
            len(processing_threads) < 5)  # Límite máximo de 5 tareas simultáneas

def update_node_status():
    """Actualiza el estado del nodo en Redis"""
    resources = get_resource_usage()
    disk = psutil.disk_usage("/").percent
    status = "overloaded" if is_overloaded() else "available"
    
    # Calcular máximo de tareas permitidas
    max_tasks = 1 if is_overloaded() else (5 if can_accept_more_tasks() else len(processing_threads))
    
    r.hset(f"node_stats:{node_id}", mapping={
        "cpu": resources["cpu"],
        "ram": resources["ram"],
        "disk": disk,
        "last_heartbeat": time.time(),
        "status": status,
        "tasks": len(processing_threads),
        "max_tasks": max_tasks
    })
    
    if status == "overloaded":
        print(f"⚠️ Nodo {node_id} sobrecargado - CPU: {resources['cpu']}% RAM: {resources['ram']}%")
    return status

def process_task(data, thread_id):
    """Procesa una tarea en un hilo específico"""
    try:
        # Incrementar contador de tareas atómicamente
        r.hincrby(f"node_stats:{node_id}", "tasks", 1)
        r.hset(f"node_stats:{node_id}", f"current_task:{thread_id}", data)
        
        # Cargar modelo y procesar tarea
        model = whisper.load_model("base")
        task = json.loads(data)
        index = task["index"]
        path = task["path"]
        
        print(f"🎯 Hilo {thread_id}: Procesando audio {index}: {path}")
        
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
        
        print(f"✅ Hilo {thread_id}: Nodo {node_id} transcribió '{path}' en {duration:.2f} s")
        with open("finalizadas.txt", "a", encoding="utf-8") as f:
            f.write(f"Nodo {node_id} terminó la tarea: {path} en {duration:.2f} s\n")  
        # Enviar resultado a la cola de resultados
        result_data = {
            "index": index,
            "text": result["text"],
            "duration": duration,
            "thread_id": thread_id
        }



        result_queue.put(result_data)
        
    finally:
        # Decrementar contador de tareas atómicamente y limpiar tarea actual
        r.hincrby(f"node_stats:{node_id}", "tasks", -1)
        r.hdel(f"node_stats:{node_id}", f"current_task:{thread_id}")
        # Eliminar el hilo del registro
        if thread_id in processing_threads:
            del processing_threads[thread_id]

def task_processor():
    """Hilo dedicado al procesamiento de tareas"""
    global thread_counter
    print(f"🎯 Iniciando procesador de tareas en nodo {node_id}")
    while True:
        try:
            data = task_queue.get()
            if data == "STOP":
                break

            # Esperar si estamos sobrecargados y tenemos más de una tarea
            while is_overloaded() and len(processing_threads) > 1:
                print("⚠️ Esperando a que se liberen recursos...")
                time.sleep(2)

            # Crear nuevo hilo para la tarea
            thread_id = f"thread_{thread_counter}"
            thread_counter += 1
            
            thread = threading.Thread(
                target=process_task,
                args=(data, thread_id),
                daemon=True
            )
            
            processing_threads[thread_id] = thread
            thread.start()

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
            
            # Verificar si podemos aceptar más tareas
            if can_accept_more_tasks() or len(processing_threads) == 0:
                # Verificar nuevas tareas
                task = r.blpop(f"task_queue:{node_id}", timeout=1)
                if task:
                    _, data = task
                    if not is_overloaded() or len(processing_threads) == 0:
                        task_queue.put(data)
                    else:
                        print(f"⚠️ Recursos altos, devolviendo tarea a la cola")
                        r.rpush(f"task_queue:{node_id}", data)
                    
        except Exception as e:
            print(f"❌ Error en gestor de control: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    print(f"🎤 Nodo {node_id} iniciando...")
    
    # Crear y arrancar hilos principales
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
        # Esperar a que terminen todos los hilos de procesamiento
        for thread in processing_threads.values():
            thread.join(timeout=5)
        print("✅ Nodo terminado correctamente")
