from curses_tools import draw_frame, get_frame_size
import asyncio

from obstacles import Obstacle


async def fly_garbage(canvas, column, garbage_frame, obstacles, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    obstacle = Obstacle(row, column, *get_frame_size(garbage_frame))
    obstacles.add(obstacle)

    while row < rows_number:
        if obstacle not in obstacles:
            return
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacle.row = row

    obstacles.remove(obstacle)