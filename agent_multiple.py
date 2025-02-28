import requests
import time

SERVER_URL = "http://127.0.0.1:5000"
global max_moves

    

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
    directions = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0), "P": (0, 0)}
    visited.add(current_position)

    last_move = None  # Initialize last_move
    max_moves = 10  # Set the initial max_moves value
    moves_history = []  # Store the history of moves
    while True:
        moves_server = []
        moves = generate_moves(current_position, visible_area, directions, visited, max_moves, last_move=last_move)
        if not moves:
            if not stack:
                print("Nu avem mutari bune.")
                return False  
            # Backtracking: Return to the last position
            current_position = stack.pop()
            print(f"Backtracking to position: {current_position}")
            last_move = None  # Reset last_move after backtracking
            continue

        for move in moves:
            print(f"Incercam asta: {move}")
            stack.append(current_position)  # Save the current position before moving

                      #varific trapuri , determin ce se va intampla
            # trimit catre server miscarile daca exista.
            # updatam pozitia daca se poate.
            max_moves = 10
            area_size = 5
            current_tile = visible_area[len(visible_area) // 2][len(visible_area) // 2]
            if current_tile == 16: # TODO: XRAY TILE MORTI RANITI
                moves_server.append(move)
                pass
            elif current_tile == 32: # Fog tile - reduces vision
                # se trimite catre sv noul size
                area_size = 3
                moves_server.append(move)
            elif current_tile == 224: # Tower tile - increased vision
                area_size = 7 
                moves_server.append(move)
            elif 96 <= current_tile <= 100: # Trap movement: scade max_moves pt o tura!
                print("Trap movement tile detected")
                max_moves -= 101-current_tile
                moves_server.append(move)
            elif 101 <= current_tile <= 105:  # Trap rewind: da rewind la ultimele n miscari
                print("Rewind tile detected")
                rewind_steps = 106 - current_tile
                for _ in range(rewind_steps):
                    if not moves_history:
                        print("Nu se pot face mutari inapoi.")
                        break
                    moves_server.append(moves_history.pop())
            elif 106 <= current_tile <= 110:  # Trap pushforward: da pushforward la ultimele n miscari
                print("Pushforward tile detected")
                pushforward_steps = 111 - current_tile
                for _ in range(pushforward_steps):
                    if direction == 'N':
                        moves_server.append('N')
                    elif direction == 'S':
                        moves_server.append('S')
                    elif direction == 'E':
                        moves_server.append('E')
                    elif direction == 'W':
                        moves_server.append('W')
                    
            elif 111 <= current_tile <= 115:  # Trap pushback: da pushback la ultimele n miscari
                print("Pushback tile detected")
                pushback_steps = 116 - current_tile
                for _ in range(pushback_steps):
                    if direction == 'N':
                        moves_server.append('S')
                    elif direction == 'S':
                        moves_server.append('N')
                    elif direction == 'E':
                        moves_server.append('W')
                    elif direction == 'W':
                        moves_server.append('E')
                    visited.add(current_position)
                    
            elif 150 <= current_tile <= 169:  # Portal: teleporteaza agentul
                print(f"Portal tile detected: {current_tile}")
                print(f"Moves history: {moves_history}")
                if moves_history[-1] == 'P':
                    moves_server.append(move)
                else:
                    moves_server.append('P') # doamne ajuta sa mearga
            else:
                moves_server.append(move)
        print(f"Moves server: {moves_server}")
        print(f"Moves history: {moves_history}")
        moves_history.append(moves_server[-1])  # Add the move to the history
        move_response = requests.post(f"{SERVER_URL}/move", json={"input": moves_server, "area_size": area_size})
        if move_response.status_code != 200:
            print(f"Nu merge mutarea: {move_response.text}")
            stack.pop()  # Undo this move
            continue

        try:
            for i in range(len(moves_server)):
                idx = i + 1
                result = move_response.json().get(f"command_{idx}", {})
                print(f"Server response: {result}")
                if not result.get("successful", 0):
                    print(f"Move {move} failed. Trying a new direction.")
                    moves_server.pop()  # Undo this move
                    continue

                # Update the position and visible area
                direction = result["name"]
                dx, dy = directions[direction]
                current_position = (current_position[0] + dx, current_position[1] + dy)
                visible_area = result["view"]
                visited.add(current_position)
                    
                print(f"Pozitie updatata: {current_position}")
                print(f"Noua zona vizibila:\n{format_visible_area(visible_area)}")
                
                    
                if contains_exit(visible_area, current_position):
                    print("Am gasit iesirea")
                    return True 

                # Update the last_move to the successful move
                last_move = direction
        except Exception as e:
            print(f"Server request failed: {e}")
            return False





planned_path = []

def generate_moves(current_position, visible_area, directions, visited, max_moves=10, last_move=None):
    global planned_path  # Use global planned_path to communicate with the server
    cx, cy = current_position
    offset = len(visible_area) // 2
    move_scores = []
    exit_position = None

    # Check for the exit tile in the visible area
    for y in range(len(visible_area)):
        for x in range(len(visible_area[0])):
            if visible_area[y][x] == 182:
                exit_position = (cx + (x - offset), cy + (y - offset))  # Absolute position of the exit

    # Score and prioritize moves
    for direction, (dx, dy) in directions.items():
        if direction != 'P':
            nx, ny = cx + dx, cy + dy
            visible_x = offset + dx
            visible_y = offset + dy

            if 0 <= visible_y < len(visible_area) and 0 <= visible_x < len(visible_area[0]):
                tile = visible_area[visible_y][visible_x]
                if tile >= 1 and tile <= 255 and (nx, ny) not in visited:
                    heuristic = -10000 if tile == 182 else abs(nx - cx) + abs(ny - cy)
                    # Penalize moves that are not in the same direction as the last move
                    if last_move and last_move != direction:
                        heuristic += 10  # Adjust penalty as needed
                        
                    if 96 <= tile <= 100: # Movement decrease tile
                        heuristic += 10 * (100 - tile)

                    if 101 <= tile <= 105: # Trap rewind tile
                        heuristic += 10 * (105 - tile)

                    if 106 <= tile <= 110: # Trap pushforward tile
                        heuristic += 10 * (110 - tile)

                    if 111 <= tile <= 115: # Trap pushback tile
                        heuristic += 10 * (115 - tile)

                    if 150 <= tile <= 169: # Portal tile
                        heuristic += 5
                    
                    # Prioritize moving toward the exit if visible
                    if exit_position:
                        exit_distance = abs(nx - exit_position[0]) + abs(ny - exit_position[1])
                        heuristic -= 1000 * (1 / (exit_distance + 1))  # Higher priority for closer positions

                    
                    move_scores.append((direction, heuristic))

    # Sort moves based on heuristic score
    move_scores.sort(key=lambda x: x[1])

    planned_path.clear()
    moves = []

    # Generate up to `max_moves` moves
    for i, (direction, _) in enumerate(move_scores):
        if i >= max_moves:
            break
        dx, dy = directions[direction]
        cx, cy = cx + dx, cy + dy
        planned_path.append((cx, cy))
        moves.append(direction)

    send_planned_path_to_server(planned_path)
    
    return moves if moves else None





def send_planned_path_to_server(planned_path):
    try:
        requests.post(f"{SERVER_URL}/update_planned_path", json={"path": planned_path})
    except Exception as e:
        print(f"Failed to update planned path: {e}")


def handle_server_response(response):
    if response.get("waiting", False):
        print("Paused, waiting for user input...")
        while True:
            time.sleep(1)
            check_response = requests.post(f"{SERVER_URL}/move", json={})
            if not check_response.get("waiting", False):
                break


def contains_exit(visible_area, current_position):
    """
    Check if the agent is at the exit tile (182).
    """
    cx, cy = current_position
    offset = len(visible_area) // 2
    tile_at_position = visible_area[offset][offset]  # Tile at the agent's current position
    return tile_at_position == 182


def format_visible_area(visible_area):
    return "\n".join([" ".join(map(str, row)) for row in visible_area])


if __name__ == "__main__":
    solve()
