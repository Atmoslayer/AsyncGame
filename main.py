import asyncio
import argparse
import curses
import os
import random
import time

from itertools import cycle

from frames_control_functions import read_controls, draw_frame, get_frame_size, check_frame, update_speed
from obstacles import Obstacle

TIC_TIMEOUT = 0.1
PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}


async def sleep(tics=1):
    for tick in range(tics):
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):

    global obstacles, obstacles_in_last_collisions

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
    global coroutines, obstacles_in_last_collisions, year
    coroutines.append(show_year(canvas, max_column))

    game_over = False
    rocket_row_size, rocket_column_size = get_frame_size(rocket_frames[0])
    row_speed = column_speed = 0
    for rocket_frame in cycle(rocket_frames):
        if game_over:
            coroutines.append(show_gameover(canvas, max_row, max_column))
            return
        else:
            rows_direction, columns_direction, space_pressed = read_controls(canvas)
            row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)

            rocket_row += row_speed
            rocket_column += column_speed

            rocket_row = check_frame(rocket_row, rows_direction, max_row, rocket_row_size)
            rocket_column = check_frame(rocket_column, columns_direction, max_column, rocket_column_size)

            draw_frame(canvas, rocket_row, rocket_column, rocket_frame)

            if space_pressed and year > 2020:
                coroutines.append(fire(canvas, rocket_row, rocket_column + 2))

            await sleep(1)

            draw_frame(canvas, rocket_row, rocket_column, rocket_frame, negative=True)
            for obstacle in obstacles:
                if obstacle.has_collision(rocket_row, rocket_column):
                    obstacles_in_last_collisions.append(obstacle)
                    game_over = True


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
    global obstacles, coroutines, obstacles_in_last_collisions
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
            obstacles.remove(obstacle)
            return
        obstacles.remove(obstacle)
        row += speed


async def fill_orbit_with_garbage(canvas, max_column):
    garbage_frames = [
        open(os.path.join(f'{os.getcwd()}/templates/garbage', garbage_file), "r").read() for garbage_file
        in os.listdir(f'{os.getcwd()}/templates/garbage')
    ]

    while True:
        garbage_column = random.randint(1, max_column - 10)
        garbage_frame = random.choice(garbage_frames)
        garbage_timeout = get_garbage_delay_tics()
        if garbage_timeout:
            coroutines.append(fly_garbage(canvas, column=garbage_column, garbage_frame=garbage_frame))
            await sleep(garbage_timeout)
        else:
            await sleep(1)


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


async def show_gameover(canvas, max_row, max_column):
    while True:
        with open("templates/game_over.txt", "r") as frame:
            frame = frame.read()
            frame_row_size, frame_column_size = get_frame_size(frame)
            draw_frame(canvas, max_row / 2 - frame_row_size / 2, max_column / 2 - frame_column_size / 2, frame)
            await asyncio.sleep(0)


async def show_year(canvas, max_column):
    global year
    year_event = ''
    event_window = canvas.derwin(1, 1, 1, 1)
    while True:
        if PHRASES.get(year):
            year_event = f'{year} - {PHRASES.get(year)}'
            event_window.clear()
        event_window = canvas.derwin(2, len(year_event) + 5, 1, round(max_column / 2 - len(year_event) / 2))
        event_window.addstr(1, 1, year_event)
        window = canvas.derwin(3, 10, 1, max_column - 12)
        window.border()
        window.addstr(1, 3, str(year))
        await asyncio.sleep(0)


async def update_year():
    global year
    while True:
        year += 1
        await sleep(15)


def get_garbage_delay_tics():
    global year
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2


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

    global coroutines, obstacles, obstacles_in_last_collisions, year

    year = 1957

    obstacles_in_last_collisions = []
    obstacles = []

    coroutines = [
        star for star in stars_generator(canvas, max_row, max_column)
    ]

    coroutines.append(animate_rocket(canvas, rocket_row, rocket_column, rocket_frames, max_row, max_column))
    coroutines.append(fill_orbit_with_garbage(canvas, max_column))
    coroutines.append(update_year())

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
    arguments = parser.parse_args()
    stars_quantity = arguments.stars
    curses.update_lines_cols()
    curses.wrapper(draw)
