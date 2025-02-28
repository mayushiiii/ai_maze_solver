from flask import Flask, request, jsonify, send_file, render_template, url_for, redirect
import numpy as np
import maze_gen_base
from viewer import Viewport
from multiprocessing import Process
from PIL import Image, ImageDraw
import os
import time
#toggle between agent_single and agent_multiple and agent_multiple2
# import agent
# import agent_multiple2 as agent
import agent_multiple as agent

app = Flask(__name__)

maze = None
agent_position = None
agent_path = []
viewport_process = None
await_input = False  
await_input_event = False  


@app.route("/")
def index():
    maze_image_url = url_for("maze_image", _external=True)
    return render_template("index.html", maze_image_url=maze_image_url)

@app.route("/pause", methods=["POST"])
def pause_solver():
 
    global await_input
    await_input = True
    return jsonify({"message": "Ai pe pauza."})


@app.route("/continue", methods=["POST"])
def continue_solver():

    global await_input, await_input_event
    await_input = False
    await_input_event = True
    return jsonify({"message": "Ai-ul nu mai doarme si rezolva."})



@app.route("/generate", methods=["POST"])
def generate_maze():
    global maze, agent_position, agent_path
    method = request.form.get("method")

    if method == "random":
        if request.form.get("seed"):
            seed = int(request.form.get("seed"))
        else:
            seed = np.random.randint(0, 1000)
        maze = maze_gen_base.Maze(seed=seed)
    elif method == "image":
        image_file = request.files.get("image")
        if image_file:
            allowed_extensions = {"jpg", "jpeg", "png"}
            if not image_file.filename.lower().endswith(tuple(allowed_extensions)):
                return redirect(url_for("index", error="Invalid image format. Please upload a JPG, JPEG, or PNG file."))
            
            image_path = os.path.join("uploads", image_file.filename)
            os.makedirs("uploads", exist_ok=True)
            image_file.save(image_path)
            maze = maze_gen_base.Maze(image=image_path)
        else:
            return redirect(url_for("index", error="No image file provided."))


    if maze:
        maze.generate_image("maze.png")
        agent_position = None
        agent_path = []
        return redirect(url_for("index"))

    return jsonify({"success": False, "message": "Maze generation failed."})


@app.route("/move", methods=["POST"])
def move_agent():
    global agent_position, agent_path, await_input, await_input_event

    if not agent_position:
        x, y = maze.start
        agent_position = (2 * x + 1, 2 * y + 1)
        agent_path.append(agent_position)
        return jsonify({
            "x": agent_position[0],
            "y": agent_position[1],
            "view": get_visible_area(agent_position, 5),
            "moves": 10
        })

    # if await_input:
    #     while not await_input_event:
    #         time.sleep(0.1)
    #     await_input_event = False
    if await_input:
        return jsonify({"waiting": True, "message": "Awaiting user input"})

    data = request.json
    moves = data.get("input", "")
    area_size = data.get("area_size", 5)
    results = {}

    for i, move in enumerate(moves):
        if move == 'P': # Handle portals
            print(f"Agent position {agent_position}")
            print(f"Maze trap positions {maze.portals}")
            #tile number = (agent position, new position)
            for key,value in maze.portals.items():
                print(f"Portalul matii {maze.portals[key]}")
                print(f"Agent position {agent_position}")
                if agent_position in value:
                    print("here")
                    new_position = value[0] if agent_position == value[1] else value[1]

        else:
            new_position = calculate_new_position(agent_position, move)
        
        success = is_valid_move(new_position)

        if success:
            agent_position = new_position
            agent_path.append(agent_position)

        visible_area = get_visible_area(agent_position, area_size)

        results[f"command_{i + 1}"] = {
            "name": move,
            "successful": int(success),
            "view": visible_area,
        }

        if not success:
            break

    update_maze_image()
    time.sleep(0.5)

    return jsonify(results)



@app.route("/maze", methods=["GET"])
def maze_image():
    if os.path.exists("maze.png"):
        return send_file("maze.png", mimetype="image/png")
    return jsonify({"success": False, "message": "Maze image not found."})


@app.route("/solve", methods=["GET"])
def solve_maze():
    global viewport_process

    if viewport_process and viewport_process.is_alive():
        return jsonify({"message": "Solver is already running."})

    viewport_process = Process(target=start_viewport)
    viewport_process.start()
    
    agent.solve()

    return jsonify({"message": "Solver started!"})

@app.route("/update_planned_path", methods=["POST"])
def update_planned_path():
    global planned_moves
    data = request.json
    planned_moves = data.get("path", [])
    update_maze_image()
    return jsonify({"success": True})


def calculate_new_position(position, direction):
    x, y = position
    if direction == "N":
        return (x, y - 1)
    if direction == "S":
        return (x, y + 1)
    if direction == "E":
        return (x + 1, y)
    if direction == "W":
        return (x - 1, y)
    return position


def is_valid_move(position):
    x, y = position
    maze_height, maze_width = maze.maze.shape
    if not (0 <= x < maze_width and 0 <= y < maze_height):
        return False  # Out of bounds
    return 1 <= maze.maze[y, x] <= 255  # Walkable tiles


def get_visible_area(position, size):
    x, y = position
    maze_height, maze_width = maze.maze.shape
    size = size // 2

    min_y = max(0, y - size)
    max_y = min(maze_height, y + size + 1)
    min_x = max(0, x - size)
    max_x = min(maze_width, x + size + 1)

    visible = maze.maze[min_y:max_y, min_x:max_x]

    centered_view = np.full((2 * size + 1, 2 * size + 1), 0, dtype=int)
    offset_y = max(0, size - y)
    offset_x = max(0, size - x)
    centered_view[
        offset_y : offset_y + visible.shape[0], offset_x : offset_x + visible.shape[1]
    ] = visible

    return centered_view.tolist()

planned_moves = []  # Global list to store planned moves

def update_maze_image():
    img_path = "maze.png"
    maze.generate_image(img_path)

    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    print(f"Planned moves: {planned_moves}")

    # Draw the planned path as a dashed green line
    for i in range(len(planned_moves) - 1):
        x, y = planned_moves[i]
        start = (
            x * maze.tile_size + maze.tile_size // 4,
            y * maze.tile_size + maze.tile_size // 2,
        )
        # Determine the direction of the agent's move based on agent_path
        if i == 0 :
            if len(agent_path) > 1:
                prev_x, prev_y = agent_path[-2]
                x_next, y_next = agent_path[-1]
                if x_next != prev_x:  # Horizontal move (left or right)
                    end = (
                        x_next * maze.tile_size + maze.tile_size // 2,
                        y * maze.tile_size + maze.tile_size // 2,
                    )
                else:  # Vertical move (up or down)
                    end = (
                        x * maze.tile_size + maze.tile_size // 2,
                        y_next * maze.tile_size + maze.tile_size // 2,
                    )
            else:
                # Handle first move and assume horizontal by default
                end = (
                    x * maze.tile_size + 3 * maze.tile_size // 2,
                    y * maze.tile_size + maze.tile_size // 2,
                )
        else:
            prev_x, prev_y = planned_moves[i - 1]
            x_next, y_next = x, y
            if x_next != prev_x:  # Horizontal move (left or right)
                end = (
                    x_next * maze.tile_size + maze.tile_size // 2,
                    y * maze.tile_size + maze.tile_size // 2,
                )
            else:  # Vertical move (up or down)
                end = (
                    x * maze.tile_size + maze.tile_size // 2,
                    y_next * maze.tile_size + maze.tile_size // 2,
                )
        draw_dashed_line(draw, start, end, dash_length=10, color="green")
        img.save(img_path)
        time.sleep(0.2)

    for x, y in agent_path[:-1]:
        rect = [
            (x * maze.tile_size, y * maze.tile_size),
            ((x + 1) * maze.tile_size - 1, (y + 1) * maze.tile_size - 1),
        ]
        draw.rectangle(rect, fill="blue")

    x, y = agent_path[-1]
    rect = [
        (x * maze.tile_size, y * maze.tile_size),
        ((x + 1) * maze.tile_size - 1, (y + 1) * maze.tile_size - 1),
    ]
    draw.rectangle(rect, fill="red")

    img.save(img_path)


def draw_dashed_line(draw, start, end, dash_length, color):
    """
    Draw a dashed line between two points.
    """
    x1, y1 = start
    x2, y2 = end

    # Calculate the total length of the line
    total_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    # Skip drawing if the line length is zero
    if total_length == 0:
        return

    # Calculate the number of dashes
    num_dashes = max(1, int(total_length / (2 * dash_length)))  # Ensure at least 1 dash
    dx = (x2 - x1) / num_dashes
    dy = (y2 - y1) / num_dashes

    # Draw the dashes
    for i in range(num_dashes):
        dash_start = (
            x1 + i * 2 * dx,
            y1 + i * 2 * dy,
        )
        dash_end = (
            x1 + (i * 2 + 1) * dx,
            y1 + (i * 2 + 1) * dy,
        )
        draw.line([dash_start, dash_end], fill=color, width=3)

def start_viewport():
    viewport = Viewport("maze.png")
    viewport.run_forever()


if __name__ == "__main__":
    try:
        app.run(debug=True)
    finally:
        if viewport_process and viewport_process.is_alive():
            viewport_process.terminate()
