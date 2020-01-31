import time
import curses
import asyncio
from random import randint, choice

from fire_animation import fire
from curses_tools import draw_frame, read_controls, get_frame_size
from star_animation import blink, BLINK_LENGTH


async def animate_spaceship(canvas, start_row, start_column, frames):
    current_frame = 0
    row, column = int(start_row), int(start_column)
    rows, columns = canvas.getmaxyx()
    height, width = get_frame_size(frames[0])
    max_row = rows - height - 1
    max_column = columns - width - 1

    while True:
        old_row, old_column = row, column
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row += rows_direction
        column += columns_direction
        if row < 1 or row > max_row:
            row = old_row
        if column < 1 or column > max_column:
            column = old_column
        draw_frame(canvas, row, column, frames[current_frame])
        await asyncio.sleep(0)

        draw_frame(canvas, row, column, frames[current_frame], negative=True)
        current_frame = (current_frame + 1) % len(frames)


def draw(canvas):
    # Загружаем кадры анимации
    spaceship_frames = []
    for i in (1, 2):
        with open(f"animation_frames/spaceship/rocket_frame_{i}.txt", "r") as frame_file:
            spaceship_frames.append(frame_file.read())

    # Настраиваем canvas
    canvas.border()
    canvas.refresh()
    curses.curs_set(False)
    canvas.nodelay(True)

    rows, columns = canvas.getmaxyx()  # getmaxyx на самом деле возвращает ширину и высоту
    max_y, max_x = rows - 1, columns - 1  # настоящие предельные значения

    star_coroutines = [
        blink(canvas, randint(1, max_y - 1), randint(1, max_x - 1),
              symbol=choice('+*.x'), animation_offset=randint(0, BLINK_LENGTH-1))
        # почему-то вываливается с ошибкой, если уменьшать на 1 - неясное
        for _ in range(200)
    ]

    # Объединяем звездные анимации с остальными
    coroutines = star_coroutines + [
        fire(canvas, max_y-1, max_x / 3),  # просто чтоб видно было отдельно от корабля
        animate_spaceship(canvas, max_y / 2 - 2, max_x / 2 - 2, spaceship_frames),  # где-то примерно в центре
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
