import random
import numpy as np # type: ignore
from PIL import Image, ImageDraw # type: ignore

class Maze:
    def __init__(self, seed=None, image=None):
        self.trap_positions = []  # Initialize trap_positions to avoid AttributeError

        if image is not None:
            img = Image.open(image).convert('L')
            self.maze = np.array(img)
            self.tile_size = 1
            self.height, self.width = self.maze.shape[0] // 2, self.maze.shape[1] // 2
            self.start = tuple(np.argwhere(self.maze == 64)[0] // 2)
            self.end = tuple(np.argwhere(self.maze == 182)[0] // 2)
            for trap_type in range(96, 116):
                trap_indices = np.argwhere(self.maze == trap_type)
                for (y, x) in trap_indices:
                    self.trap_positions.append((x // 2, y // 2, trap_type))
        else:
            if seed != 0:
                random.seed(seed)
            width = random.randint(10, 50)
            height = random.randint(10, 50)
            self.width = width
            self.height = height
            self.start = (random.randint(0, width - 1), random.randint(0, height - 1))
            self.end = (random.randint(0, width - 1), random.randint(0, height - 1))
            self.tile_size = 20
            self.portals = {}
            self.maze = self.create_maze()

    def create_maze(self):
        self.maze = np.zeros((self.height * 2 + 1, self.width * 2 + 1), dtype=np.uint8)
        x, y = self.start
        self.maze[2 * y + 1, 2 * x + 1] = 255
        stack = [(x, y)]

        while stack:
            x, y = stack[-1]
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and self.maze[2 * ny + 1, 2 * nx + 1] == 0:
                    self.maze[2 * ny + 1, 2 * nx + 1] = 255
                    self.maze[2 * y + 1 + dy, 2 * x + 1 + dx] = 255
                    stack.append((nx, ny))
                    break
            else:
                stack.pop()

        start_x, start_y = self.start
        end_x, end_y = self.end

        # Ensure entrance and exit are connected to open paths
        self.maze[2 * start_y + 1, 2 * start_x + 1] = 64
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            sx, sy = 2 * start_x + 1 + dx, 2 * start_y + 1 + dy
            if 0 <= sx < self.maze.shape[1] and 0 <= sy < self.maze.shape[0]:
                self.maze[sy, sx] = 255

        self.maze[2 * end_y + 1, 2 * end_x + 1] = 182
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            ex, ey = 2 * end_x + 1 + dx, 2 * end_y + 1 + dy
            if 0 <= ex < self.maze.shape[1] and 0 <= ey < self.maze.shape[0]:
                self.maze[ey, ex] = 255
                
        # Ensure no white spaces on outer walls
        self.maze[0, :] = 0
        self.maze[-1, :] = 0
        self.maze[:, 0] = 0
        self.maze[:, -1] = 0

        attempts = 10
        while attempts > 0:
            self.clear_traps()
            # if self.place_tiles() : # de adaugat is solvable daca nu esti maria.
            if self.place_tiles() and self.is_solvable():
                return self.maze
            attempts -= 1
            print(f"Failed to place tiles, {attempts} attempts left")

        # If no valid configuration is found, regenerate the maze
        return self.create_maze()

    def clear_traps(self):
        for x, y, _ in self.trap_positions:
            self.maze[y, x] = 255
        self.trap_positions = []

    def place_tiles(self):
        white_space = (np.sum(self.maze == 255))/2 -1
        max_traps = int(0.2 * (white_space/2 -1))
        total_tiles = max_traps
        tile_types = [16, 32, 224, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169]

        placed_tiles = 0
        self.trap_positions = []
        while placed_tiles < total_tiles:
            x, y = random.randint(1, self.width * 2 - 2), random.randint(1, self.height * 2 - 2)
            tile = random.choice(tile_types)

            # Ensure no special tiles are adjacent
            adjacent_positions = [
                (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)
            ]
            if any(0 <= ax < self.maze.shape[1] and 0 <= ay < self.maze.shape[0] and self.maze[ay, ax] != 255 and self.maze[ay, ax] != 0  for ax, ay in adjacent_positions):
                print("Adjacent tile is not white")
                continue
            # Ensure no special tiles near start or end
            if any((x, y) == (self.start[0] * 2 + 1, self.start[1] * 2 + 1) or (x, y) == (self.end[0] * 2 + 1, self.end[1] * 2 + 1) for x, y in adjacent_positions):
                print("Tile is near start or end")
                continue
            if self.maze[y, x] == 255:  # Place only on white tiles
                self.maze[y, x] = tile
                placed_tiles += 1

                if 96 <= tile <= 115:  # Trap tiles
                    n = (tile - 96) % 5 + 1
                    self.trap_positions.append((x, y, n))
                if 150 <= tile <= 169:
                    self.trap_positions.append((x, y, tile))
                    verify = 0
                    placed_tiles += 1
                    while verify == 0:
                        x1, y1 = random.randint(1, self.width * 2 - 2), random.randint(1, self.height * 2 - 2)
                        adjacent_positions2 = [
                            (x1 + 1, y1), (x1 - 1, y1), (x1, y1 + 1), (x1, y1 - 1), (x1 + 1, y1 + 1), (x1 - 1, y1 + 1), (x1 + 1, y1 - 1), (x1 - 1, y1 - 1)
                        ]
                        # Ensure no special tiles are adjacent
                        if (x1, y1) in adjacent_positions2 or (x1, y1) == (self.start[0] * 2 + 1, self.start[1] * 2 + 1) or (x1, y1) == (self.end[0] * 2 + 1, self.end[1] * 2 + 1):
                            continue
                        # Ensure there are no special tiles near the portal
                        if any(0 <= ax < self.maze.shape[1] and 0 <= ay < self.maze.shape[0] and self.maze[ay, ax] != 255 and self.maze[ay, ax] != 0  for ax, ay in adjacent_positions2):
                            continue
                        if self.maze[y1, x1] == 255 and (x1, y1) != (x, y):
                            verify = 1
                    self.portals[tile] = [(x, y), (x1, y1)]
                    self.maze[y1, x1] = tile
                    self.trap_positions.append((x1, y1, tile))
                    tile_types.remove(tile)
        return True

    def is_solvable(self):
        from collections import deque

        visited = set()
        queue = deque([(self.start[0] * 2 + 1, self.start[1] * 2 + 1, [])])
        portals = {tile: [] for tile in range(150, 170)}

        for x, y, tile in self.trap_positions:
            if 150 <= tile <= 169:
                portals[tile].append((x * 2 + 1, y * 2 + 1))

        while queue:
            x, y, path = queue.popleft()
            if (x, y) == (self.end[0] * 2 + 1, self.end[1] * 2 + 1):
                return True

            if (x, y) in visited:
                continue
            visited.add((x, y))
            path = path[-5:]

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= ny < self.maze.shape[0] and 0 <= nx < self.maze.shape[1]:
                    tile = self.maze[ny, nx]

                    if tile == 0 or (nx, ny) in visited:
                        continue

                    if 101 <= tile <= 105:  # Trap rewind
                        steps_back = (tile - 101) % 5 + 1
                        if len(path) >= steps_back:
                            new_x, new_y = path[-steps_back]
                            queue.append((new_x, new_y, path[:-steps_back]))
                    elif 111 <= tile <= 115:  # Trap pushback
                        steps_push = (tile - 111) % 5 + 1
                        new_x, new_y = x - dx * steps_push, y - dy * steps_push
                        if 0 <= new_y < self.maze.shape[0] and 0 <= new_x < self.maze.shape[1]:
                            queue.append((new_x, new_y, path + [(x, y)]))
                    elif 150 <= tile <= 169:  # Portal
                        other_portal = [pos for pos in portals[tile] if pos != (nx, ny)]
                        if other_portal:
                            queue.append((other_portal[0][0], other_portal[0][1], path + [(x, y)]))
                    else:
                        queue.append((nx, ny, path + [(x, y)]))

        return False
    
    def generate_image(self, filename, view_mode='full', agent_path=None):
        width, height = self.maze.shape[1] * self.tile_size, self.maze.shape[0] * self.tile_size
        img = Image.new(mode='L', size=(width, height))
        draw = ImageDraw.Draw(img)

        for i in range(self.maze.shape[0]):
            for j in range(self.maze.shape[1]):
                color = int(self.maze[i, j])
                draw.rectangle(
                    [j * self.tile_size, i * self.tile_size, (j + 1) * self.tile_size, (i + 1) * self.tile_size],
                    fill=color
                )

        for x, y, n in self.trap_positions:
            text_position = (x * self.tile_size + self.tile_size // 4, y * self.tile_size + self.tile_size // 4)
            draw.text(text_position, str(n), fill="white")

        draw.text((2 * self.start[0] * self.tile_size + self.tile_size // 4 + 20, 2 * self.start[1] * self.tile_size + self.tile_size // 4 + 20), 'O', fill='white')
        draw.text((2 * self.end[0] * self.tile_size + self.tile_size // 4 + 20, 2 * self.end[1] * self.tile_size + self.tile_size // 4 + 20), 'X', fill='white')
        img.save(filename)
