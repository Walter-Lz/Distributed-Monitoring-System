import random
import time
import tkinter as tk
import redis
import json

# Conexión a Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_path_from_node(start, end, obstacles):
    r.rpush("snake:movement:request", json.dumps({
        "start": start,
        "end": end,
        "obstacles": obstacles
    }))
    _, msg = r.blpop("snake:movement:response")
    data = json.loads(msg)
    return [tuple(x) for x in data["path"]]

def notify_score_event(event):
    r.rpush("snake:score:event", json.dumps({"event": event}))

def get_score():
    score = r.get("snake:score:value")
    return int(score) if score else 0

root = tk.Tk()
root.title("Snake Game")

canvas = tk.Canvas(root, width=400, height=360, bg='black')
canvas.pack()

snake = canvas.create_rectangle(0, 0, 20, 20, fill='green')
objectives = []
obstacles = []

score_label = tk.Label(root, text="Score: 0", fg="black")
score_label.pack()

time_label = tk.Label(root, text="Time: 0", fg="black")
time_label.pack()

movements_label = tk.Label(root, text="Movements: 0", fg="black")
movements_label.pack()

score = 0
movements = 0

def draw_grid():
    for i in range(0, 400, 20):
        canvas.create_line(i, 0, i, 360, fill='gray')
    for j in range(0, 360, 20):
        canvas.create_line(0, j, 400, j, fill='gray')

def create_obstacles():
    global obstacles
    for _ in range(20):
        while True:
            x = random.randint(1, 19)
            y = random.randint(1, 17)
            if (x, y) not in obstacles and (x, y) not in objectives and (x, y) != (0, 0):
                obstacles.append((x, y))
                canvas.create_rectangle(x * 20, y * 20, (x + 1) * 20, (y + 1) * 20, fill='blue')
                break

def create_random_objective():
    while True:
        x = random.randint(0, 19)
        y = random.randint(0, 17)
        too_close_to_obstacle = False
        for obstacle in obstacles:
            if abs(x - obstacle[0]) <= 1 and abs(y - obstacle[1]) <= 1:
                too_close_to_obstacle = True
                break
        if not too_close_to_obstacle:
            canvas.create_oval(x * 20 + 5, y * 20 + 5, x * 20 + 15, y * 20 + 15, fill='red')
            objectives.append((x, y))
            break

def place_objective(event):
    x = event.x // 20
    y = event.y // 20
    if (x, y) not in obstacles and (x, y) not in objectives:
        canvas.create_oval(x * 20 + 5, y * 20 + 5, x * 20 + 15, y * 20 + 15, fill='red')
        objectives.append((x, y))

def move_snake_auto(path_to_goal, current_position):
    global movements, goal

    if not path_to_goal:
        no_objetivos_label = tk.Label(root, text="¡Ya no hay objetivos!", fg="red", font=("Arial", 16))
        no_objetivos_label.place(relx=0.5, rely=0.5, anchor="center")
        root.update()
        return

    for next_position in path_to_goal:
        canvas.move(snake, (next_position[0] - current_position[0]) * 20, (next_position[1] - current_position[1]) * 20)
        current_position = next_position
        movements += 1
        movements_label.config(text=f"Movimientos: {movements}")
        time.sleep(0.3)
        root.update()

    if current_position == goal:
        notify_score_event("objective_reached")
        score_label.config(text=f"Puntuación: {get_score()}")
        obj_ids = canvas.find_overlapping(goal[0] * 20, goal[1] * 20, goal[0] * 20 + 20, goal[1] * 20 + 20)
        if obj_ids:
            canvas.itemconfig(obj_ids[-1], fill='')
        objectives.pop(0)
        if len(objectives) != 0:
            goal = objectives[0]
            path = get_path_from_node(current_position, goal, obstacles)
            move_snake_auto(path, current_position)
        else:
            no_objetivos_label = tk.Label(root, text="¡Ya no hay objetivos!", fg="red", font=("Arial", 16))
            no_objetivos_label.place(relx=0.5, rely=0.5, anchor="center")
            root.update()
            return

def update_score_and_time():
    global start_time
    current_time = int(time.time() - start_time)
    time_label.config(text=f"Time: {current_time}")
    if len(objectives) > 0:
        root.after(1000, update_score_and_time)

draw_grid()
create_obstacles()
create_random_objective()
goal = objectives[0]
start_time = time.time()
update_score_and_time()
canvas.bind("<Button-1>", place_objective)
path = get_path_from_node((0, 0), goal, obstacles)
move_snake_auto(path, (0, 0))

root.mainloop()