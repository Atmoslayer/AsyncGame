import curses
import random
import time

from animations import blink, fire, animate_rocket

TIC_TIMEOUT = 0.1


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
