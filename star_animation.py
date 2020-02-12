import asyncio
import curses
from random import randint


# захотелось отделить сценарий анимации от логики, так вроде гораздо удобнее
from utilities import sleep

STAR_ANIMATION_STEPS = (
    (20, curses.A_DIM),
    (3, 0),
    (5, curses.A_BOLD),
    (3, 0),
)
BLINK_LENGTH = sum(step[0] for step in STAR_ANIMATION_STEPS)


async def blink(canvas, row, column, symbol='*', animation_offset=0):
    # задерживаем фазу звезды на случайное число кадров в пределах длины цикла анимации
    await sleep(animation_offset)

    while True:
        for step in STAR_ANIMATION_STEPS:
            canvas.addstr(row, column, symbol, step[1])
            await sleep(step[0])