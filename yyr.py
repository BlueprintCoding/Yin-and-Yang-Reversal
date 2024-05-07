import pygame
import sys
import levelgen
from collections import deque

# Initialize Pygame
pygame.init()

# Game variables
black = (0, 0, 0)
white = (255, 255, 255)
grey = (200, 200, 200)
red = (255, 0, 0)
ui_bar_height = 40  # Height of the UI bar at the top
width, height = 800, 600 + ui_bar_height
tile_size = 50
fps = 60
max_history_length = 60
initial_lives = 2
character_size = (23, 35)
invincibility_duration = 2

# Display
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Yin and Yang Reversal")
clock = pygame.time.Clock()

# Load images and scale them to the new size
character_a_img = pygame.image.load("img/yin.png").convert_alpha()
character_a_img = pygame.transform.scale(character_a_img, character_size)
character_b_img = pygame.image.load("img/yang.png").convert_alpha()
character_b_img = pygame.transform.scale(character_b_img, character_size)
block_img = pygame.image.load("img/spike-wall.png").convert_alpha()
background_tile_img = pygame.image.load("img/background-tile.png").convert()
background_tile_img = pygame.transform.scale(background_tile_img, (tile_size, tile_size))
exit_img = pygame.image.load("img/exit.png").convert_alpha()
exit_yin_img = pygame.image.load("img/exit-yin.png").convert_alpha()
exit_yang_img = pygame.image.load("img/exit-yang.png").convert_alpha()
exit_complete_img = pygame.image.load("img/exit-complete.png").convert_alpha()
exit_img = pygame.transform.scale(exit_img, (tile_size, tile_size))
exit_yin_img = pygame.transform.scale(exit_yin_img, (tile_size, tile_size))
exit_yang_img = pygame.transform.scale(exit_yang_img, (tile_size, tile_size))
exit_complete_img = pygame.transform.scale(exit_complete_img, (tile_size, tile_size))
menu_background = pygame.image.load("img/background.png").convert()  # Load the menu background image
ui_bar_img = pygame.image.load("img/ui-bar.png").convert()  # Ensure it's the right path

font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)
lives_font = pygame.font.Font(None, 24)

def show_text(screen, text, size, color, center):
    font = pygame.font.Font(None, size)
    lives_font = pygame.font.Font(None, 24)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    screen.blit(text_surface, text_rect)

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = exit_img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update_image(self, new_image):
        self.image = new_image


class Character(pygame.sprite.Sprite):
    def __init__(self, image, x, y, direction, rewindable=False):
        super().__init__()
        self.image = image
        # Set the character dimensions
        character_width = 26
        character_height = 35
        self.image = pygame.transform.scale(self.image, (character_width, character_height))
        self.rect = self.image.get_rect()
        # Calculate center position
        center_x = x + (tile_size - character_width) // 2
        center_y = y + (tile_size - character_height) // 2

        # Set the center position
        self.rect.x = center_x
        self.rect.y = center_y
        # Shrink the hitbox
        # self.rect.inflate_ip(-10, -10)
        self.direction = direction
        self.history = deque(maxlen=max_history_length)
        self.speed = 2
        self.alive = True
        self.rewindable = rewindable
        self.lives = initial_lives
        self.invincible = False
        self.invincibility_timer = 0
        self.flash_red = False
        self.at_exit = False
        self.record_position()

    def update(self, move_direction, vertical_direction, blocks, rewind_life=False, manual_rewind=False, boosted=False):
        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        # If character is at exit, do not allow further movement
        if self.at_exit:
            return

        self.speed = 5 if boosted else 3

        if rewind_life:
            self.rewind_position_by(5)
        elif manual_rewind:
            self.reverse_position()
        else:
            self.record_position()
            if move_direction == "left":
                self.rect.x -= self.speed * self.direction
            elif move_direction == "right":
                self.rect.x += self.speed * self.direction
            elif vertical_direction == "up":
                self.rect.y -= self.speed
            elif vertical_direction == "down":
                self.rect.y += self.speed

            if not self.invincible and pygame.sprite.spritecollide(self, blocks, False):
                self.alive = False
                if self.lives > 0:
                    self.lives -= 1
                    self.rewind_position_by(10)
                    self.invincible = True
                    self.invincibility_timer = invincibility_duration
                    self.flash_red = True

        # Prevent the character from going out of bounds
        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x + self.rect.width > width:
            self.rect.x = width - self.rect.width
        if self.rect.y < 0:
            self.rect.y = 0
        elif self.rect.y + self.rect.height > height:
            self.rect.y = height - self.rect.height

    def lock_position(self):
        self.at_exit = True
        self.kill()
        # print(f"Character at exit: {self.rect.x}, {self.rect.y}")

    def record_position(self):
        current_position = (self.rect.x, self.rect.y)
        if not self.history or self.history[-1] != current_position:
            # print(f"Recording position: {self.rect.x}, {self.rect.y}")
            self.history.append(current_position)

    def reverse_position(self):
        if self.history:
            x, y = self.history.pop()
            # print(f"Reversing position to: {x}, {y}")
            self.rect.x = x
            self.rect.y = y
            self.alive = True
        else:
            print("No position in history to reverse to")

    def rewind_position_by(self, positions):
        if len(self.history) >= positions:
            x, y = self.history[-positions]
            # print(f"Rewinding position by {positions} steps to: {x}, {y}")
            self.rect.x = x
            self.rect.y = y
            self.alive = True
        else:
            print("Not enough positions in history to rewind")


class Block(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = block_img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rect.width = 48
        self.rect.height = 48


def create_level():
    level = levelgen.generate_level()
    blocks = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    exits = pygame.sprite.Group()
    character_a = None
    character_b = None

    for row_index, row in enumerate(level):
        for col_index, col in enumerate(row):
            x = col_index * tile_size
            y = row_index * tile_size
            if col == "X":
                block = Block(x, y)
                blocks.add(block)
                all_sprites.add(block)
            elif col == "A":
                character_a = Character(character_a_img, x, y, 1, rewindable=True)
                all_sprites.add(character_a)
            elif col == "B":
                character_b = Character(character_b_img, x, y, -1, rewindable=True)
                all_sprites.add(character_b)
            elif col == "E":
                exit_sprite = Exit(x, y)
                exits.add(exit_sprite)
                all_sprites.add(exit_sprite)

    return blocks, all_sprites, exits, character_a, character_b


def draw_grid(screen, rows, cols, tile_size):
    for row in range(rows):
        for col in range(cols):
            screen.blit(background_tile_img, (col * tile_size, row * tile_size))

def draw_ui(window, lives_a, lives_b, elapsed_time):
    # Draw the UI bar at the bottom
    pygame.draw.rect(window, grey, (0, height - ui_bar_height, width, ui_bar_height))
    window.blit(ui_bar_img, (0, height - ui_bar_height))
    lives_text_a = f"Yin Lives: {lives_a + 1}"
    lives_text_b = f"Yang Lives: {lives_b + 1}"
    timer_text = f"Time: {elapsed_time:.2f} s"
    show_text(window, lives_text_a, 24, black, (70, height - ui_bar_height // 2))
    show_text(window, lives_text_b, 24, black, (width - 140, height - ui_bar_height // 2))
    show_text(window, timer_text, 24, black, (width // 2, height - ui_bar_height // 2))


def main():
    running = True
    start_time = 0
    elapsed_time = 0
    game_state = "menu"
    move_direction_a = None
    vertical_direction_a = None
    reverse_a = False
    move_direction_b = None
    vertical_direction_b = None
    reverse_b = False
    boosted = False
    flash_time = 0
    character_a = None
    character_b = None
    win_image = pygame.image.load("img/exit-complete.png").convert_alpha()  # Make sure the image is loaded
    win_image = pygame.transform.scale(win_image, (50, 50)) 
    yin_sprite = pygame.image.load("img/yin.png").convert_alpha()
    yin_sprite = pygame.transform.scale(yin_sprite, (30, 40))  # Adjust size as needed
    yang_sprite = pygame.image.load("img/yang.png").convert_alpha()
    yang_sprite = pygame.transform.scale(yang_sprite, (30, 40))  # Adjust size as needed

    yin_rect = yin_sprite.get_rect(center=(width / 4, height / 2 + 200))
    yang_rect = yang_sprite.get_rect(center=(3 * width / 4, height / 2 + 200))

    while running:
        current_time = pygame.time.get_ticks()
        if game_state == "menu":
            window.blit(menu_background, (0, 0))
            # Display the game title
            show_text(window, "Yin and Yang Reversal", 74, black, (width / 2, height / 2 - 150))
            # Display start game instructions
            show_text(window, "Press ENTER to Start", 36, black, (width / 2, height / 2 - 100))
            show_text(window, "Get Yin and Yang to the exit", 36, black, (width / 2, height / 2 - 50))
            show_text(window, "Yin moves standardly left and right, Yang is reversed. ", 36, black, (width / 2, height / 2 - 25))
            show_text(window, "Rewind time for each character to get out of tight sports", 36, black, (width / 2, height / 2 - 0))

            # Display controls
            show_text(window, "Controls", 36, black, (width / 2, height / 2 + 50))
            control_text = "Move: Arrow Keys | Boost: Shift | Rewind Time: Q (Yin), E (Yang)"
            show_text(window, control_text, 28, black, (width / 2, height / 2 + 100))
            # Display Yin and Yang sprites and labels
            window.blit(yin_sprite, yin_rect)
            show_text(window, "Yin", 36, black, (width / 4, height / 2 + 160))
            window.blit(yang_sprite, yang_rect)
            show_text(window, "Yang", 36, black, (3 * width / 4, height / 2 + 160))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    game_state = "playing"
                    start_time = pygame.time.get_ticks()
                    blocks, all_sprites, exits, character_a, character_b = create_level()
                    move_direction_a = None
                    vertical_direction_a = None
                    reverse_a = False
                    move_direction_b = None
                    vertical_direction_b = None
                    reverse_b = False
                    boosted = False
                    character_a_at_exit = False
                    character_b_at_exit = False
                    flash_time = 0
                    exit_image_to_use = exit_img

        elif game_state == "playing":
            elapsed_time = (current_time - start_time) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        move_direction_a = "left"
                        move_direction_b = "left"
                    elif event.key == pygame.K_RIGHT:
                        move_direction_a = "right"
                        move_direction_b = "right"
                    elif event.key == pygame.K_UP:
                        vertical_direction_a = "up"
                        vertical_direction_b = "up"
                    elif event.key == pygame.K_DOWN:
                        vertical_direction_a = "down"
                        vertical_direction_b = "down"
                    elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        boosted = True
                    elif event.key == pygame.K_q:
                        reverse_a = True
                    elif event.key == pygame.K_e:
                        reverse_b = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        move_direction_a = None
                        move_direction_b = None
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        vertical_direction_a = None
                        vertical_direction_b = None
                    if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        boosted = False
                    if event.key == pygame.K_q:
                        reverse_a = False
                    if event.key == pygame.K_e:
                        reverse_b = False

                        
            # Detect if both characters are at the exit
            character_a_at_exit = any(pygame.sprite.collide_rect(character_a, exit) for exit in exits)
            character_b_at_exit = any(pygame.sprite.collide_rect(character_b, exit) for exit in exits)
            if character_a_at_exit and character_b_at_exit:
                exit_image_to_use = exit_complete_img
                
                result = "complete"
            elif character_a_at_exit:
                exit_image_to_use = exit_yin_img
                result = "partial"
            elif character_b_at_exit:
                exit_image_to_use = exit_yang_img
                result = "partial"
            else:
                exit_image_to_use = exit_img

            # Update the image for all exit sprites
            for exit_sprite in exits:
                exit_sprite.update_image(exit_image_to_use)      

                        # Lock character into position if they are at the exit
            if character_a_at_exit:
                character_a.lock_position()
            if character_b_at_exit:
                character_b.lock_position()          


            # Update character A
            character_a.update(move_direction_a, vertical_direction_a, blocks, rewind_life=False, manual_rewind=reverse_a, boosted=boosted)

            # Update character B
            character_b.update(move_direction_b, vertical_direction_b, blocks, rewind_life=False, manual_rewind=reverse_b, boosted=boosted)
            # all_sprites.update()

            # Determine game over conditions
            if (not character_a.alive and character_a.lives == 0) or (not character_b.alive and character_b.lives == 0):
                game_state = "game_over"
                result = "Game Over"
            elif character_a_at_exit and character_b_at_exit:
                game_state = "win"
                final_time = elapsed_time
                result = "You Win!"

            window.fill(white)
            draw_grid(window, height // tile_size, width // tile_size, tile_size)
            all_sprites.draw(window)
            draw_ui(window, character_a.lives, character_b.lives, elapsed_time)

            # Apply red flash if needed
            if character_a.flash_red or character_b.flash_red:
                window.fill(red, special_flags=pygame.BLEND_RGBA_MULT)
                flash_time += 1
                if flash_time > 5:
                    character_a.flash_red = False
                    character_b.flash_red = False
                    flash_time = 0

            pygame.display.flip()  # Update the full display Surface to the screen
            clock.tick(fps)
            

        elif game_state == "win":
            window.blit(menu_background, (0, 0))  # Blit the background image
            win_image_rect = win_image.get_rect(center=(width // 2, height // 2 - 100))
            window.blit(win_image, win_image_rect)
            show_text(window, "You Win!", 74, black, (width / 2, height / 2 - 50))
            show_text(window, f"Time taken: {final_time:.2f} seconds", 36, black, (width / 2, height / 2 + 5))
            show_text(window, "Press ENTER to Restart", 36, black, (width / 2, height / 2 + 35))
            
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    game_state = "menu"

        elif game_state == "game_over":
            window.blit(menu_background, (0, 0))  # Blit the background image
            show_text(window, "Game Over", 74, black, (width / 2, height / 2 - 50))
            show_text(window, "Press ENTER to Restart", 36, black, (width / 2, height / 2 + 50))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    game_state = "menu"


if __name__ == "__main__":
    main()
