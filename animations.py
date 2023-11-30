import asyncio
import curses
import random
from itertools import cycle

from frames_control_functions import read_controls, draw_frame


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

        for step in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        for step in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        for step in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        for step in range(3):
            await asyncio.sleep(0)