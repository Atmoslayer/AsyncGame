import argparse
import curses
import random
import time

from animations import blink, fire, animate_rocket
from frames_control_functions import get_frame_size

TIC_TIMEOUT = 0.1


def stars_generator(canvas, max_row, max_column):
    stars_symbols = ['*', ':', '.', '+']
    for star in range(stars_quantity):
        star_row = random.randint(1, max_row - 2)
        star_column = random.randint(1, max_column - 2)
        star_symbol = random.choice(stars_symbols)
        yield blink(canvas, star_row, star_column, star_symbol)


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

    rocket_row = max_row / 2
    rocket_column = max_column / 2

    coroutines = [
        star for star in stars_generator(canvas, max_row, max_column)
    ]

    coroutines.append(fire(canvas, rocket_row, rocket_column + 2))
    coroutines.append(animate_rocket(canvas, rocket_row, rocket_column, rocket_frames, max_row, max_column))

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
    parser = argparse.ArgumentParser(description='Space game parser')
    parser.add_argument('--stars', help='Enter stars quantity', type=int, default=100)
    arguments = parser.parse_args()
    stars_quantity = arguments.stars
    curses.update_lines_cols()
    curses.wrapper(draw)
