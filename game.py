import pygame
import os
import json
from tkinter import Tk, filedialog

pygame.init()

# Game window
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 640
LOWER_MARGIN = 100
SIDE_MARGIN = 300

screen = pygame.display.set_mode((SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN))
pygame.display.set_caption('Level Editor')

# Define game variables
ROWS = 16
MAX_COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
GRID_HEIGHT = ROWS * TILE_SIZE
TILE_TYPES = 5
level = 0
current_tile = -1  # No tile selected by default
scroll_left = False
scroll_right = False
scroll = 0
scroll_speed = 5
is_dragging = False
mouse_start_pos = None
mouse_end_pos = None
highlighted_tile = None
highlighted_tile_pos = None

# Create a button to close the app
close_button = pygame.Rect(SCREEN_WIDTH + SIDE_MARGIN - 50, SCREEN_HEIGHT + LOWER_MARGIN - 50, 40, 40)

# Initialize the tile map
def initialize_ground():
    for col in range(MAX_COLS):
        tile_map[ROWS - 2][col] = 1

tile_map = [[-1 for _ in range(MAX_COLS)] for _ in range(ROWS)]  # Map grid
initialize_ground()

# Player variables
player_size = 20
player_x = SCREEN_WIDTH // 2
player_y = SCREEN_HEIGHT // 2
player_speed = 5

# Load images
plx_1_img = pygame.image.load('./Background/plx_1.png').convert_alpha()
plx_2_img = pygame.image.load('./Background/plx_2.png').convert_alpha()
plx_3_img = pygame.image.load('./Background/plx_3.png').convert_alpha()
plx_4_img = pygame.image.load('./Background/plx_4.png').convert_alpha()
plx_5_img = pygame.image.load('./Background/plx_5.png').convert_alpha()

# Store tiles in list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'./Tiles/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

# Load character image
character_idle_img = pygame.image.load('./Animations/idle.gif').convert_alpha()
character_idle_img = pygame.transform.scale(character_idle_img, (TILE_SIZE, TILE_SIZE))
character_idle_img_flipped = pygame.transform.flip(character_idle_img, True, False)

# Define colors
GREEN = (144, 201, 120)
WHITE = (255, 255, 255)
RED = (200, 25, 25)
BLACK = (0, 0, 0)
BLUE = (0, 120, 215)
ORANGE = (255, 165, 0)

# Scale images to fit the grid area
plx_1_img = pygame.transform.scale(plx_1_img, (int(plx_1_img.get_width() * 3), GRID_HEIGHT))
plx_2_img = pygame.transform.scale(plx_2_img, (int(plx_2_img.get_width() * 3), GRID_HEIGHT))
plx_3_img = pygame.transform.scale(plx_3_img, (int(plx_3_img.get_width() * 3), GRID_HEIGHT))
plx_4_img = pygame.transform.scale(plx_4_img, (int(plx_4_img.get_width() * 3), GRID_HEIGHT))
plx_5_img = pygame.transform.scale(plx_5_img, (int(plx_5_img.get_width() * 3), GRID_HEIGHT))

# Button class
class Button:
    def __init__(self, x, y, width, height, text, callback=None, image=None, color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = color if color else WHITE
        self.is_selected = False
        self.image = image

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 3)
        if self.image:
            screen.blit(self.image, self.rect.topleft)
        else:
            font = pygame.font.Font(None, 24)
            text_surf = font.render(self.text, True, BLACK)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Save map to a file
def save_map():
    Tk().withdraw()  # Hide the Tkinter root window
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, "w") as file:
            json.dump({"map": tile_map}, file)

# Load map from a file
def load_map():
    Tk().withdraw()  # Hide the Tkinter root window
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, "r") as file:
            data = json.load(file)
            global tile_map
            tile_map = data.get("map", tile_map)

# Reset the map to its initial state
def reset_map():
    global tile_map, character_spawned
    tile_map = [[-1 for _ in range(MAX_COLS)] for _ in range(ROWS)]
    initialize_ground()
    character_spawned = False

# Create save, load, eraser, and reset buttons
side_buttons = [
    Button(SCREEN_WIDTH + 50, SCREEN_HEIGHT - 200, 100, 40, "Reset", reset_map, color=GREEN),
    Button(SCREEN_WIDTH + 50, SCREEN_HEIGHT - 150, 100, 40, "Eraser", None, color=RED),
    Button(SCREEN_WIDTH + 50, SCREEN_HEIGHT - 100, 100, 40, "Save", save_map, color=BLUE),
    Button(SCREEN_WIDTH + 50, SCREEN_HEIGHT - 50, 100, 40, "Load", load_map, color=ORANGE)
]

# Create right-side tile buttons
tile_buttons = []
for i, img in enumerate(img_list):
    button = Button(SCREEN_WIDTH + 50, 50 + i * (TILE_SIZE + 10), TILE_SIZE, TILE_SIZE, "", None, image=img)
    tile_buttons.append(button)

# Add character button to the side panel
character_button = Button(SCREEN_WIDTH + 50, 50 + len(tile_buttons) * (TILE_SIZE + 10), TILE_SIZE, TILE_SIZE, "", None, image=character_idle_img)
tile_buttons.append(character_button)

# Character variables
character_spawned = False
character_x, character_y = None, None
character_width, character_height = TILE_SIZE, TILE_SIZE
character_vel_x, character_vel_y = 0, 0
character_jump_strength = -15
character_gravity = 1
character_is_jumping = False
character_facing_left = False

# Helper function to check for collision with the map
def check_collision(x, y):
    grid_x = x // TILE_SIZE
    grid_y = y // TILE_SIZE
    if 0 <= grid_x < MAX_COLS and 0 <= grid_y < ROWS:
        tile_value = tile_map[grid_y][grid_x]
        if tile_value == 2:  # Allow walking through tile type 2 (bush)
            return False
        return tile_value != -1
    return False

# Adjusted collision for movement
def handle_horizontal_collision(x, y, vel_x):
    new_x = x + vel_x
    if vel_x > 0:  # Moving right
        if new_x + character_width + scroll > MAX_COLS * TILE_SIZE or check_collision(new_x + character_width + scroll, y) or check_collision(new_x + character_width + scroll, y + character_height - 1):
            return x
    elif vel_x < 0:  # Moving left
        if new_x + scroll < 0 or check_collision(new_x + scroll, y) or check_collision(new_x + scroll, y + character_height - 1):
            return x
    return new_x

def handle_vertical_collision(x, y, vel_y):
    new_y = y + vel_y
    if vel_y > 0:  # Moving down
        if check_collision(x + scroll, new_y + character_height) or check_collision(x + character_width - 1 + scroll, new_y + character_height):
            return y, True
    elif vel_y < 0:  # Moving up
        if check_collision(x + scroll, new_y) or check_collision(x + character_width - 1 + scroll, new_y):
            return y, False
    return new_y, False

# Draw functions
def draw_bg():
    screen.fill(GREEN)
    layers = [plx_1_img, plx_2_img, plx_3_img, plx_4_img, plx_5_img]
    for layer in layers:
        width = layer.get_width()
        x_offset = scroll % width
        for x in range(-width, SCREEN_WIDTH + SIDE_MARGIN + width, width):
            screen.blit(layer, (x - x_offset, 0))

def draw_grid():
    for c in range(MAX_COLS + 1):
        pygame.draw.line(screen, WHITE, (c * TILE_SIZE - scroll, 0), (c * TILE_SIZE - scroll, GRID_HEIGHT))
    for c in range(ROWS + 1):
        pygame.draw.line(screen, WHITE, (0, c * TILE_SIZE), (SCREEN_WIDTH, c * TILE_SIZE))

def draw_map():
    for row in range(ROWS):
        for col in range(MAX_COLS):
            if tile_map[row][col] != -1:
                screen.blit(img_list[tile_map[row][col]], (col * TILE_SIZE - scroll, row * TILE_SIZE))

def draw_side_panel():
    pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH, 0, SIDE_MARGIN, SCREEN_HEIGHT))
    for button in tile_buttons + side_buttons:
        button.draw()

def draw_character():
    if character_spawned:
        if character_facing_left:
            screen.blit(character_idle_img_flipped, (character_x, character_y))
        else:
            screen.blit(character_idle_img, (character_x, character_y))

def draw_close_button():
    pygame.draw.rect(screen, BLACK, close_button)
    pygame.draw.rect(screen, WHITE, close_button, 2)
    font = pygame.font.Font(None, 24)
    text_surf = font.render("X", True, WHITE)
    text_rect = text_surf.get_rect(center=close_button.center)
    screen.blit(text_surf, text_rect)

def draw_welcome_text():
    font = pygame.font.Font(None, 36)
    text = font.render("Level Editor v1.2!", True, BLACK)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT + LOWER_MARGIN // 2))
    screen.blit(text, text_rect)

def draw_highlighted_tile():
    if highlighted_tile_pos:
        grid_x, grid_y = highlighted_tile_pos
        pygame.draw.rect(screen, RED, (grid_x * TILE_SIZE - scroll, grid_y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 3)

# Game loop
run = True
is_dragging = False  # Initialize dragging state
drag_start_x = 0  # Track the starting x position for dragging

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # Check if the close button was clicked
            if close_button.collidepoint(mouse_pos):
                run = False

            # Start dragging for horizontal scrolling
            if event.button == 1:  # Left mouse button
                is_dragging = True
                drag_start_x = event.pos[0]

            for button in side_buttons:
                if button.is_clicked(mouse_pos):
                    for b in side_buttons:
                        b.is_selected = False
                    button.is_selected = True
                    if button.text == "Eraser":
                        current_tile = -1
                    elif button.text in ["Save", "Load", "Reset"]:
                        if button.callback:
                            button.callback()
            for i, button in enumerate(tile_buttons):
                if button.is_clicked(mouse_pos):
                    for b in side_buttons:
                        b.is_selected = False
                    for b in tile_buttons:
                        b.is_selected = False
                    button.is_selected = True
                    current_tile = i
            if mouse_pos[0] < SCREEN_WIDTH:  # Check if clicked on the map
                grid_x, grid_y = (mouse_pos[0] + scroll) // TILE_SIZE, mouse_pos[1] // TILE_SIZE
                if 0 <= grid_y < ROWS and 0 <= grid_x < MAX_COLS:
                    highlighted_tile_pos = (grid_x, grid_y)
                    if current_tile == len(tile_buttons) - 1:  # Character button selected
                        character_x, character_y = grid_x * TILE_SIZE - scroll, grid_y * TILE_SIZE
                        character_spawned = True
                        character_vel_x, character_vel_y = 0, 0
                    elif current_tile == -1:  # Eraser functionality
                        tile_map[grid_y][grid_x] = -1
                        highlighted_tile_pos = None
                    elif current_tile != -1:
                        tile_map[grid_y][grid_x] = current_tile

        if event.type == pygame.MOUSEBUTTONUP:
            highlighted_tile_pos = None
            if event.button == 1:  # Left mouse button
                is_dragging = False

        if event.type == pygame.MOUSEMOTION:
            if is_dragging:
                dx = event.pos[0] - drag_start_x
                scroll -= dx
                drag_start_x = event.pos[0]
                # Constrain scrolling to the map bounds
                scroll = max(0, min(scroll, (MAX_COLS * TILE_SIZE) - SCREEN_WIDTH))

        if event.type == pygame.KEYDOWN:
            if character_spawned:
                if event.key == pygame.K_w and not character_is_jumping:
                    character_vel_y = character_jump_strength
                    character_is_jumping = True
                if event.key == pygame.K_a:
                    scroll_left = True
                    character_vel_x = -player_speed
                    character_facing_left = True
                if event.key == pygame.K_d:
                    scroll_right = True
                    character_vel_x = player_speed
                    character_facing_left = False

        if event.type == pygame.KEYUP:
            if character_spawned:
                if event.key == pygame.K_a:
                    scroll_left = False
                    character_vel_x = 0
                if event.key == pygame.K_d:
                    scroll_right = False
                    character_vel_x = 0

    # Scrolling logic
    if character_spawned and character_x is not None:
        if character_x <= 100 and scroll > 0 and character_vel_x < 0:
            scroll -= scroll_speed
            character_x = 100
        elif character_x >= SCREEN_WIDTH - 100 and scroll < (MAX_COLS * TILE_SIZE) - SCREEN_WIDTH and character_vel_x > 0:
            scroll += scroll_speed
            character_x = SCREEN_WIDTH - 100

    # Character physics
    if character_spawned:
        # Horizontal movement with collision
        character_x = handle_horizontal_collision(character_x, character_y, character_vel_x)

        # Vertical movement with collision
        character_y, is_collision = handle_vertical_collision(character_x, character_y, character_vel_y)
        if is_collision:
            character_vel_y = 0
            character_is_jumping = False
        else:
            character_vel_y += character_gravity

        # Despawn logic if the character touches the bottom row
        if character_y + character_height >= SCREEN_HEIGHT:
            if character_y // TILE_SIZE == ROWS - 1:  # Check if on the last grid row
                character_spawned = False

    # Draw everything
    draw_bg()
    draw_grid()
    draw_map()
    draw_side_panel()
    draw_character()
    draw_welcome_text()
    draw_highlighted_tile()
    draw_close_button()


    pygame.display.update()

pygame.quit()
