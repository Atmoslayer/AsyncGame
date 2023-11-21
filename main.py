import asyncio
import curses
import random
import time

TIC_TIMEOUT = 0.1


async def blink(canvas, row, column, symbol='*'):
    while True:

        random_integer = random.randint(1, 10)
        print(random_integer)

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


def draw(canvas):
    curses.curs_set(False)
    canvas.border()
    screen = curses.initscr()
    max_row, max_column = screen.getmaxyx()
    stars_symbols = ['*', ':', '.', '+']
    coroutines = []
    for stars_quantity in range(100):
        star_row = random.randint(1, max_row-2)
        star_column = random.randint(1, max_column-2)
        star_symbol = random.choice(stars_symbols)
        coroutines.append(blink(canvas, star_row, star_column, star_symbol))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
            canvas.refresh()
        if len(coroutines) == 0:
            break

        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)