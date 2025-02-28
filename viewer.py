import pygame
import os
import requests

SERVER_URL = "http://127.0.0.1:5000"  # Flask server URL

class Viewport:
    def __init__(self, img_path):
        pygame.init()
        self.screen_width = 1920
        self.screen_height = 1080
        self.screen = pygame.display.set_mode([self.screen_width, self.screen_height])
        pygame.display.set_caption("Maze Viewer")

        self.img_path = img_path
        self.maze_img = pygame.image.load(self.img_path)
        self.maze_rect = self.maze_img.get_rect()

        self.zoom_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        self.last_mouse_pos = (0, 0)

        self.is_paused = False  

    def draw_maze(self):
        try:
            if os.path.exists(self.img_path):
                self.maze_img = pygame.image.load(self.img_path)

            zoomed_width = int(self.maze_rect.width * self.zoom_factor)
            zoomed_height = int(self.maze_rect.height * self.zoom_factor)
            zoomed_img = pygame.transform.scale(self.maze_img, (zoomed_width, zoomed_height))

            self.screen.blit(zoomed_img, (self.offset_x, self.offset_y))
        except Exception as e:
            print(f"Error loading maze image: {e}")

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        endpoint = "/continue" if not self.is_paused else "/pause"
        response = requests.post(f"{SERVER_URL}{endpoint}")
        if response.status_code == 200:
            print(f"Server-ul are pauza : {'Resumed' if not self.is_paused else 'Paused'}")
        else:
            print(f"Eroare la server: {response.text}")

    def run_forever(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEWHEEL:
                    old_zoom = self.zoom_factor
                    self.zoom_factor += event.y * 0.1  
                    self.zoom_factor = max(0.1, self.zoom_factor)  
                    mouse_x, mouse_y = pygame.mouse.get_pos()

                    self.offset_x -= (mouse_x - self.offset_x) * (self.zoom_factor - old_zoom)
                    self.offset_y -= (mouse_y - self.offset_y) * (self.zoom_factor - old_zoom)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  
                        self.dragging = True
                        self.last_mouse_pos = pygame.mouse.get_pos()
                    if event.button == 3:  
                        self.toggle_pause()

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  
                        self.dragging = False

                if event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        dx = mouse_x - self.last_mouse_pos[0]
                        dy = mouse_y - self.last_mouse_pos[1]
                        self.offset_x += dx
                        self.offset_y += dy
                        self.last_mouse_pos = (mouse_x, mouse_y)

            self.screen.fill((0, 0, 0))
            self.draw_maze()
            pygame.display.flip()
            pygame.time.delay(100)  

        pygame.quit()
