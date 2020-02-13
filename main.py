import time
import curses
import asyncio
from random import randint, choice, random, uniform
import os

from fire_animation import fire
from curses_tools import draw_frame, read_controls, get_frame_size
from obstacles import show_obstacles
from physics import update_speed
from space_garbage import fly_garbage
from star_animation import blink, BLINK_LENGTH
from utilities import get_real_maxyx

TICK_LENGTH = .1

coroutines = list()

spaceship_frames = []
current_spaceship_frame = 0
obstacles = set()
obstacles_in_last_collisions = set()

async def animate_spaceship(canvas, start_row, start_column, frames, obstacles, obstacles_in_last_collisions):
    current_frame = 0
    row, column = int(start_row), int(start_column)
    row_speed, column_speed = 0, 0
    rows, columns = canvas.getmaxyx()
    height, width = get_frame_size(frames[0])
    max_row = rows - height - 1
    max_column = columns - width - 1

    while True:
        old_row, old_column = row, column
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
        row += row_speed
        column += column_speed
        if row < 1 or row > max_row:
            row = old_row
        if column < 1 or column > max_column:
            column = old_column

        if space_pressed:
            coroutines.append(
                fire(canvas, row, column+2,
                     obstacles=obstacles, obstacles_in_last_collisions=obstacles_in_last_collisions)
            )
            
        draw_frame(canvas, row, column, frames[current_frame])
        await asyncio.sleep(0)

        draw_frame(canvas, row, column, frames[current_frame], negative=True)
        current_frame = (current_frame + 1) % len(frames)


async def fill_orbit_with_garbage(canvas, garbage_frames, garbage_probability=.05):
    while True:
        if random() <= garbage_probability:
            max_y, max_x = get_real_maxyx(canvas)
            coroutines.append(
                fly_garbage(canvas, randint(1, max_x-3), choice(garbage_frames),
                            obstacles=obstacles, speed=uniform(.1, 1))
            )
        await asyncio.sleep(0)


def draw(canvas):
    global coroutines, spaceship_frames
    # Загружаем кадры анимации
    for i in (1, 2):
        with open(f"animation_frames/spaceship/rocket_frame_{i}.txt", "r") as frame_file:
            spaceship_frames.append(frame_file.read())

    garbage_frames = []
    folder = "animation_frames/garbage"
    for filename in os.listdir(folder):
        with open(f"{folder}/{filename}", "r") as frame_file:
            garbage_frames.append(frame_file.read())

    # Настраиваем canvas
    canvas.border()
    canvas.refresh()
    curses.curs_set(False)
    canvas.nodelay(True)

    max_y, max_x = get_real_maxyx(canvas)

    star_coroutines = [
        blink(canvas, randint(1, max_y - 1), randint(1, max_x - 1),
              symbol=choice('+*.x'), animation_offset=randint(0, BLINK_LENGTH-1))
        for _ in range(200)
    ]

    # Объединяем звездные анимации с остальными
    coroutines = star_coroutines + [
        #fire(canvas, max_y-1, max_x / 3),  # просто чтоб видно было отдельно от корабля
        animate_spaceship(canvas, max_y / 2 - 2, max_x / 2 - 2, spaceship_frames,
                          obstacles, obstacles_in_last_collisions),  # где-то примерно в центре
        show_obstacles(canvas, obstacles),
        fill_orbit_with_garbage(canvas, garbage_frames)
    ]

    # запускаем event loop
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TICK_LENGTH)


if __name__ == '__main__':

    curses.update_lines_cols()
    curses.wrapper(draw)
