import time
import json
import threading
import psutil
import whisper
from utils import redis_client

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
    "tasks": 0
})

def report_status():
    while True:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        r.hset(f"node_stats:{node_id}", mapping={
            "cpu": cpu,
            "ram": ram,
            "disk": disk
        })
        time.sleep(1)

def process_task(data):
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

# Arrancar hilo de monitoreo
threading.Thread(target=report_status, daemon=True).start()

print(f"Nodo {node_id} escuchando")
while True:
    _, data = r.blpop(f"task_queue:{node_id}")
    r.hincrby(f"node_stats:{node_id}", "tasks", 1)
    threading.Thread(target=process_task, args=(data,), daemon=True).start()
