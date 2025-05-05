import os
import json
import time
from utils import redis_client

r = redis_client.get_redis()
AUDIO_DIR = "audios"

audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]
if not audio_files:
    print("❌ No hay audios para procesar.")
    exit()

def show_node_statuses():
    print("\nEstado actual de los nodos:")
    node_keys = [key for key in r.scan_iter("node_stats:*")]
    for key in node_keys:
        node = key.split(":")[1]
        stats = r.hgetall(key)
        print(f"🖥️ Nodo {node} ➤ CPU: {stats.get('cpu', '?')}% | RAM: {stats.get('ram', '?')}% | Disco: {stats.get('disk', '?')}% | Tareas: {stats.get('tasks', '0')}")

def get_best_node():
    candidates = []
    for key in r.scan_iter("node_stats:*"):
        node = key.split(":")[1]
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

for idx, filename in enumerate(audio_files):
    path = os.path.join(AUDIO_DIR, filename)
    node = None

    while not node:
        node = get_best_node()
        if not node:
            print("⏳ Esperando nodos disponibles...")
            time.sleep(1)

    print(f"📤 Enviando '{filename}' a {node}")
    payload = json.dumps({"index": idx, "path": path})
    r.rpush(f"task_queue:{node}", payload)
    r.hincrby(f"node_stats:{node}", "tasks", 1)

results = {}
print("\n📝 TRANSCRIPCIONES EN TIEMPO REAL:\n")
while len(results) < len(audio_files):
    for key in r.scan_iter("node_stats:*"):
        node = key.split(":")[1]
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

        show_node_statuses()
    time.sleep(1)

print("\nTodas las transcripciones han sido recibidas.")
