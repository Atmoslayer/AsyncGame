import asyncio
import curses
from itertools import cycle

from frames_control_functions import read_controls, draw_frame, get_frame_size, check_frame, update_speed


async def sleep(tics=1):
    for tick in range(tics):
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
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


async def animate_rocket(canvas, rocket_row, rocket_column, rocket_frames, max_row, max_column):
    rocket_row_size, rocket_column_size = get_frame_size(rocket_frames[0])
    row_speed = column_speed = 0
    for rocket_frame in cycle(rocket_frames):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)

        rocket_row += row_speed
        rocket_column += column_speed

        rocket_row = check_frame(rocket_row, rows_direction, max_row, rocket_row_size)
        rocket_column = check_frame(rocket_column, columns_direction, max_column, rocket_column_size)

        draw_frame(canvas, rocket_row, rocket_column, rocket_frame)

        await sleep(1)

        draw_frame(canvas, rocket_row, rocket_column, rocket_frame, negative=True)


async def blink(canvas, row, column, timeout, symbol='*'):

    while True:

        await sleep(timeout)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
