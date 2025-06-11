# core/logic/game_state.py

def create_game_state(snake, food, obstacles=None, score=0, game_over=False):
    """
    Crea y retorna el estado completo del juego como un diccionario.
    - snake: lista de posiciones [[x, y], ...]
    - food: lista de posiciones de comida [[x, y], ...]
    - obstacles: lista de posiciones de obstáculos [[x, y], ...]
    """
    if obstacles is None:
        obstacles = []
    state = {
        "snake": snake,
        "food": food[0] if food else [10, 10],  # Por compatibilidad
        "score": score,
        "game_over": game_over,
        "obstacles": obstacles
    }
    return state

def update_score(game_state, points=1):
    """Suma puntos al score actual."""
    game_state["score"] += points
    return game_state

def set_game_over(game_state, value=True):
    """Marca el juego como terminado."""
    game_state["game_over"] = value
    return game_state

def reset_game():
    """Crea un estado inicial por defecto."""
    return create_game_state(
        snake=[[5, 5], [5, 4], [5, 3]],
        food=[[10, 10]],
        obstacles=[]
    )
