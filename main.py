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
    1957: 'First Sputnik',
    1961: 'Gagarin flew!',
    1969: 'Armstrong got on the moon!',
    1971: 'First orbital space station Salute-1',
    1981: 'Flight of the Shuttle Columbia',
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: 'Take the plasma gun! Shoot the garbage!',
}


async def sleep(tics=1):
    """Execute delays for animations. Delay duration can be transmitted."""
    for tick in range(tics):
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

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


async def animate_rocket(canvas, rocket_row, rocket_column, max_row, max_column, gun_from_start):
    """Display animation of rocket, read and uses controls. Rocket frames specified on start."""
    global coroutines, obstacles_in_last_collisions, year
    coroutines.append(show_year(canvas, max_column))

    with open("templates/rocket/rocket_frame_1.txt", "r") as frame:
        rocket_frame_1 = frame.read()
    with open("templates/rocket/rocket_frame_2.txt", "r") as frame:
        rocket_frame_2 = frame.read()

    rocket_frames = [rocket_frame_1, rocket_frame_1, rocket_frame_2, rocket_frame_2]

    rocket_row_size, rocket_column_size = get_frame_size(rocket_frames[0])
    rocket_row = round(rocket_row - rocket_row_size / 2)
    rocket_column = round(rocket_column - rocket_column_size / 2)

    row_speed = column_speed = 0
    for rocket_frame in cycle(rocket_frames):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)

        rocket_row = check_frame(rocket_row, row_speed, max_row, rocket_row_size)
        rocket_column = check_frame(rocket_column, column_speed, max_column, rocket_column_size)

        draw_frame(canvas, rocket_row, rocket_column, rocket_frame)

        if space_pressed and (year > 2020 or gun_from_start):
            coroutines.append(fire(canvas, rocket_row, rocket_column + 2))

        await sleep(1)

        draw_frame(canvas, rocket_row, rocket_column, rocket_frame, negative=True)
        for obstacle in obstacles:
            if obstacle.has_collision(rocket_row, rocket_column):
                obstacles_in_last_collisions.append(obstacle)
                await explode(
                    canvas, rocket_row + round(rocket_row_size / 2), rocket_column + round(rocket_column_size / 2)
                )
                coroutines.append(show_gameover(canvas, max_row, max_column))
                return


async def blink(canvas, row, column, timeout, symbol='*'):
    """Display animation of the transmitted star."""
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
    """Animate garbage, flying from top to bottom. Column position will stay same, as specified on start."""
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

            await explode(canvas, round(obstacle.row + obstacle.rows_size / 2), round(obstacle.column + obstacle.columns_size / 2))
            return
        obstacles.remove(obstacle)
        row += speed


async def fill_orbit_with_garbage(canvas, max_column):
    """Specify and create coroutines for garbage objects animation according to game complexity."""
    garbage_frames = [
        open(os.path.join(f'{os.getcwd()}/templates/garbage', garbage_file), "r").read() for garbage_file
        in os.listdir(f'{os.getcwd()}/templates/garbage')
    ]

    while True:
        garbage_frame = random.choice(garbage_frames)
        garbage_row_size, garbage_column_size = get_frame_size(garbage_frame)
        garbage_column = random.randint(1, max_column - garbage_column_size)
        garbage_timeout = get_garbage_delay_tics()
        if garbage_timeout:
            coroutines.append(fly_garbage(canvas, column=garbage_column, garbage_frame=garbage_frame))
            await sleep(garbage_timeout)
        else:
            await sleep(1)


def stars_generator(canvas, max_row, max_column):
    """Generate star parameters, according to screen size and required quantity."""
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
    """Draw GameOver sign in the middle of the screen if the rocker clashes the garbage."""
    with open("templates/game_over.txt", "r") as frame:
        frame = frame.read()
        frame_row_size, frame_column_size = get_frame_size(frame)
    while True:
        draw_frame(canvas, max_row / 2 - frame_row_size / 2, max_column / 2 - frame_column_size / 2, frame)
        await asyncio.sleep(0)


async def show_year(canvas, max_column):
    """Draw current game year in the right corner of the screen."""
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
    """Update current game year after specified time."""
    global year
    while True:
        year += 1
        await sleep(15)


def get_garbage_delay_tics():
    """Specify game complexity by updating the garbage quantity according to the current game year."""
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


async def explode(canvas, center_row, center_column):
    """Animate object explosion on transmitted coordinates"""
    global explosion_frames
    rows, columns = get_frame_size(explosion_frames[0])
    corner_row = center_row - rows / 2
    corner_column = center_column - columns / 2

    curses.beep()
    for frame in explosion_frames:

        draw_frame(canvas, corner_row, corner_column, frame)

        await asyncio.sleep(0)
        draw_frame(canvas, corner_row, corner_column, frame, negative=True)
        await asyncio.sleep(0)


def draw(canvas):
    """Specify all start parameters, draws and executes main event loop."""
    global coroutines, obstacles, obstacles_in_last_collisions, year, explosion_frames

    explosion_frames = [
        open(os.path.join(f'{os.getcwd()}/templates/explosion', explosion_file), "r").read() for explosion_file
        in os.listdir(f'{os.getcwd()}/templates/explosion')
    ]

    canvas.nodelay(True)
    curses.curs_set(False)
    screen = curses.initscr()
    max_row, max_column = screen.getmaxyx()

    rocket_row = max_row / 2
    rocket_column = max_column / 2

    year = 1957

    obstacles_in_last_collisions = []
    obstacles = []

    coroutines = [
        star for star in stars_generator(canvas, max_row, max_column)
    ]

    coroutines.append(animate_rocket(canvas, rocket_row, rocket_column, max_row, max_column, gun_from_start))
    coroutines.append(fill_orbit_with_garbage(canvas, max_column))
    coroutines.append(update_year())

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)


        canvas.border()
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Space game parser')
    parser.add_argument(
        '--stars',
        help='Enter stars quantity',
        type=int,
        default=100
    )
    parser.add_argument(
        '--fullclip',
        help='Enter "True", if you want use gun from start of the game',
        action='store_true'
    )
    arguments = parser.parse_args()
    stars_quantity = arguments.stars
    gun_from_start = arguments.fullclip
    curses.update_lines_cols()
    curses.wrapper(draw)
