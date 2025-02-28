import requests
import time

SERVER_URL = "http://127.0.0.1:5000"

def main():
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
        print(f"No server response: {e}")
        return

    current_position = (initial_data["x"], initial_data["y"])
    visible_area = initial_data["view"]

    print(f"Starting at position: {current_position}")
    print(f"Initial visible area:\n{format_visible_area(visible_area)}")

    visited = set()
    directions = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
    visited.add(current_position)

    while True:
        move = generate_single_move(current_position, visible_area, directions, visited)
        if not move:
            print("Nu mai avem mutari nerezolvate. Maze gresit.")
            break

        print(f"Incercam asta: {move}")

        move_response = requests.post(f"{SERVER_URL}/move", json={"input": move})
        if move_response.status_code != 200:
            print(f"Move failed: {move_response.text}")
            break

        try:
            result = move_response.json().get("command_1", {})
        except Exception as e:
            print(f"Failed to parse server response: {e}")
            break

        print(f"Server response: {result}")

        if not result.get("successful", 0):
            print(f"Move {move} failed. Trying a new direction.")
            continue

        direction = result["name"]
        dx, dy = directions[direction]
        current_position = (current_position[0] + dx, current_position[1] + dy)
        visible_area = result["view"]
        visited.add(current_position)

        print(f"Pozitie updatata: {current_position}")
        print(f"Noua ta zona :\n{format_visible_area(visible_area)}")

        if contains_exit(visible_area):
            print("Maze rezolvat! ")
            return


    time.sleep(0.5) 

def generate_single_move(current_position, visible_area, directions, visited):
 
    cx, cy = current_position
    failed_directions = set()

    offset = len(visible_area) // 2

    for direction, (dx, dy) in directions.items():
        if direction in failed_directions:
            continue

        nx, ny = cx + dx, cy + dy
        visible_x = offset + dx
        visible_y = offset + dy

        if 0 <= visible_y < len(visible_area) and 0 <= visible_x < len(visible_area[0]):
            tile = visible_area[visible_y][visible_x]
            if tile >= 1 and tile <= 255 and (nx, ny) not in visited:
                return direction
            else:
                failed_directions.add(direction)
        else:
            failed_directions.add(direction)  

    return None  



def is_valid_move(new_position, current_position, visible_area, visited):

    cx, cy = current_position
    nx, ny = new_position
    offset = len(visible_area) // 2 
  
    visible_x = nx - cx + offset
    visible_y = ny - cy + offset

    if 0 <= visible_y < len(visible_area) and 0 <= visible_x < len(visible_area[0]):
        tile = visible_area[visible_y][visible_x]
        print(f"Checking move to {new_position}: Tile value = {tile}")
        if tile == 0: 
            print(f"Miscarea este {new_position} proasta (wall).")
            return False
        return tile >=1 and tile <= 255 and new_position not in visited
    print(f"Vezi ca iesi din labirint")
    return False

def contains_exit(visible_area):

    for row in visible_area:
        if 182 in row:
            return True
    return False

def format_visible_area(visible_area):

    return "\n".join([" ".join(map(str, row)) for row in visible_area])

if __name__ == "__main__":
    main()