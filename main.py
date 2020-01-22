import time
import curses
import asyncio
from random import randint, choice

from fire_animation import fire
from curses_tools import draw_frame, read_controls, get_frame_size

BLINK_LENGTH = 31


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for i in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for i in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(0)


async def spaceship_animation(canvas, start_row, start_column, frames):
    current_frame = 0
    row, column = start_row, start_column
    max_row, max_column = canvas.getmaxyx()
    height, width = get_frame_size(frames[0])
    max_row -= height
    max_column -= width

    while True:
        old_row, old_column = row, column
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row += rows_direction
        column += columns_direction
        if row < 1 or row >= max_row:
            row = old_row
        if column < 1 or column >= max_column:
            column = old_column
        draw_frame(canvas, row, column, frames[current_frame])
        canvas.refresh()
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frames[current_frame], negative=True)
        current_frame = (current_frame + 1) % len(frames)


def draw(canvas):
    # Загружаем кадры анимации
    SPACESHIP_FRAMES = []
    for i in (1, 2):
        with open(f"animation_frames/spaceship/rocket_frame_{i}.txt", "r") as frame_file:
            SPACESHIP_FRAMES.append(frame_file.read())

    # Настраиваем canvas
    canvas.border()
    canvas.refresh()
    curses.curs_set(False)
    canvas.nodelay(True)

    max_y, max_x = canvas.getmaxyx()

    star_coroutines = [
        blink(canvas, randint(1, max_y-2), randint(1, max_x-2), symbol=choice('+*.x'))
        # почему-то вываливается с ошибкой, если уменьшать на 1 - неясное
        for _ in range(200)
    ]
    # Сдвинем анимацию каждой звезды на случайное число циклов, чтобы все мигали вразнобой
    # Кажется предполагалось не так, но я не совсем понял, что от меня ожидается
    for coroutine in star_coroutines:
        for _ in range(randint(0, BLINK_LENGTH)):
            coroutine.send(None)

    # Объединяем звездные анимации с остальными
    coroutines = star_coroutines + [
        fire(canvas, max_y-2, max_x / 3),  # просто чтоб видно было отдельно от корабля
        spaceship_animation(canvas, max_y / 2 - 2, max_x / 2 - 2, SPACESHIP_FRAMES)
    ]

    # запускаем event loop
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(.1)


if __name__ == '__main__':

    curses.update_lines_cols()
    curses.wrapper(draw)
