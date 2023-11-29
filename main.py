import asyncio
import curses
import random
import time
from itertools import cycle


TIC_TIMEOUT = 0.1
SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""
    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1
            break

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1
            break

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1
            break

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1
            break

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True
            break

    return rows_direction, columns_direction, space_pressed


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def animate_rocket(canvas, rocket_row, rocket_column, rocket_frames):
    for rocket_frame in cycle(rocket_frames):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        rocket_row = rocket_row + rows_direction
        rocket_column = rocket_column + columns_direction
        draw_frame(canvas, rocket_row, rocket_column, rocket_frame)
        canvas.refresh()

        for step in range(5):
            await asyncio.sleep(0)

        draw_frame(canvas, rocket_row, rocket_column, rocket_frame, negative=True)


async def blink(canvas, row, column, symbol='*'):

    while True:

        random_integer = random.randint(1, 50)

        for step in range(random_integer):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)

        for step in range(10):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        for step in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        for step in range(9):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        for step in range(3):
            await asyncio.sleep(0)


def draw(canvas):
    with open("templates/rocket_frame_1.txt", "r") as frame:
        rocket_frame_1 = frame.read()
    with open("templates/rocket_frame_2.txt", "r") as frame:
        rocket_frame_2 = frame.read()
    rocket_frames = [rocket_frame_1, rocket_frame_2]
    canvas.nodelay(True)
    curses.curs_set(False)
    canvas.border()
    screen = curses.initscr()
    max_row, max_column = screen.getmaxyx()
    stars_symbols = ['*', ':', '.', '+']
    coroutines = []

    rocket_row = max_row / 2
    rocket_column = max_column / 2

    for stars_quantity in range(100):
        star_row = random.randint(1, max_row-2)
        star_column = random.randint(1, max_column-2)
        star_symbol = random.choice(stars_symbols)
        coroutines.append(blink(canvas, star_row, star_column, star_symbol))

    coroutines.append(fire(canvas, rocket_row, rocket_column + 2))
    coroutines.append(animate_rocket(canvas, rocket_row, rocket_column, rocket_frames))

    while True:
        index = 0

        while index < len(coroutines):
            coroutine = coroutines[index]
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
            index += 1

        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
