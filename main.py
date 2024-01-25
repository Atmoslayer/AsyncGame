import asyncio
import argparse
import curses
import os
import random
import time

from itertools import cycle

from frames_control_functions import read_controls, draw_frame, get_frame_size, check_frame, update_speed
from obstacles import Obstacle, show_obstacles

TIC_TIMEOUT = 0.1


async def sleep(tics=1):
    for tick in range(tics):
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):

    global obstacles
    global obstacles_in_last_collisions

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
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                return
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_rocket(canvas, rocket_row, rocket_column, rocket_frames, max_row, max_column):
    global coroutines
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

        if space_pressed:
            coroutines.append(fire(canvas, rocket_row, rocket_column + 2))

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
    global obstacles
    global coroutines
    global obstacles_in_last_collisions
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        frame_row_size, frame_column_size = get_frame_size(garbage_frame)
        obstacle = Obstacle(row, column, frame_row_size, frame_column_size, row)
        obstacles.append(obstacle)
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.remove(obstacle)
            return
        obstacles.remove(obstacle)
        row += speed


async def fill_orbit_with_garbage(canvas, max_column, garbage_quantity):

    garbage_frames = [
        open(os.path.join(f'{os.getcwd()}/templates/garbage', garbage_file), "r").read() for garbage_file
        in os.listdir(f'{os.getcwd()}/templates/garbage')
    ]

    while True:
        garbage_column = random.randint(1, max_column - 10)
        garbage_frame = random.choice(garbage_frames)
        garbage_timeout = random.randint(1, garbage_quantity)
        coroutines.append(fly_garbage(canvas, column=garbage_column, garbage_frame=garbage_frame))
        await sleep(garbage_timeout)


def stars_generator(canvas, max_row, max_column):
    stars_symbols = ['*', ':', '.', '+']
    for star in range(stars_quantity):
        star_min_row = 1
        star_max_row = max_row - 2
        star_min_column = 1
        star_max_column = max_column - 2
        star_row = random.randint(star_min_row, star_max_row)
        star_column = random.randint(star_min_column, star_max_column)
        star_symbol = random.choice(stars_symbols)
        star_timeout = random.randint(1, 50)
        yield blink(canvas, star_row, star_column, star_timeout, star_symbol)


def draw(canvas):
    with open("templates/rocket/rocket_frame_1.txt", "r") as frame:
        rocket_frame_1 = frame.read()
    with open("templates/rocket/rocket_frame_2.txt", "r") as frame:
        rocket_frame_2 = frame.read()

    rocket_frames = [rocket_frame_1, rocket_frame_1, rocket_frame_2, rocket_frame_2]
    canvas.nodelay(True)
    curses.curs_set(False)
    screen = curses.initscr()
    max_row, max_column = screen.getmaxyx()

    rocket_row = max_row / 2
    rocket_column = max_column / 2

    global obstacles
    global obstacles_in_last_collisions

    obstacles_in_last_collisions = []
    obstacles = []

    global coroutines

    coroutines = [
        star for star in stars_generator(canvas, max_row, max_column)
    ]

    coroutines.append(animate_rocket(canvas, rocket_row, rocket_column, rocket_frames, max_row, max_column))
    coroutines.append(fill_orbit_with_garbage(canvas, max_column, garbage_quantity))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)

            canvas.refresh()
            canvas.border()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Space game parser')
    parser.add_argument('--stars', help='Enter stars quantity', type=int, default=100)
    parser.add_argument('--garbage', help='Enter garbage quantity', type=int, default=50)
    arguments = parser.parse_args()
    stars_quantity = arguments.stars
    garbage_quantity = arguments.garbage
    curses.update_lines_cols()
    curses.wrapper(draw)