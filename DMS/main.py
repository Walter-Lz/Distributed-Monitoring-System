import time
from utils import redis_client
from supabase import create_client, Client

SUPABASE_URL = "https://kybwqugpfsfzkyuhngwv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt5YndxdWdwZnNmemt5dWhuZ3d2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc2MzEyNjAsImV4cCI6MjA2MzIwNzI2MH0.oDJ04R3CZmcuPPmFYIb_8t1Rz5MkK0Ji8Wl1Ur40yEw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Limpia la tabla de logs de Supabase
supabase.table("Log").delete().neq("id", 0).execute()

# Limpia Redis
r = redis_client.get_redis()
r.flushall()

NODE_TIMEOUT = 5

# Cola global para tareas (puedes usarla para Snake)
UNASSIGNED_TASKS_QUEUE = "global:unassigned_tasks"
active_nodes = set()

def check_node_status(node_id):
    stats = r.hgetall(f"node_stats:{node_id}")
    if not stats:
        return False
    try:
        last_heartbeat = float(stats.get("last_heartbeat", 0))
        current_time = time.time()
        time_diff = current_time - last_heartbeat
        is_alive = time_diff <= NODE_TIMEOUT
        has_valid_stats = all(key in stats for key in ["cpu", "ram", "disk", "status"])
        if not is_alive or not has_valid_stats:
            return False
        return True
    except (ValueError, TypeError):
        return False

def show_node_statuses():
    print("\nEstado actual de los nodos:")
    node_keys = [key for key in r.scan_iter("node_stats:*")]
    for key in node_keys:
        node = key.split(":")[1]
        stats = r.hgetall(key)
        if not check_node_status(node):
            continue
        try:
            cpu = float(stats.get("cpu", 100))
            ram = float(stats.get("ram", 100))
            disk = float(stats.get("disk", 100))
            tasks = int(stats.get("tasks", 0))
            max_tasks = int(stats.get("max_tasks", 1))
            node_status = stats.get("status", "available")
            print(f"🟢 Nodo {node} ➤ CPU: {cpu:.1f}% | RAM: {ram:.1f}% | Disco: {disk:.1f}% | Tareas: {tasks}/{max_tasks} | Estado: {node_status}")
        except (ValueError, TypeError):
            print(f"⚠️ Nodo {node} tiene datos de estado inválidos")

print("\n📝 Sistema distribuido listo para recibir tareas (ejemplo: Snake)...\n")

while True:
    show_node_statuses()
    snake_task = {
    "type": "snake_move",
    "player_id": "player1",
    "direction": "up",
    "timestamp": time.time()
    }
    r.lpush(UNASSIGNED_TASKS_QUEUE, json.dumps(snake_task))
    print("🚀 Tarea de Snake enviada a la cola global.")
    time.sleep(2)