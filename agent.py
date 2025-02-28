import requests
import time

SERVER_URL = "http://127.0.0.1:5000"

def solve():
    print("Connecting to server...")
    response = requests.post(f"{SERVER_URL}/generate", json={})
    if response.status_code != 200:
        print(f"Failed to generate maze: {response.text}")
        return

    print("Maze generated. Starting to solve...")

    initial_response = requests.post(f"{SERVER_URL}/move", json={})
    if initial_response.status_code != 200:
        print(f"Failed to retrieve initial position: {initial_response.text}")
        return

    try:
        initial_data = initial_response.json()
    except Exception as e:
        print(f"Failed to parse initial response: {e}")
        return

    current_position = (initial_data["x"], initial_data["y"])
    visible_area = initial_data["view"]

    print(f"Starting at position: {current_position}")
    print(f"Initial visible area:\n{format_visible_area(visible_area)}")

    solve_maze_with_backtracking(current_position, visible_area)


def solve_maze_with_backtracking(start_position, visible_area):
  
    current_position = start_position
    visited = set()
    stack = [] 
    directions = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
    visited.add(current_position)

    while True:
        move = generate_single_move(current_position, visible_area, directions, visited)
        if not move:
            if not stack:
                print("Nu avem mutari bune.")
                return False  
            # Backtracking: intoarcete la ultima pozitie
            current_position = stack.pop()
            print(f"Backtracking to position: {current_position}")
            continue

        print(f"Incercam asta: {move}")
        stack.append(current_position)  # Salvam ultima pozitie

        move_response = requests.post(f"{SERVER_URL}/move", json={"input": move})
        if move_response.status_code != 200:
            print(f"Nu merge mutarea: {move_response.text}")
            return False

        try:
            result = move_response.json().get("command_1", {})
        except Exception as e:
            print(f"Server request failed: {e}")
            return False

        print(f"Server response: {result}")

        if not result.get("successful", 0):
            print(f"Move {move} failed. Trying a new direction.")
            stack.pop()  
            continue

        direction = result["name"]
        dx, dy = directions[direction]
        current_position = (current_position[0] + dx, current_position[1] + dy)
        visible_area = result["view"]
        visited.add(current_position)

        print(f"Pozitie updatata: {current_position}")
        print(f"Noua zona vizibila:\n{format_visible_area(visible_area)}")

        if contains_exit(visible_area):
            print("Am gasit eisirea")
            return True 


planned_path = []

def generate_single_move(current_position, visible_area, directions, visited):

    global planned_path
    cx, cy = current_position
    offset = len(visible_area) // 2
    move_scores = []
    heuristic = 0

    for direction, (dx, dy) in directions.items():
        nx, ny = cx + dx, cy + dy
        visible_x = offset + dx
        visible_y = offset + dy
        

        if 0 <= visible_y < len(visible_area) and 0 <= visible_x < len(visible_area[0]):
            tile = visible_area[visible_y][visible_x]
            if tile >= 1 and tile <= 255 and (nx, ny) not in visited:
                if tile == 182:
                    heuristic = -1000 
                else:
                    heuristic = abs(nx - cx) + abs(ny - cy) 
                move_scores.append((direction, heuristic))
            elif (nx, ny) in visited:
                heuristic += 50 # penalizare
                move_scores.append((direction, heuristic))

    move_scores.sort(key=lambda x: x[1])
    planned_path.clear()
    dx, dy = directions[move_scores[0][0]]
    nx, ny = cx + dx, cy + dy
    planned_path.append((nx, ny)) if move_scores else None
    send_planned_path_to_server(planned_path)
    return move_scores[0][0] if move_scores else None

def send_planned_path_to_server(planned_path):
    try:
        requests.post(f"{SERVER_URL}/update_planned_path", json={"path": planned_path})
    except Exception as e:
        print(f"Failed to update planned path: {e}")

def handle_server_response(response):
    if response.get("waiting", False):
        print("Paused, waiting for user input...")
        while True:
            # Poll server or wait for a signal that user input is received
            time.sleep(1)
            check_response = requests.post(f"{SERVER_URL}/move", json={})
            if not check_response.get("waiting", False):
                break

def contains_exit(visible_area):
  
    for row in visible_area:
        if 182 in row:
            return True
    return False


def format_visible_area(visible_area):
    return "\n".join([" ".join(map(str, row)) for row in visible_area])


if __name__ == "__main__":
    solve()
