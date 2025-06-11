# core/logic/scenario.py

import random

BOARD_WIDTH = 20
BOARD_HEIGHT = 20

def random_position(exclude=None):
    """Genera una posición aleatoria no incluida en exclude."""
    if exclude is None:
        exclude = []
    while True:
        pos = [random.randint(0, BOARD_WIDTH - 1), random.randint(0, BOARD_HEIGHT - 1)]
        if pos not in exclude:
            return pos

def add_food(game_state, position=None):
    """Agrega comida en una posición nueva (aleatoria si no se da)."""
    exclude = game_state["snake"] + game_state.get("obstacles", [])
    pos = position if position else random_position(exclude)
    game_state["food"] = pos
    return game_state

def add_obstacle(game_state, position=None):
    """Agrega un obstáculo (aleatorio si no se da)."""
    if "obstacles" not in game_state:
        game_state["obstacles"] = []
    exclude = game_state["snake"] + [game_state["food"]] + game_state["obstacles"]
    pos = position if position else random_position(exclude)
    game_state["obstacles"].append(pos)
    return game_state

def remove_food(game_state):
    """Quita la comida (usado al comer)."""
    game_state["food"] = None
    return game_state

def clear_obstacles(game_state):
    """Elimina todos los obstáculos."""
    game_state["obstacles"] = []
    return game_state
