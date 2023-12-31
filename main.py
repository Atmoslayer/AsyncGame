import argparse
import curses
import random
import time

from animations import blink, fire, animate_rocket

TIC_TIMEOUT = 0.1


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
    with open("templates/rocket_frame_1.txt", "r") as frame:
        rocket_frame_1 = frame.read()
    with open("templates/rocket_frame_2.txt", "r") as frame:
        rocket_frame_2 = frame.read()
    rocket_frames = [rocket_frame_1, rocket_frame_1, rocket_frame_2, rocket_frame_2]
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
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)

            canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Space game parser')
    parser.add_argument('--stars', help='Enter stars quantity', type=int, default=100)
    arguments = parser.parse_args()
    stars_quantity = arguments.stars
    curses.update_lines_cols()
    curses.wrapper(draw)