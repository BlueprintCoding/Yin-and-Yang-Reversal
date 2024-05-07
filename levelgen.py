import random
import time

wall = 'X'
path = '-'
exit_marker = 'E'
character_a_marker = 'A'
character_b_marker = 'B'
tile_size = 50
grid_cols = 16
grid_rows = 12


def create_prim_maze():
    random.seed(time.time())
    maze = [[wall for _ in range(grid_cols)] for _ in range(grid_rows)]
    walls = []
    start_row = random.randint(1, grid_rows - 2)
    start_col = random.randint(1, grid_cols - 2)
    maze[start_row][start_col] = path
    walls.extend([(start_row - 1, start_col), (start_row + 1, start_col),
                  (start_row, start_col - 1), (start_row, start_col + 1)])

    while walls:
        rand_wall = walls.pop(random.randint(0, len(walls) - 1))
        row, col = rand_wall

        if maze[row][col] == wall:
            surrounding_cells = sum(
                1 for r, c in [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
                if 0 <= r < grid_rows and 0 <= c < grid_cols and maze[r][c] == path)

            if surrounding_cells < 2:
                maze[row][col] = path
                new_walls = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
                for wall_pos in new_walls:
                    r, c = wall_pos
                    if 0 <= r < grid_rows and 0 <= c < grid_cols and maze[r][c] == wall:
                        walls.append(wall_pos)

    # Set entrance and exit
    maze[grid_rows - 1][1] = character_a_marker
    maze[grid_rows - 1][grid_cols - 2] = character_b_marker

    exit_row = random.randint(0, 2)
    exit_col = random.randint(2, grid_cols - 3)
    maze[exit_row][exit_col] = exit_marker

    return maze


def generate_level():
    maze = create_prim_maze()
    level = ["".join(row) for row in maze]
    return level


if __name__ == "__main__":
    generated_level = generate_level()
    for row in generated_level:
        print(row)
