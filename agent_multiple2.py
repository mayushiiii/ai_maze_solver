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
    visited = {current_position : 1}
    stack = [] 
    directions = {"N": (0, -1), "S": (0, 1), "W": (-1, 0), "E": (1, 0), "P": (0, 0)}

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
                if current_position not in visited:
                    visited[current_position] = 1
                else:
                    visited[current_position] += 1
                    
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

def generate_moves(current_position, visible_area, directions, visited, max_moves=3, last_move=None):
    global planned_path
    cx, cy = current_position
    offset = len(visible_area) // 2
    exit_position = None
    unvisited_tiles_found = False  # Track if there are unvisited or promising tiles

    # Check for the exit tile and unvisited tiles in the visible area
    for y in range(len(visible_area)):
        for x in range(len(visible_area[0])):
            absolute_x, absolute_y = cx + (x - offset), cy + (y - offset)
            tile = visible_area[y][x]

            if tile == 182:  # Exit tile found
                exit_position = (absolute_x, absolute_y)
            if 1 <= tile <= 255 and (absolute_x, absolute_y) not in visited:  # Unvisited tile
                unvisited_tiles_found = True

    # Stop if no promising tiles and no exit are visible
    if not exit_position and not unvisited_tiles_found:
        print("No promising moves visible. Stopping move generation.")
        return None

    # Recursive helper to explore paths with a max depth of `max_moves`
    def explore_path(position, visible_area, visited, depth_remaining, path, score):
        if depth_remaining == 0:  # Base case: maximum moves reached
            return score, path

        x, y = position
        offset = len(visible_area) // 2
        best_score = float("inf")
        best_path = []

        for direction, (dx, dy) in directions.items():
            if direction == 'P':
                continue  # Skip the "P" direction for now

            nx, ny = x + dx, y + dy
            visible_x = offset + dx
            visible_y = offset + dy

            # Ensure move is within bounds
            if not (0 <= visible_y < len(visible_area) and 0 <= visible_x < len(visible_area[0])):
                continue

            tile = visible_area[visible_y][visible_x]
            if tile < 1 or tile > 255:
                continue  # Invalid move

            # Calculate heuristic
            heuristic = 0
            if tile == 182:  # Exit tile
                heuristic = -10000  # Prioritize reaching the exit
            elif 96 <= tile <= 100:  # Movement decrease tile
                heuristic += 10 * (100 - tile)
            elif 101 <= tile <= 105:  # Trap rewind tile
                heuristic += 10 * (105 - tile)
            elif 106 <= tile <= 110:  # Trap pushforward tile
                heuristic += 10 * (110 - tile)
            elif 111 <= tile <= 115:  # Trap pushback tile
                heuristic += 10 * (115 - tile)
            elif 150 <= tile <= 169:  # Portal tile
                heuristic += 5
            if (nx, ny) in visited:
                visits = visited.get((nx, ny), 0)
                heuristic += visits * 10  # Penalize each revisit heavily
            else:
                heuristic -= 10  # Prioritize visiting new tiles
            # Add proximity to exit if visible
            if exit_position:
                exit_distance = abs(nx - exit_position[0]) + abs(ny - exit_position[1])
                heuristic -= 1000 * (1 / (exit_distance + 1))  # Higher priority for closer positions

            # Simulate this move
            new_score = score + heuristic
            new_path = path + [direction]
            new_visited = visited.copy()
            new_visited[(nx, ny)] = 1

            # Recursive call for the next move
            candidate_score, candidate_path = explore_path(
                (nx, ny), visible_area, new_visited, depth_remaining - 1, new_path, new_score
            )

            # Update best path if this path is better
            if candidate_score < best_score:
                best_score = candidate_score
                best_path = candidate_path

        return best_score, best_path

    # Start recursive exploration with a depth limit of `max_moves`
    _, best_path = explore_path(current_position, visible_area, visited, 1, [], 0)

    # Convert the best path into moves, limiting to a maximum of 3
    planned_path.clear()
    cx, cy = current_position
    moves = []
    for move in best_path[:3]:  # Limit to the first 3 moves
        dx, dy = directions[move]
        cx, cy = cx + dx, cy + dy
        planned_path.append((cx, cy))
        moves.append(move)

    # Send the planned path to the server
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
