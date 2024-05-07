import pygame
import sys
from collections import deque

# Initialize Pygame
pygame.init()

# Game variables
width, height = 800, 600
black = (0, 0, 0)
white = (255, 255, 255)
grey = (200, 200, 200)
red = (255, 0, 0)
fps = 60
tile_size = 50
max_history_length = 30
initial_lives = 2
character_size = (40, 40)
invincibility_duration = 2 # Frames of invincibility after position reset

# Display
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Time-Reversal Puzzle Platformer")

clock = pygame.time.Clock()

# Load images and scale them to the new size
character_a_img = pygame.image.load("character_a.png").convert_alpha()
character_a_img = pygame.transform.scale(character_a_img, character_size)
character_b_img = pygame.image.load("character_b.png").convert_alpha()
character_b_img = pygame.transform.scale(character_b_img, character_size)
block_img = pygame.image.load("spike-wall.png").convert_alpha()
background_tile_img = pygame.image.load("background-tile.png").convert()
background_tile_img = pygame.transform.scale(background_tile_img, (tile_size, tile_size))
exit_img = pygame.image.load("exit.png").convert_alpha()
exit_img = pygame.transform.scale(exit_img, (tile_size, tile_size))


class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = exit_img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


# Level design
level = [
    "XXXXXXXXXXXXXXXX",
    "X---X--E------XX",
    "X---X-----XXXXX",
    "XX----XXX------X",
    "XXX---XXX----XXX",
    "X---XXXXXXX-----",
    "X-----X------XXX",
    "X----XX---X-XXXX",
    "X----XXXXXX----X",
    "X--XX--X--XX----",
    "X--XX--X--XX---X",
    "XX-----X------XX",
    "---A---X-B------"
]

# Fonts
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)
lives_font = pygame.font.Font(None, 24)

#Character Class
class Character(pygame.sprite.Sprite):
    def __init__(self, image, x, y, direction, rewindable=False):
        super().__init__()
        self.image = image
        # Set the character dimensions
        character_width = 23
        character_height = 45
        self.image = pygame.transform.scale(self.image, (character_width, character_height))
        
        # Set the bounding box size
        self.rect = self.image.get_rect()
        self.rect.x = x + (tile_size - character_width) // 2
        self.rect.y = y + (tile_size - character_height) // 2
        self.direction = direction
        self.history = deque(maxlen=max_history_length)
        self.default_speed = 3
        self.boosted_speed = 5
        self.speed = self.default_speed
        self.alive = True
        self.rewindable = rewindable
        self.lives = initial_lives
        self.invincible = False
        self.invincibility_timer = 0
        self.flash_red = False
        self.record_position()

    def update(self, move_direction, vertical_direction, blocks, rewind_life=False, manual_rewind=False, boosted=False):
        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        self.speed = self.boosted_speed if boosted else self.default_speed

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
                    self.rewind_position_by(5)
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

    def record_position(self):
        current_position = (self.rect.x, self.rect.y)
        if not self.history or self.history[-1] != current_position:
            print(f"Recording position: {self.rect.x}, {self.rect.y}")
            self.history.append(current_position)

    def reverse_position(self):
        if self.history:
            x, y = self.history.pop()
            print(f"Reversing position to: {x}, {y}")
            self.rect.x = x
            self.rect.y = y
            self.alive = True
        else:
            print("No position in history to reverse to")

    def rewind_position_by(self, positions):
        if len(self.history) >= positions:
            x, y = self.history[-positions]
            print(f"Rewinding position by {positions} steps to: {x}, {y}")
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

        # Adjust the size of the rect to 45x45 pixels
        self.rect.width = 48
        self.rect.height = 48



def create_level():
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


def show_text(screen, text, size, color, center):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    screen.blit(text_surface, text_rect)


def main():
    running = True
    game_state = "menu"
    move_direction_a = None
    vertical_direction_a = None
    reverse_a = False
    move_direction_b = None
    vertical_direction_b = None
    reverse_b = False
    flash_time = 0
    boosted = False

    character_a = None
    character_b = None
    result = ""

    while running:
        if game_state == "menu":
            window.fill(white)
            show_text(window, "Time-Reversal Puzzle Platformer", 74, black, (width / 2, height / 2 - 50))
            show_text(window, "Press ENTER to Start", 36, black, (width / 2, height / 2 + 50))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    game_state = "playing"
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

        elif game_state == "playing":
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

            # Update character A
            character_a.update(move_direction_a, vertical_direction_a, blocks, rewind_life=False, manual_rewind=reverse_a, boosted=boosted)

            # Update character B
            character_b.update(move_direction_b, vertical_direction_b, blocks, rewind_life=False, manual_rewind=reverse_b, boosted=boosted)

            # Check if either character is at an exit
            character_a_at_exit = pygame.sprite.spritecollideany(character_a, exits)
            character_b_at_exit = pygame.sprite.spritecollideany(character_b, exits)

            # Determine game over conditions
            if (not character_a.alive and character_a.lives == 0) or (not character_b.alive and character_b.lives == 0):
                game_state = "game_over"
                result = "Game Over"
            elif character_a_at_exit and character_b_at_exit:
                game_state = "game_over"
                result = "You Win!"

            # Flash the screen red if needed
            if character_a.flash_red or character_b.flash_red:
                window.fill(red)
                flash_time += 1
                if flash_time > 5:
                    character_a.flash_red = False
                    character_b.flash_red = False
                    flash_time = 0
            else:
                draw_grid(window, rows=height // tile_size, cols=width // tile_size, tile_size=tile_size)

            # Draw all the sprites on top of the grid
            all_sprites.draw(window)

            # Display lives for both characters
            a_lives_text = lives_font.render(f"Lives: {character_a.lives + 1}", True, black)
            window.blit(a_lives_text, (10, 10))

            b_lives_text = lives_font.render(f"Lives: {character_b.lives + 1}", True, black)
            window.blit(b_lives_text, (width - b_lives_text.get_width() - 10, 10))

            pygame.display.flip()
            clock.tick(fps)

        elif game_state == "game_over":
            window.fill(white)
            show_text(window, result, 74, black, (width / 2, height / 2 - 50))
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
