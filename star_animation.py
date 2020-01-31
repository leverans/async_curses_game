import asyncio
import curses
from random import randint


# захотелось отделить сценарий анимации от логики, так вроде гораздо удобнее
STAR_ANIMATION_STEPS = (
    (20, curses.A_DIM),
    (3, 0),
    (5, curses.A_BOLD),
    (3, 0),
)
BLINK_LENGTH = sum(step[0] for step in STAR_ANIMATION_STEPS)


# c измененным комментарием по причинам выноса параметра смещения анимации стало логично, а то я сначала опешил :)
async def blink(canvas, row, column, symbol='*', animation_offset=0):
    # задерживаем фазу звезды на случайное число кадров в пределах длины цикла анимации
    for _ in range(animation_offset):
        await asyncio.sleep(0)

    while True:
        for step in STAR_ANIMATION_STEPS:
            canvas.addstr(row, column, symbol, step[1])
            for _ in range(step[0]):
                await asyncio.sleep(0)