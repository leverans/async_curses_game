import time
import curses
import asyncio
from random import randint, choice, random, uniform
import os

from explosion import explode
from fire_animation import fire
from curses_tools import draw_frame, read_controls, get_frame_size
from game_scenario import PHRASES, get_garbage_delay_tics
from physics import update_speed
from space_garbage import fly_garbage
from star_animation import blink, BLINK_LENGTH
from utilities import get_real_maxyx, sleep

TICK_LENGTH = .1
YEAR_LENGTH_IN_SECONDS = 10.5
START_YEAR = 1980
PLASMA_GUN_YEAR = 1980
TICKS_IN_YEAR = int(YEAR_LENGTH_IN_SECONDS / TICK_LENGTH)

coroutines = list()

spaceship_frames = []
gameover_banner = []
current_spaceship_frame = 0
obstacles = set()
obstacles_in_last_collisions = set()

current_year = START_YEAR
current_message = ""


async def control_time(canvas):
    global current_year, current_message

    while True:
        max_y, max_x = get_real_maxyx(canvas)
        window = canvas.derwin(1, int(max_x / 2), max_y-1, max(1, int(max_x / 2 - 25)))
        draw_frame(window, 0, 0, str(current_year))
        current_message = PHRASES.get(current_year, None) or current_message
        if current_message:
            draw_frame(window, 0, 8, current_message)
        await sleep(TICKS_IN_YEAR)
        draw_frame(window, 0, 8, current_message, negative=True)
        current_year += 1


async def run_spaceship(canvas, start_row, start_column, frames, obstacles, obstacles_in_last_collisions):
    global current_spaceship_frame
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

        for obstacle in obstacles:
            if obstacle.has_collision(row, column, *get_frame_size(frames[0])):
                obstacles.remove(obstacle)
                obstacles_in_last_collisions.add(obstacle)
                coroutines.append(
                    show_gameover(canvas, gameover_banner)
                )
                return

        if space_pressed and current_year >= PLASMA_GUN_YEAR:
            coroutines.append(
                fire(canvas, row, column+2,
                     obstacles=obstacles, obstacles_in_last_collisions=obstacles_in_last_collisions)
            )

        current_frame = current_spaceship_frame
        draw_frame(canvas, row, column, frames[current_frame])
        await asyncio.sleep(0)

        draw_frame(canvas, row, column, frames[current_frame], negative=True)


async def animate_spaceship(frames):
    global current_spaceship_frame
    while True:
        current_spaceship_frame = (current_spaceship_frame + 1) % len(frames)
        await sleep(2)


async def fill_orbit_with_garbage(canvas, garbage_frames):
    while True:
        garbage_delay = get_garbage_delay_tics(current_year)
        if garbage_delay:
            await sleep(garbage_delay)
            max_y, max_x = get_real_maxyx(canvas)
            coroutines.append(
                fly_garbage(canvas, randint(1, max_x-3), choice(garbage_frames),
                            obstacles=obstacles, speed=uniform(.1, 1))
            )
        else:
            await sleep(TICKS_IN_YEAR)  # засыпаем на весь год, т.к. в этом году еще чисто


async def show_gameover(canvas, banner):
    while True:
        max_y, max_x = get_real_maxyx(canvas)
        height, width = get_frame_size(banner)
        draw_frame(canvas, (max_y - height)/2, (max_x - width)/2, banner)
        await asyncio.sleep(0)


async def explode_collided_garbage(canvas, obstacles_to_explode):
    while True:
        for obstacle in obstacles_to_explode:
            coroutines.append(
                explode(canvas, obstacle.row + obstacle.rows_size / 2, obstacle.column + obstacle.columns_size / 2)
            )
        obstacles_to_explode.clear()
        await sleep(1)


def draw(canvas):
    global coroutines, spaceship_frames, gameover_banner
    # Загружаем кадры анимации
    for i in (1, 2):
        with open(f"animation_frames/spaceship/rocket_frame_{i}.txt", "r") as frame_file:
            spaceship_frames.append(frame_file.read())

    with open(f"animation_frames/game_over.txt", "r") as frame_file:
        gameover_banner = frame_file.read()

    garbage_frames = []
    folder = "animation_frames/garbage"
    for filename in os.listdir(folder):
        with open(f"{folder}/{filename}", "r") as frame_file:
            garbage_frames.append(frame_file.read())

    # Настраиваем canvas
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
        run_spaceship(canvas, max_y / 2 - 2, max_x / 2 - 2, spaceship_frames,
                          obstacles, obstacles_in_last_collisions),  # где-то примерно в центре
        animate_spaceship(spaceship_frames),
        fill_orbit_with_garbage(canvas, garbage_frames),
        explode_collided_garbage(canvas, obstacles_in_last_collisions),
        control_time(canvas),
    ]

    # запускаем event loop
    while True:
        canvas.border()
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
