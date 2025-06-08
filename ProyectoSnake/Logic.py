from functools import reduce

def create_game_state(snake_position, objectives, obstacles, score=0, game_over=False):
    """
    Crea el estado del juego con los campos esperados por el frontend.
    """
    return {
        'snake': snake_position,
        'food': objectives[0] if objectives else [10, 10],
        'score': score,
        'game_over': game_over,
        'obstacles': obstacles
    }


def deep_search(start, end, obstacles):
    """
    Perform a deep search algorithm to find the shortest path from start to end, avoiding obstacles.

    Args:
        start (tuple): Tuple representing the starting position.
        end (tuple): Tuple representing the ending position.
        obstacles (list): List of tuples representing the positions of obstacles.

    Returns:
        list: List of tuples representing the shortest path from start to end.
    """
    
    def remove(var, lista):
        """
        Helper function to remove elements from a list based on a condition.

        Args:
            var: The condition to remove elements.
            lista (list): The list to filter.

        Returns:
            list: The filtered list.
        """
        return list(filter(lambda x: not var(x), lista))

    def member(element, lista):
        """
        Helper function to check if an element exists in a list.

        Args:
            element: The element to check.
            lista (list): The list to search in.

        Returns:
            bool: True if the element exists, False otherwise.
        """
        return any(x == element for x in lista)

    def neighbors(node, obstacles, end):
        """
        Helper function to find neighboring nodes of a given node.

        Args:
            node (tuple): Tuple representing the coordinates of the node.
            obstacles (list): List of tuples representing the positions of obstacles.
            end (tuple): Tuple representing the ending position.

        Returns:
            list: List of tuples representing neighboring nodes.
        """
        x, y = node
        dx = [1, -1, 0, 0]  # Increases X
        dy = [0, 0, 1, -1]  # Increases Y

        # Generates all the posible neighbor coordinates
        potential_neighbours = map(lambda i: (x + dx[i], y + dy[i]), range(4))

        # Filtrates valid neighbors
        valid_neighbours = filter(lambda coord: coord not in obstacles and coord[0] >= 0 and coord[1] >= 0, potential_neighbours)

        # Sorts the neighbors acording how close they are to the final node
        sorted_neighbours = sorted(valid_neighbours, key=lambda coord: abs(coord[0] - end[0]) + abs(coord[1] - end[1]))

        return sorted_neighbours


    def extend(path, obstacles, visited, end):
        """
        Helper function to extend the path from a given position.

        Args:
            path (list): List representing the current path.
            obstacles (list): List of tuples representing the positions of obstacles.
            visited (set): Set of visited positions.
            end (tuple): Tuple representing the ending position.

        Returns:
            list: List of tuples representing the extended path.
        """
        return remove(lambda x: member(x, path) or member(x, visited), neighbors(path[-1], obstacles, end))

    def prof(start, end, obstacles):
        """
        Helper function to perform a depth-first search.

        Args:
            start (tuple): Tuple representing the starting position.
            end (tuple): Tuple representing the ending position.
            obstacles (list): List of tuples representing the positions of obstacles.

        Returns:
            list: List of tuples representing the shortest path from start to end.
        """
        return prof_aux(end, [(start,)], obstacles, set())

    def prof_aux(end, paths, obstacles, visited):
        """
        Helper function to perform depth-first search recursively.

        Args:
            end (tuple): Tuple representing the ending position.
            paths (list): List of tuples representing the current paths.
            obstacles (list): List of tuples representing the positions of obstacles.
            visited (set): Set of visited positions.

        Returns:
            list: List of tuples representing the shortest path from start to end.
        """
        if not paths:
            return None  # No valid route found
        elif end == paths[0][-1]:
            return list(reversed(paths[0]))  # Valid route found
        else:
            new_paths = reduce(lambda acc, path: acc + [path + (neighbor,) for neighbor in extend(path, obstacles, visited, end)], paths, [])
            already_visited = visited.union(set(route[-1] for route in new_paths))
            best_path = min(new_paths, key=lambda path: sum(abs(coord[0] - end[0]) + abs(coord[1] - end[1]) for coord in path))
            return prof_aux(end, [best_path], obstacles, already_visited)


    # Execution of the shortest path search
    shortest_path = prof(start, end, obstacles)

    return list(reversed(shortest_path))
